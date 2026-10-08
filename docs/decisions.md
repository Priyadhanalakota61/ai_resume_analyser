# Confirmed product decisions

_Last updated: 2026-10-07_

This file records decisions stated by the user and the project scoring method adopted at the user's direction. It distinguishes project behavior from industry-wide claims.

## Confirmed by the user

- Repository: `Priyadhanalakota61/resume_analyzer`.
- Product branch: `resume_analyzer`.
- Stack: Flask, MySQL, Gemini API.
- Each analysis accepts a resume PDF and a job description.
- MySQL should store extracted resume text and generated analysis results.
- The original uploaded PDF is not specified for storage; do not persist it unless the user explicitly requests that.

## Project scoring method

The user asked us to use corporate HR practice as a reference. ATS products vary; there is no single score formula established for all employers. For this project, use a transparent **ATS-style job-match estimate**:

1. Extract the explicit job requirements from the job description.
2. Compare each requirement to evidence in the extracted resume text.
3. Mark each requirement as either `matched` or `not_found`; do not infer that an unsupported qualification is present.
4. Calculate `matched requirements / total extracted requirements * 100`, with every requirement counted equally.
5. Show the requirement list and resume evidence so the user can understand the estimate.

This is the project's defined matching method, not an official ATS score, a universal corporate HR formula, or a hiring decision. Do not claim it predicts the result of applying to a company. If no explicit requirements can be identified, report that a score could not be calculated instead of inventing a number.

## Open questions

- Whether to store the job description in MySQL.
- Data-retention period and whether the app needs a delete function.
- Database name and local MySQL connection details.
- Gemini key availability and active quota for the selected model.
- Deployment target and any requirements beyond local development.

## Gemini free-tier restriction

Google's terms for unpaid Gemini API services say not to submit sensitive, confidential, or personal information. Free-tier prompts and responses may be used to improve Google products, and human reviewers may process them. The app must therefore require the user to confirm that the uploaded resume is synthetic or anonymized before sending extracted text to Gemini. That confirmation does not make it acceptable to submit personal information.

Official terms: https://ai.google.dev/gemini-api/terms
