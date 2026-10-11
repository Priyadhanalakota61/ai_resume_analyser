"""Bounded JSearch discovery. No resume text is sent to the job provider."""
import ipaddress
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import requests
from pydantic import BaseModel
from app.services.experience import job_experience


class JobSearchError(RuntimeError):
    pass


class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    publisher: str
    apply_url: str
    direct: bool = False
    posted_at: str
    retrieved_at: str
    description: str
    description_usable: bool
    minimum_experience_months: int | None = None
    experience_evidence: str = ""

    def metadata(self):
        return self.model_dump(exclude={'description'})


def parse_date(value):
    try:
        date = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def safe_job_url(value):
    if not isinstance(value, str) or len(value) > 2500 or any(c.isspace() for c in value):
        return None
    try:
        url = urlsplit(value)
        host = (url.hostname or '').lower()
        if url.scheme not in ('https', 'http') or not host or url.username or url.password:
            return None
        if host == 'localhost' or host.endswith(('.local', '.internal')) or '.' not in host:
            return None
        try:
            if not ipaddress.ip_address(host).is_global:
                return None
        except ValueError:
            pass
        path = url.path.lower().rstrip('/')
        query = dict(parse_qsl(url.query))
        # Reject recognizable broad search/landing URLs, not specific postings.
        if not path or path in ('/jobs', '/search', '/careers'):
            return None
        if ('indeed.' in host and ('/q-' in path or path == '/jobs')) or ('naukri.com' in host and '-jobs-in-' in path):
            return None
        if 'linkedin.com' in host and '/jobs/search' in path:
            return None
        return value
    except ValueError:
        return None


def canonical_url(value):
    url = urlsplit(value)
    query = [(k, v) for k, v in parse_qsl(url.query) if not k.lower().startswith('utm_')]
    return urlunsplit((url.scheme, url.netloc.lower(), url.path.rstrip('/'), urlencode(sorted(query)), ''))


def normalize_posting(raw, now):
    if not isinstance(raw, dict) or raw.get('job_is_expired') is True or raw.get('job_is_active') is False:
        return None
    posted = parse_date(raw.get('job_posted_at_datetime_utc'))
    expiry = parse_date(raw.get('job_offer_expiration_datetime_utc') or raw.get('job_expiration_datetime_utc'))
    if not posted or posted > now + timedelta(hours=1) or posted < now - timedelta(days=30) or (expiry and expiry <= now):
        return None
    options = [x for x in (raw.get('apply_options') or []) if isinstance(x, dict)]
    options.append({'apply_link': raw.get('job_apply_link'), 'is_direct': raw.get('job_apply_is_direct'), 'publisher': raw.get('job_publisher')})
    options.sort(key=lambda x: x.get('is_direct') is not True)
    chosen = next((x for x in options if safe_job_url(x.get('apply_link'))), None)
    if not chosen:
        return None
    def value(key, limit=300):
        v = raw.get(key)
        return v.strip()[:limit] if isinstance(v, str) else ''
    title, identifier = value('job_title'), value('job_id', 2000)
    if not title or not identifier:
        return None
    description = value('job_description', 40000)
    usable = 200 <= len(description) <= 30000 and not description.endswith(('...', '…'))
    minimum_months, experience_evidence = job_experience(description)
    location = value('job_location') or ', '.join(filter(None, [value('job_city'), value('job_state'), value('job_country')]))
    return JobPosting(id=identifier, title=title, company=value('employer_name') or 'Company not supplied',
        location=location or ('Remote' if raw.get('job_is_remote') else 'Location not supplied'),
        publisher=str(chosen.get('publisher') or raw.get('job_publisher') or 'JSearch')[:200],
        apply_url=chosen['apply_link'], direct=chosen.get('is_direct') is True,
        posted_at=posted.isoformat(), retrieved_at=now.isoformat(), description=description,
        description_usable=usable, minimum_experience_months=minimum_months,
        experience_evidence=experience_evidence)


def provider_ready():
    if not os.getenv('JOB_SEARCH_API_KEY', '').strip():
        raise JobSearchError('Set JOB_SEARCH_API_KEY in your local .env using an OpenWeb Ninja JSearch key. No live listings were retrieved.')
    country = os.getenv('JOB_SEARCH_COUNTRY', 'in').strip().lower()
    if not re.fullmatch('[a-z]{2}', country):
        raise JobSearchError('JOB_SEARCH_COUNTRY must be a two-letter country code, such as in.')
    return country


def search_jobs(roles, locations, experience_months=None):
    country = provider_ready()
    now = datetime.now(timezone.utc)
    jobs, warnings = [], []
    seen_ids, seen_links, seen_titles = set(), set(), set()
    excluded_ids = set()
    with requests.Session() as client:
        for role in roles[:3]:
            for location in locations[:3]:
                remote = location.casefold() == 'remote'
                params = {'query': f'{role} jobs in {country}' if remote else f'{role} jobs in {location}',
                          'country': country, 'language': 'en', 'date_posted': 'month'}
                if remote:
                    params['work_from_home'] = 'true'
                try:
                    response = client.get('https://api.openwebninja.com/jsearch/search-v2',
                        headers={'x-api-key': os.environ['JOB_SEARCH_API_KEY'].strip()}, params=params, timeout=(5, 20))
                    if response.status_code in (401, 403):
                        raise JobSearchError('Job provider rejected access. Check your OpenWeb Ninja key and JSearch access.')
                    if response.status_code == 429:
                        warnings.append('Job provider quota/rate limit reached; showing only listings already retrieved.')
                        return sorted(jobs, key=lambda j: j.posted_at, reverse=True)[:10], warnings
                    response.raise_for_status()
                    payload = response.json()
                    data = payload.get('data') if isinstance(payload, dict) else None
                    # search-v2 nests postings under data.jobs alongside its cursor.
                    if isinstance(data, dict):
                        data = data.get('jobs')
                    if not isinstance(data, list):
                        warnings.append(f'Job provider returned an unexpected response format for {role} in {location}.')
                        continue
                    for raw in data[:100]:
                        if remote and isinstance(raw, dict) and raw.get('job_is_remote') is not True:
                            continue
                        job = normalize_posting(raw, now)
                        if not job:
                            continue
                        if experience_months is not None and job.minimum_experience_months is not None and job.minimum_experience_months > experience_months:
                            excluded_ids.add(job.id)
                            continue
                        link = canonical_url(job.apply_url)
                        title_key = (job.title.casefold(), job.company.casefold(), job.location.casefold())
                        if job.id in seen_ids or link in seen_links or title_key in seen_titles:
                            continue
                        seen_ids.add(job.id); seen_links.add(link); seen_titles.add(title_key)
                        jobs.append(job)
                except JobSearchError:
                    raise
                except (requests.RequestException, ValueError, TypeError):
                    warnings.append(f'Could not retrieve {role} in {location}; other searches may still have results.')
    if excluded_ids:
        warnings.append(f'Excluded {len(excluded_ids)} postings whose explicit minimum experience exceeds your confirmed {experience_months} months.')
    return sorted(jobs, key=lambda j: j.posted_at, reverse=True)[:10], list(dict.fromkeys(warnings))
