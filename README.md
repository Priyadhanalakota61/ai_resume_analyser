# Resume Analyzer

Resume Analyzer takes a resume PDF and provides an ATS score, relevant interview questions, and suggestions based on skills.

## Current status

The repository currently contains the initial Flask application foundation. Resume upload, PDF extraction, Gemini analysis, MySQL persistence, and scoring have not been implemented yet.

The agreed stack is Flask, MySQL, and the Gemini API. The exact scoring criteria, additional inputs, and resume data-retention behavior are not specified yet and will be confirmed before those parts are built.

## Run locally on Windows

From the repository folder, open PowerShell and run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000 in a browser. The `/health` route returns a small application health response.

## Configuration and privacy

No Gemini API key or MySQL credentials are needed for this initial Flask page. When those integrations are added, configure secrets in a local `.env` file. The repository ignores `.env`; do not commit credentials.

Use synthetic or anonymized resumes for development and demos. Do not submit a real resume to Gemini until its data handling has been reviewed and the user has chosen to proceed.
