# Resume Analyzer

Resume Analyzer takes a resume PDF and a job description, then provides an ATS-style job-match estimate, interview practice questions, and suggestions based on skills.

## Current implementation

- Flask application and upload form.
- Extracts selectable text from PDF resumes in memory; scanned-image OCR is not implemented.
- Sends the extracted text and job description to the configured Gemini model only after the user confirms the resume is synthetic or anonymized.
- Shows a job-match estimate, requirement evidence, skill feedback, suggestions, and interview questions.
- Saves extracted resume text and generated results to MySQL. The uploaded PDF and job description are not stored.
- MySQL creates the `analysis_records` table automatically when the selected database exists and is reachable.
- The request limit is 5 MiB.

## ATS-style job-match estimate

This project uses a transparent, project-defined estimate:

`matched requirements / all identified job requirements * 100`

Each identified requirement counts equally. The result is not an official ATS score, a hiring decision, or a prediction of a company's screening outcome. The analysis displays the requirements and resume evidence used.

## Gemini free-tier privacy

Google's terms for unpaid Gemini API services say not to submit sensitive, confidential, or personal information. Free-tier prompts and responses may be used to improve Google products, and human reviewers may process them. For this version, use only synthetic or anonymized resume content. The app asks for confirmation and links to [Google's Gemini API terms](https://ai.google.dev/gemini-api/terms).

## Run locally on Windows

Use Python 3.10 or newer. Create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit the local `.env` file and set:

- `GEMINI_API_KEY`: your key from Google AI Studio.
- `GEMINI_MODEL`: defaults to `gemini-2.5-flash-lite`; change it only to a model available to your AI Studio project.
- `DATABASE_URL`: your MySQL connection string.

Example format (replace every placeholder):

```text
DATABASE_URL=mysql+pymysql://<username>:<password>@localhost:3306/<database>?charset=utf8mb4
```

Create the database in MySQL Workbench first and use its name in `DATABASE_URL`. If your password contains URL-reserved characters, URL-encode it in the connection string. Do not share your Gemini key or database password in chat or commit the `.env` file.

Start Flask:

```powershell
python run.py
```

Open http://127.0.0.1:5000. The `/health` route returns a small application health response.

## Run tests

```powershell
python -m pytest
```

## Stored data

The MySQL table stores the extracted resume text and generated result JSON, including the requirement evidence used for the score. The original PDF and job description are not stored. Records remain in MySQL until manually removed; this version has no in-app deletion or automatic expiration.

## Known limits

- The app needs a running MySQL server, an existing database, and valid local connection settings before it will call Gemini.
- The app needs a working Gemini API key and available model quota.
- Free-tier data rules restrict the app to synthetic or anonymized resume content.
- Password-protected PDFs, scanned-image PDFs, and PDFs with no extractable text are not analyzed.
