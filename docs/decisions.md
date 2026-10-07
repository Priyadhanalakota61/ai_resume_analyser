# Confirmed product decisions

_Last updated: 2026-10-07_

This file records decisions stated by the user. Open questions are listed separately and must not be treated as settled.

## Confirmed

- Repository: `Priyadhanalakota61/resume_analyzer`.
- Product branch: `resume_analyzer`.
- Stack: Flask, MySQL, Gemini API.
- Each analysis accepts:
  - A resume PDF.
  - A job description.
- The product outputs:
  - An ATS score.
  - Relevant interview questions.
  - Suggestions based on skills.
- MySQL should store:
  - Extracted resume text.
  - Generated analysis results.
- The original uploaded PDF is not specified for storage; do not persist it unless the user explicitly requests that.

## Open questions

- Exact ATS score formula and which criteria affect the score.
- Whether to store the job description in MySQL.
- Data-retention period and whether the app needs a delete function.
- Database name and local MySQL connection details.
- Gemini key availability and the active quota for the selected model.
- Deployment target and any requirements beyond local development.

## Privacy implementation requirement

The Gemini free tier may use prompts and responses to improve Google products. Before sending personal resume text to Gemini, the product must explain the applicable data handling and obtain the user's explicit confirmation. Use synthetic or anonymized resumes for development and demos.
