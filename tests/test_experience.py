from unittest.mock import Mock
import pytest
from app.services.experience import job_experience, resume_experience_hint
from app.services import job_search
from test_discovery import raw, fake_client, setup_workflow, app


@pytest.mark.parametrize('text,months', [
    ('4 to 7 years experience in back-end development', 48),
    ('At least 8 years of experience required.', 96),
    ('2+ years of professional experience', 24),
    ('Experience: 6-12 months', 6),
    ('Experience required 3 years', 36),
    ('1.5 years of work experience', 18),
    ('3 years experience required. 5 years experience preferred.', 36),
    ('8 years experience preferred', None),
    ('Up to 8 years experience', None),
    ('Maximum 2 years experience', None),
    ('Senior Python Developer', None),
    ('Graduated in 2022. Built Python projects.', None),
    ('7-4 years experience', None),
])
def test_job_duration(text,months):
    assert job_experience(text)[0] == months


def test_resume_hint_does_not_sum_or_infer_dates():
    assert resume_experience_hint('2 years experience in development')['months'] == 24
    assert resume_experience_hint('Internship: January 2023 to June 2023')['months'] is None
    assert resume_experience_hint('5 months experience. 2 years experience.')['months'] is None


def test_filter_before_ten_cap_and_keep_unknown(monkeypatch):
    monkeypatch.setenv('JOB_SEARCH_API_KEY','synthetic-key')
    client=Mock();response=Mock(status_code=200)
    senior=[raw(str(i), days=1, job_title=f'Senior role {i}', job_description='8 years experience required. '+ 'Synthetic duties. '*20) for i in range(12)]
    junior=raw('junior', days=2, job_title='Junior developer', job_description='1 to 3 years experience required. '+ 'Synthetic duties. '*20)
    unknown=raw('unknown', days=3, job_title='Developer')
    response.json.return_value={'data':{'jobs':senior+[junior,unknown],'cursor':None}}
    client.get.return_value=response;fake_client(monkeypatch,client)
    jobs,warnings=job_search.search_jobs(['Python'],['Bengaluru'],experience_months=24)
    assert [job.id for job in jobs] == ['junior','unknown']
    assert jobs[0].minimum_experience_months == 12
    assert jobs[1].minimum_experience_months is None
    assert 'Excluded 12' in warnings[0]
    assert 'description' not in jobs[0].metadata()
    assert jobs[0].metadata()['experience_evidence'] == '1 to 3 years experience'


def test_zero_experience_excludes_positive_minimum(monkeypatch):
    monkeypatch.setenv('JOB_SEARCH_API_KEY','synthetic-key')
    client=Mock();response=Mock(status_code=200)
    response.json.return_value={'data':{'jobs':[raw(job_description='6 months experience required. '+ 'Duties. '*40)]}}
    client.get.return_value=response;fake_client(monkeypatch,client)
    jobs,warnings=job_search.search_jobs(['Python'],['Bengaluru'],experience_months=0)
    assert not jobs and warnings


@pytest.mark.parametrize('duration',['','-1','2.5','601','nan','999999999999'])
def test_search_requires_valid_confirmed_duration(app,monkeypatch,duration):
    from app import discovery
    client=app.test_client();token,item=setup_workflow(app,client);item.searched=False
    search=Mock();monkeypatch.setattr(discovery,'search_jobs',search)
    response=client.post(f'/discover/{token}/search',data={'csrf_token':'synthetic-csrf','roles':['Python'],'locations':['Bengaluru'],'experience_months':duration})
    assert response.status_code == 400
    assert b'Confirm your total work experience' in response.data
    search.assert_not_called()


def test_confirmed_experience_passed_and_saved(app,monkeypatch):
    from app import discovery
    client=app.test_client();token,item=setup_workflow(app,client);item.searched=False
    search=Mock(return_value=([],[]));monkeypatch.setattr(discovery,'search_jobs',search)
    response=client.post(f'/discover/{token}/search',data={'csrf_token':'synthetic-csrf','roles':['Python'],'locations':['Bengaluru'],'experience_months':'24'})
    assert response.status_code == 302
    assert search.call_args.kwargs['experience_months'] == 24
    assert item.profile['confirmed_experience_months'] == 24
    assert b'Confirmed work experience: 24 months' in client.get(response.headers['Location']).data
