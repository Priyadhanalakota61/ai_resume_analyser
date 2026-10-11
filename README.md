# ResumeMatch — Resume Analyzer and Job Discovery

Flask / MySQL / Gemini portfolio prototype. Upload a **synthetic or thoroughly anonymized** selectable-text resume PDF, enter up to **three locations**, review/edit suggested roles, and discover up to **ten recent sourced postings** across those locations. Jobs load first; their comparisons run sequentially and appear progressively. The original manual PDF + job-description comparison remains available.

## Results

- Resume skills and suggested role searches with supporting excerpts. Unsupported profile entries are omitted individually; if no role survives, enter a role manually. Explicit short skill tokens such as SQL are accepted only as whole tokens.
- Job title, company, source location, publisher, application link, source-reported date and retrieval time.
- Job-match estimate, explicit requirements with job/resume excerpts, strengths, gaps, suggestions and role-specific interview practice questions.
- Matching is `matched requirements / all identified requirements * 100`, counted equally in Python. No requirements means no score. It is **not an official ATS score**, eligibility decision or screening prediction. Gaps mean evidence was not found; questions are practice suggestions.
- Exact excerpt checks reject unsupported evidence, but do not prove semantic correctness or eliminate all model errors.

## Job source and honesty

The adapter uses [JSearch through OpenWeb Ninja](https://www.openwebninja.com/api/jsearch), `GET https://api.openwebninja.com/jsearch/search-v2`, authenticated with `x-api-key`. This is the **direct portal key**, not a RapidAPI key. Configure `JOB_SEARCH_API_KEY` locally. No account or subscription is created by this project; check provider terms and quotas before use.

Searches request the last month and locally exclude missing dates, dates older than 30 days, future dates, explicit expired/inactive postings, recognized broad search pages and unsafe links. Direct application links marked by the provider are preferred. Dates and active state are **provider-reported**, not independently verified at the employer. A reachable page would not prove applications remain open. The app does not scrape job boards or fetch arbitrary application URLs server-side.

Up to three role queries x three locations = **at most nine provider requests**, one first page per query; no hidden pagination/retries. Deduplicated results are sorted newest first, then capped at ten. This is the newest subset retrieved, not a guarantee of the newest ten jobs worldwide. Fewer results are displayed honestly. Remote searches request provider-reported remote roles in the configured country; country/time-zone restrictions still require review.

Descriptions under 200 or over 30,000 characters, or visibly truncated with trailing ellipsis, are not scored. This heuristic cannot prove completeness. Retrieved descriptions are shown to Gemini for comparison; missing data or failed analysis produces an availability message, never invented listings/scores. Provider coverage and response compatibility must be confirmed with a live key.

## Update an existing Windows installation

Stop the app with Ctrl+C. From PowerShell in your existing project folder:

```powershell
git status
git fetch origin
git switch resume_analyzer
git pull --ff-only origin resume_analyzer
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
notepad .env
```

Preserve local changes and your existing `.env`. If Git reports a conflict or refuses to switch, resolve it before continuing; do not discard user work. Add these lines to your existing `.env` (keep the working Gemini model/key and database URL):

```text
JOB_SEARCH_API_KEY=YOUR_OPENWEB_NINJA_KEY
JOB_SEARCH_COUNTRY=in
SECRET_KEY=YOUR_PRIVATE_RANDOM_SESSION_KEY
```

Get a direct JSearch key from the provider's developer portal. Select a plan yourself; the app does not purchase anything. Do not share keys in chat or commit `.env`. Generate a random session key locally, for example:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Copy that value into SECRET_KEY. If omitted, the app generates a key at startup and sessions reset on restart. Start:

```powershell
.\.venv\Scripts\python.exe run.py
```

Open http://127.0.0.1:5000. Use the new job-discovery form, review the suggested roles, then search. Analyses begin automatically after listings load; individual buttons show cached outcomes. One profile extraction + up to ten job analyses means **up to eleven Gemini requests** per workflow. Quota failures affect individual cards. To retry a cached failed analysis after resolving configuration, start a new workflow.

## First-time setup

Use Python 3.10+ (3.12 recommended):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set GEMINI_API_KEY, a GEMINI_MODEL available to your key, DATABASE_URL and the job-provider settings above. Do not overwrite an existing `.env`. Create your MySQL database in Workbench first; Workbench is a client and the MySQL server must run. Connection format:

```text
DATABASE_URL=mysql+pymysql://USERNAME:URL_ENCODED_PASSWORD@127.0.0.1:3306/DATABASE?charset=utf8mb4
```

The existing analysis_records table is reused, so no destructive migration is needed. Missing tables are created automatically; the database itself must exist. MySQL preflight precedes Gemini calls. Passwords with reserved characters must be URL encoded. Keep the Gemini model that already works locally; model availability is not guaranteed by a fallback value.

## Data and privacy

Use synthetic/anonymized resumes under [unpaid Gemini data-use terms](https://ai.google.dev/gemini-api/terms). The app requires confirmation and does not automatically anonymize PDFs. Remove identifiers and sensitive/confidential data yourself.

MySQL persists extracted resume text and generated results. Job-discovery results include the extracted profile, job source metadata and analysis evidence, not the raw job description or PDF. Records have no automatic expiry or deletion screen. A description's quoted requirements may appear within generated analysis evidence. No job applications are submitted.

Private workflow state (resume, descriptions and outcomes) lives only in a bounded, server-side memory store: 20 workflows, 30-minute TTL, browser ownership and CSRF checks. Expired state is inaccessible and pruned on access. Resume text is never placed in the session cookie. Restart/eviction loses transient workflows; MySQL records remain. This is a **single-process local demo**, not a durable multi-worker queue. Public deployment requires a shared private state backend, authentication, quotas and retention policy; it is not implemented here.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover scoring, provider parsing/errors, date/expiration filters, URL checks, duplicate removal, evidence rejection, missing descriptions, private ownership/CSRF, cached analysis, database error handling and the profile-to-dashboard/manual flows. Provider and Gemini are mocked; production MySQL is not exercised. Confirm all three live services locally before presenting. A mock test suite is not proof of live job coverage.

## Repository and reusable skill

Repository: Priyadhanalakota61/ai_resume_analyser. Upgrade work lives on `resume_analyzer`. Review the upgrade before merging into main. `skills/build-resume-analyzer/SKILL.md` records the reusable implementation contract; the corresponding ChatGPT skill is saved separately in the Skills workspace.

### Experience-aware discovery
Confirm work experience in whole months on the role-review form (2 years = 24 months). A single explicit resume duration can prefill it; ambiguous statements and dated histories require manual confirmation. Education and gaps are never counted automatically. Decide whether to include internships; employer acceptance varies. Before selecting ten postings or calling Gemini, exclude parsed explicit minimum experience above the confirmed total. Conservative English duration rules handle common year/month ranges; preferred-only and upper-bound statements are not treated as mandatory minimums. Unrecognised experience requirements are excluded from discovery rather than analysed. Explicit no-experience-required or freshers-welcome statements can establish a zero-month minimum. This is a search filter, not proof of eligibility or complete semantic parsing. Fewer than ten jobs may remain. Confirmed duration and posting excerpts are included in saved analysis metadata.
