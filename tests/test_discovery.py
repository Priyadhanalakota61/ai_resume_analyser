import io
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import pytest
from app import create_app
from app.services import job_search, resume_profile
from app.services.job_search import normalize_posting, safe_job_url, JobSearchError
from app.services.gemini_analyzer import AnalysisInsights, validate_evidence, GeminiAnalysisError
from app.transient import WorkflowStore

NOW = datetime.now(timezone.utc)
RESUME = 'Built REST APIs with Python and Flask. Wrote SQL joins and tested database queries.'
JD = 'Applicants must write Python and Flask REST APIs. Candidates must also know SQL joins. ' * 4


def raw(i='1', days=1, **kw):
    result = dict(job_id=i, job_title='Python Developer', employer_name='Example Demo Company',
        job_location='Bengaluru, India', job_posted_at_datetime_utc=(NOW-timedelta(days=days)).isoformat(),
        job_apply_link=f'https://jobs.example.com/posting/{i}', job_description=JD, job_publisher='Demo Publisher')
    result.update(kw)
    return result


def insights():
    return AnalysisInsights(requirements=[dict(requirement='Python REST APIs', status='matched',
        resume_evidence='Built REST APIs with Python and Flask.', job_evidence='Applicants must write Python and Flask REST APIs.')],
        skills_found=['Python'], skills_missing=[], suggestions=['Discuss the API project.'],
        interview_questions=['How did you test the API?'])


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'https://localhost/x', 'http://127.0.0.1/x',
    'https://in.indeed.com/jobs?q=python', 'https://in.indeed.com/q-python-jobs.html',
    'https://www.naukri.com/python-jobs-in-bengaluru', 'https://linkedin.com/jobs/search/?q=python',
    'https://user:password@example.com/job', 'https://example.com'])
def test_reject_bad_links(url):
    assert safe_job_url(url) is None


def test_posting_filters_dates_expiration_and_description():
    assert normalize_posting(raw(), NOW).description_usable
    for data in [raw(days=31), raw(days=-2), raw(job_posted_at_datetime_utc=None),
                 raw(job_is_expired=True), raw(job_is_active=False),
                 raw(job_expiration_datetime_utc=(NOW-timedelta(days=1)).isoformat())]:
        assert normalize_posting(data, NOW) is None
    assert not normalize_posting(raw(job_description='short'), NOW).description_usable
    assert not normalize_posting(raw(job_description=JD+'...'), NOW).description_usable
    assert not normalize_posting(raw(job_description='x'*31000), NOW).description_usable
    job = normalize_posting(raw(apply_options=[dict(apply_link='https://employer.example.com/job/1', is_direct=True)]), NOW)
    assert job.direct and 'employer' in job.apply_url
    assert 'description' not in job.metadata()


def fake_client(monkeypatch, client):
    context=Mock();context.__enter__=Mock(return_value=client);context.__exit__=Mock(return_value=False)
    monkeypatch.setattr(job_search.requests,'Session',lambda:context)


def test_provider_sort_dedupe_partial_and_limits(monkeypatch):
    monkeypatch.setenv('JOB_SEARCH_API_KEY', 'synthetic-test-key')
    client=Mock();response=Mock(status_code=200)
    response.json.return_value={'data':[raw(str(i),days=i+1,job_title=f'Role {i}') for i in range(15)]+[raw('0')]}
    client.get.side_effect=[response,job_search.requests.Timeout()]
    fake_client(monkeypatch,client)
    jobs,warnings=job_search.search_jobs(['Python Developer'],['Bengaluru','Hyderabad'])
    assert len(jobs)==10 and len(warnings)==1
    assert jobs[0].id=='0' and jobs[-1].id=='9'
    assert client.get.call_args_list[0].kwargs['params']['country']=='in'
    assert 'resume' not in str(client.get.call_args_list)


def test_missing_key_and_quota(monkeypatch):
    monkeypatch.delenv('JOB_SEARCH_API_KEY',raising=False)
    with pytest.raises(JobSearchError):job_search.search_jobs(['Python'],['Remote'])
    monkeypatch.setenv('JOB_SEARCH_API_KEY','synthetic-test-key')
    client=Mock();client.get.return_value.status_code=429;fake_client(monkeypatch,client)
    jobs,warnings=job_search.search_jobs(['Python'],['Remote'])
    assert not jobs and 'quota' in warnings[0]
    assert client.get.call_args.kwargs['params']['work_from_home']=='true'


def test_evidence_rejects_fabrication_and_duplicates():
    assert validate_evidence(insights(),RESUME,JD)
    bad=insights();bad.requirements[0].resume_evidence='Built Kubernetes clusters.'
    with pytest.raises(GeminiAnalysisError):validate_evidence(bad,RESUME,JD)
    bad=insights();bad.requirements[0].job_evidence='Must know Kubernetes.'
    with pytest.raises(GeminiAnalysisError):validate_evidence(bad,RESUME,JD)
    bad=insights();bad.requirements.append(bad.requirements[0])
    with pytest.raises(GeminiAnalysisError):validate_evidence(bad,RESUME,JD)


def test_profile_evidence(monkeypatch):
    value=resume_profile.ResumeProfile(skills=[dict(label='Python',resume_evidence='Built Kubernetes clusters')],
        suggested_roles=[dict(label='Python Developer',resume_evidence='Built REST APIs with Python and Flask.')])
    monkeypatch.setattr(resume_profile,'generate_structured',lambda *a:value)
    with pytest.raises(GeminiAnalysisError):resume_profile.extract_profile(RESUME)


def test_store_expiry_ownership_capacity():
    store=WorkflowStore(capacity=1);key=store.create('one',RESUME,{})
    assert store.get(key,'two') is None
    store.get(key,'one').expires=0
    assert store.get(key,'one') is None
    a=store.create('one',RESUME,{});b=store.create('one',RESUME,{})
    assert store.get(a,'one') is None and store.get(b,'one')


@pytest.fixture
def app(monkeypatch):
    from app import discovery
    app=create_app();app.config.update(TESTING=True,SECRET_KEY='synthetic-session-key')
    monkeypatch.setattr(discovery,'ensure_database_ready',lambda:None)
    monkeypatch.setattr(discovery,'save_analysis',lambda *a:42)
    monkeypatch.setattr(discovery,'analyze_resume',lambda *a:insights())
    return app


def setup_workflow(app,client,description=JD):
    with client.session_transaction() as sess:
        sess['owner']='demo';sess['csrf']='synthetic-csrf'
    key=app.extensions['workflows'].create('demo',RESUME,{'skills':[],'suggested_roles':[]})
    item=app.extensions['workflows'].get(key,'demo')
    item.jobs=[normalize_posting(raw(job_description=description),NOW)];item.searched=True
    return key,item


def test_analysis_cached_escaped_and_persisted(app,monkeypatch):
    from app import discovery
    client=app.test_client();key,item=setup_workflow(app,client)
    analyze=Mock(return_value=insights());save=Mock(return_value=42)
    monkeypatch.setattr(discovery,'analyze_resume',analyze);monkeypatch.setattr(discovery,'save_analysis',save)
    item.jobs[0].title='<script>alert(1)</script>'
    page=client.get(f'/discover/{key}/jobs')
    assert b'&lt;script&gt;' in page.data and b'<script>alert' not in page.data
    path=f'/discover/{key}/jobs/0/analyze'
    assert client.post(path).status_code==400
    a=client.post(path,headers={'X-CSRF-Token':'synthetic-csrf'}).json
    b=client.post(path,headers={'X-CSRF-Token':'synthetic-csrf'}).json
    assert a==b and a['result']['job_match_score']==100
    assert analyze.call_count==1 and save.call_count==1
    assert 'description' not in save.call_args.args[1]['job']
    stranger=app.test_client();assert stranger.get(f'/discover/{key}/jobs').status_code==410


def test_insufficient_and_database_failure(app,monkeypatch):
    from app import discovery
    client=app.test_client();key,item=setup_workflow(app,client,'short')
    analyze=Mock(side_effect=AssertionError('No Gemini call expected'))
    monkeypatch.setattr(discovery,'analyze_resume',analyze)
    response=client.post(f'/discover/{key}/jobs/0/analyze',headers={'X-CSRF-Token':'synthetic-csrf'}).json
    assert response['status']=='unavailable' and analyze.call_count==0
    item.jobs[0]=normalize_posting(raw(),NOW);item.outcomes.clear()
    def fail():raise discovery.DatabaseSaveError('Database unavailable')
    monkeypatch.setattr(discovery,'ensure_database_ready',fail)
    response=client.post(f'/discover/{key}/jobs/0/analyze',headers={'X-CSRF-Token':'synthetic-csrf'}).json
    assert response['status']=='unavailable' and analyze.call_count==0


def test_save_failure_preserves_analysis(app,monkeypatch):
    from app import discovery
    client=app.test_client();key,item=setup_workflow(app,client)
    def fail(*a):raise discovery.DatabaseSaveError('Not saved')
    monkeypatch.setattr(discovery,'save_analysis',fail)
    response=client.post(f'/discover/{key}/jobs/0/analyze',headers={'X-CSRF-Token':'synthetic-csrf'}).json
    assert response['status']=='complete' and response['saved'] is False


def test_locations_limit_and_manual_flow(app,monkeypatch):
    from app import discovery,routes
    client=app.test_client();client.get('/')
    with client.session_transaction() as sess:token=sess['csrf']
    monkeypatch.setattr(discovery,'provider_ready',lambda:'in')
    response=client.post('/discover',data={'csrf_token':token,'resume_pdf':(io.BytesIO(b'fake'),'demo.pdf'),
        'gemini_data_consent':'yes','locations':['A','B','C','D']})
    assert response.status_code==400 and b'one to three' in response.data
    monkeypatch.setattr(routes,'extract_resume_text',lambda *a:RESUME)
    monkeypatch.setattr(routes,'ensure_database_ready',lambda:None)
    monkeypatch.setattr(routes,'analyze_resume',lambda *a:insights())
    monkeypatch.setattr(routes,'save_analysis',lambda *a:42)
    response=client.post('/',data={'csrf_token':token,'resume_pdf':(io.BytesIO(b'fake'),'demo.pdf'),
        'gemini_data_consent':'yes','job_description':JD})
    assert response.status_code==200 and b'100%' in response.data


def test_profile_search_dashboard_roundtrip(app,monkeypatch):
    from app import discovery
    client=app.test_client();client.get('/')
    with client.session_transaction() as sess:csrf=sess['csrf']
    profile=resume_profile.ResumeProfile(skills=[dict(label='Python',resume_evidence='Built REST APIs with Python and Flask.')],
        suggested_roles=[dict(label='Python Developer',resume_evidence='Built REST APIs with Python and Flask.')])
    monkeypatch.setattr(discovery,'provider_ready',lambda:'in')
    monkeypatch.setattr(discovery,'extract_resume_text',lambda *a:RESUME)
    monkeypatch.setattr(discovery,'extract_profile',lambda *a:profile)
    search=Mock(return_value=([normalize_posting(raw(),NOW)],['One search timed out.']))
    monkeypatch.setattr(discovery,'search_jobs',search)
    response=client.post('/discover',data={'csrf_token':csrf,'resume_pdf':(io.BytesIO(b'fake'),'demo.pdf'),
        'gemini_data_consent':'yes','locations':['Bengaluru','Remote']})
    assert response.status_code==302
    review_url=response.headers['Location']
    assert b'Python Developer' in client.get(review_url).data
    response=client.post(review_url+'/search',data={'csrf_token':csrf,'roles':['Python Developer'], 'locations':['Bengaluru','Remote']})
    assert response.status_code==302
    page=client.get(response.headers['Location'])
    assert b'One search timed out' in page.data and b'Example Demo Company' in page.data
    client.post(review_url+'/search',data={'csrf_token':csrf,'roles':['Python Developer'],'locations':['Remote']})
    assert search.call_count==1
    with client.session_transaction() as sess:
        assert RESUME not in str(dict(sess))


def test_empty_requirements_no_score(app,monkeypatch):
    from app import discovery
    client=app.test_client();key,item=setup_workflow(app,client)
    value=insights();value.requirements=[]
    monkeypatch.setattr(discovery,'analyze_resume',lambda *a:value)
    result=client.post(f'/discover/{key}/jobs/0/analyze',headers={'X-CSRF-Token':'synthetic-csrf'}).json
    assert result['result']['job_match_score'] is None


def test_auth_and_malformed_provider(monkeypatch):
    monkeypatch.setenv('JOB_SEARCH_API_KEY','synthetic-test-key')
    client=Mock();fake_client(monkeypatch,client)
    client.get.return_value.status_code=403
    with pytest.raises(JobSearchError):job_search.search_jobs(['Python'],['Remote'])
    client.get.return_value.status_code=200
    client.get.return_value.json.return_value={'data':None}
    jobs,warnings=job_search.search_jobs(['Python'],['Bengaluru'])
    assert not jobs and warnings


def test_offer_expiration_and_empty_pdf():
    from app.services.pdf_extractor import extract_resume_text, PdfExtractionError
    from pypdf import PdfWriter
    assert normalize_posting(raw(job_offer_expiration_datetime_utc=(NOW-timedelta(days=1)).isoformat()),NOW) is None
    with pytest.raises(PdfExtractionError):extract_resume_text(b'not a pdf')
    writer=PdfWriter();writer.add_blank_page(width=100,height=100)
    stream=io.BytesIO();writer.write(stream)
    with pytest.raises(PdfExtractionError,match='No selectable text'):extract_resume_text(stream.getvalue())


def test_top_level_direct_link_beats_publisher_option():
    job=normalize_posting(raw(job_apply_is_direct=True,
        apply_options=[dict(apply_link='https://publisher.example.com/jobs/123',is_direct=False)]),NOW)
    assert job.direct and job.apply_url=='https://jobs.example.com/posting/1'


def test_whitespace_evidence_rejected(monkeypatch):
    bad=insights();bad.requirements[0].job_evidence=' '*12
    with pytest.raises(GeminiAnalysisError):validate_evidence(bad,RESUME,JD)
    profile=resume_profile.ResumeProfile(skills=[],suggested_roles=[dict(label='Python Developer',resume_evidence=' '*12)])
    monkeypatch.setattr(resume_profile,'generate_structured',lambda *a:profile)
    with pytest.raises(GeminiAnalysisError):resume_profile.extract_profile(RESUME)


@pytest.mark.parametrize('description',['Needs Python.',JD+'...'])
def test_manual_insufficient_description_no_model_call(app,monkeypatch,description):
    from app import routes
    client=app.test_client();client.get('/')
    with client.session_transaction() as sess:csrf=sess['csrf']
    unexpected=Mock(side_effect=AssertionError('Must not call model'))
    monkeypatch.setattr(routes,'analyze_resume',unexpected)
    response=client.post('/',data={'csrf_token':csrf,'resume_pdf':(io.BytesIO(b'fake'),'demo.pdf'),
        'gemini_data_consent':'yes','job_description':description})
    assert response.status_code==400 and unexpected.call_count==0
