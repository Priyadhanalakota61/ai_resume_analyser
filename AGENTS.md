# Resume Analyzer project agent instructions

## Mission

Develop the Resume Analyzer on the `resume_analyzer` branch of this repository.

The repository README defines the product as: accept a resume PDF and provide an ATS score, relevant interview questions, and suggestions based on skills. The user confirmed that each analysis will use a resume PDF plus a job description, and that MySQL should save both extracted resume text and generated results. The user also confirmed Flask, MySQL, and the Gemini API as the intended stack.

Treat the repository and explicit user decisions as requirements. Do not invent additional product behavior, scoring criteria, data-retention rules, deployment targets, or credentials. If a necessary decision is not established, pause and ask. Keep confirmed decisions in `docs/decisions.md`; never record assumptions as facts.

## Branch and repository safety

- Before editing, inspect the current branch and repository status.
- Make project changes only on `resume_analyzer`.
- Never commit to or push to `main`.
- Preserve existing user work. Do not reset, clean, discard, or overwrite unrelated changes.
- Do not push, publish, deploy, open a pull request, or merge unless the user explicitly requests that action.
- Do not claim a branch, commit, test, API request, or database operation succeeded unless tool output verifies it.

## Secrets and resume privacy

- Keep API keys, database passwords, uploaded resumes, and extracted personal data out of Git, logs, screenshots, examples, and test fixtures.
- Keep local credentials in `.env` and ensure `.env` is ignored. Commit only `.env.example` with blank or placeholder values.
- Never ask the user to paste a secret into chat. Explain how to add credentials locally.
- Use synthetic or anonymized resumes for development and demos.
- The user may have a Gemini free-tier API key; key presence and quota are not confirmed.
- The user authorized storing extracted resume text and generated analysis results in MySQL. Do not store the original uploaded PDF unless the user explicitly decides to.
- Before any real resume text is sent to Gemini, the application must disclose the applicable Gemini free-tier data handling and require an explicit user confirmation in the product flow. Do not transmit the resume to Gemini without that confirmation.
- No retention period or deletion workflow has been specified. Do not claim a retention period or implement automatic deletion without asking.

## Build and verification method

1. Read repository instructions and README before coding. Inspect the current files and report the actual project state.
2. Implement only confirmed requirements. Ask before resolving material product decisions that are not specified.
3. Use Flask, MySQL, and Gemini as the agreed stack. Keep provider calls in a small service module so integration details are isolated.
4. Accept the confirmed inputs: PDF resume and job description. Validate the PDF and handle unreadable/empty text, unsupported files, missing API credentials, Gemini quota/errors, and database connection failures with clear messages.
5. Generate only the confirmed outputs: ATS score, relevant interview questions, and skill-based suggestions. Do not add extra user-facing analysis features unless requested.
6. Do not fabricate model output when Gemini fails. Clearly distinguish unavailable analysis from successful analysis.
7. Explain what the ATS score actually measures once its formula is agreed. Never present it as an official ATS score or hiring decision. The exact score formula remains undecided.
8. Add focused tests for meaningful behavior, especially PDF validation/extraction boundaries, scoring after criteria are confirmed, API response parsing, and MySQL persistence.
9. Run available checks and report exactly which passed. Clearly identify any check that requires the user's local MySQL server or Gemini credentials.
10. Keep setup instructions accurate to the implementation. Do not claim the project is fully tested when a dependency, database, or credential was unavailable.

## Confirmed scope and decisions

- Repository: `Priyadhanalakota61/resume_analyzer`.
- Product branch: `resume_analyzer`.
- Agreed stack: Flask, MySQL, Gemini API.
- Inputs: resume PDF and job description.
- Outputs: ATS score, relevant interview questions, and skill-based suggestions.
- MySQL should store extracted resume text and generated analysis results; do not store source PDFs unless the user decides to.
- The user has MySQL Workbench installed; this does not confirm that a local MySQL server is running or configured.
- The user may have a Gemini free-tier API key; key presence and quota are not confirmed.
- The exact ATS scoring formula, retention period, deletion workflow, database name, UI details, and deployment target remain unspecified. Do not assume them.
