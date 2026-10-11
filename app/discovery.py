import secrets
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session, url_for
from app.database import DatabaseConfigurationError, DatabaseSaveError, ensure_database_ready, save_analysis
from app.services.gemini_analyzer import GeminiAnalysisError, GeminiConfigurationError, analyze_resume
from app.services.pdf_extractor import PdfExtractionError, extract_resume_text
from app.services.resume_profile import extract_profile
from app.services.job_search import JobSearchError, search_jobs, provider_ready
from app.scoring import calculate_match_score
from app.services.experience import resume_experience_hint

jobs = Blueprint('jobs', __name__)
ERRORS = (DatabaseConfigurationError, DatabaseSaveError, GeminiAnalysisError, GeminiConfigurationError, JobSearchError, PdfExtractionError)


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']


def owner():
    if 'owner' not in session:
        session['owner'] = secrets.token_urlsafe(24)
    return session['owner']


@jobs.before_app_request
def protect_post():
    if request.method == 'POST':
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
        expected = session.get('csrf', '')
        if not expected or not secrets.compare_digest(supplied, expected):
            abort(400, description='Form expired. Reload the page and try again.')


def workflow(token):
    item = current_app.extensions['workflows'].get(token, owner())
    if item is None:
        abort(410, description='This private search has expired or belongs to another browser. Upload the resume again.')
    return item


def bounded_inputs(name, max_length):
    values = [v.strip() for v in request.form.getlist(name) if v.strip()]
    if not 1 <= len(values) <= 3 or any(len(v) > max_length or any(ord(c) < 32 for c in v) for v in values):
        raise ValueError(f'Enter one to three {name}, each at most {max_length} characters.')
    return list(dict.fromkeys(values))


@jobs.route('/discover', methods=['POST'])
def profile():
    try:
        provider_ready()  # Avoid sending resume to Gemini when jobs cannot be retrieved.
        file = request.files.get('resume_pdf')
        if not file or not file.filename or not file.filename.lower().endswith('.pdf'):
            raise ValueError('Choose a resume PDF.')
        if request.form.get('gemini_data_consent') != 'yes':
            raise ValueError('Confirm the resume is synthetic or anonymized.')
        locations = bounded_inputs('locations', 100)
        resume = extract_resume_text(file.read())
        if len(resume) > 30000:
            raise ValueError('Resume text exceeds 30,000 characters. Use a shorter resume.')
        ensure_database_ready()
        result = extract_profile(resume)
        profile_data = result.model_dump(mode='json')
        profile_data['experience_hint'] = resume_experience_hint(resume)
        token = current_app.extensions['workflows'].create(owner(), resume, profile_data)
        item = workflow(token)
        item.locations = locations
        return redirect(url_for('jobs.review', token=token))
    except (*ERRORS, ValueError) as exc:
        return render_template('index.html', error=str(exc)), 400


@jobs.route('/discover/<token>', methods=['GET'])
def review(token):
    return render_template('profile.html', token=token, item=workflow(token))


@jobs.route('/discover/<token>/search', methods=['POST'])
def search(token):
    item = workflow(token)
    try:
        duration = request.form.get('experience_months', '').strip()
        if len(duration) > 3 or not duration.isascii() or not duration.isdigit() or not 0 <= int(duration) <= 600:
            raise ValueError('Confirm your total work experience in whole months (0 to 600). Enter 0 for no experience.')
        experience_months = int(duration)
        roles = bounded_inputs('roles', 100)
        locations = bounded_inputs('locations', 100)
        with item.lock:
            if item.searched:
                return redirect(url_for('jobs.dashboard', token=token))
            item.jobs, item.warnings = search_jobs(roles, locations, experience_months=experience_months)
            item.experience_months = experience_months
            item.profile['confirmed_experience_months'] = experience_months
            item.roles, item.locations, item.searched = roles, locations, True
        return redirect(url_for('jobs.dashboard', token=token))
    except (JobSearchError, ValueError) as exc:
        return render_template('profile.html', token=token, item=item, error=str(exc)), 400


@jobs.route('/discover/<token>/jobs')
def dashboard(token):
    item = workflow(token)
    if not item.searched:
        return redirect(url_for('jobs.review', token=token))
    return render_template('jobs.html', token=token, item=item)


@jobs.route('/discover/<token>/jobs/<int:index>/analyze', methods=['POST'])
def analyze_job(token, index):
    item = workflow(token)
    if index >= len(item.jobs):
        abort(404)
    with item.lock:
        if index in item.outcomes:
            return jsonify(item.outcomes[index])
        job = item.jobs[index]
        if not job.description_usable:
            outcome = {'status': 'unavailable', 'message': 'Description missing, too short, too long or visibly truncated. No score or questions were generated.'}
        else:
            try:
                ensure_database_ready()
                insights = analyze_resume(item.resume, job.description)
                result = insights.model_dump(mode='json')
                result['job_match_score'] = calculate_match_score(result['requirements'])
                result['strengths'] = [r['requirement'] for r in result['requirements'] if r['status'] == 'matched']
                result['gaps'] = [r['requirement'] for r in result['requirements'] if r['status'] == 'not_found']
                payload = {'mode': 'job_discovery', 'profile': item.profile, 'job': job.metadata(), 'analysis': result}
                try:
                    record_id = save_analysis(item.resume, payload)
                    outcome = {'status': 'complete', 'result': result, 'record_id': record_id, 'saved': True}
                except (DatabaseConfigurationError, DatabaseSaveError) as exc:
                    outcome = {'status': 'complete', 'result': result, 'saved': False, 'message': str(exc)}
            except (DatabaseConfigurationError, DatabaseSaveError, GeminiAnalysisError, GeminiConfigurationError) as exc:
                outcome = {'status': 'unavailable', 'message': str(exc)}
        item.outcomes[index] = outcome
        return jsonify(outcome)
