# Resume Analyzer project agent instructions

## Mission

Develop the Resume Analyzer on the `resume_analyzer` branch of this repository.

The repository README currently defines the product as: accept a resume PDF and provide an ATS score, relevant interview questions, and suggestions based on skills. The user has also confirmed Flask, MySQL, and Gemini API as the intended stack.

Treat those statements and future explicit user decisions as requirements. Do not invent additional product behavior, scoring criteria, data-retention rules, deployment targets, or credentials. If a necessary decision is not established by the repository or the user, pause and ask. Keep confirmed decisions in `docs/decisions.md`; never record assumptions as facts.

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
- The user believes they may have a Gemini free-tier API key. Do not claim it is valid or available until an actual local check confirms it.
- Before sending any real resume to Gemini, explain the applicable data handling and obtain the user's explicit consent for that data transfer.
- Do not persist uploaded PDFs or extracted resume content unless the user explicitly approves the retention behavior. Ask when persistence becomes necessary.

## Build and verification method

1. Read repository instructions and the README before coding. Inspect the current files and report the actual project state.
2. Implement only confirmed requirements. Ask before resolving material product decisions that are not specified.
3. Use Flask, MySQL, and Gemini as the agreed stack. Keep provider calls in a small service module so integration details are isolated.
4. Validate the PDF and handle unreadable/empty text, unsupported files, missing API credentials, Gemini quota/errors, and database connection failures with clear messages.
5. Do not fabricate model output when Gemini fails. Clearly distinguish unavailable analysis from successful analysis.
6. Explain what the ATS score actually measures once its formula is agreed. Never present it as an official ATS score or a hiring decision.
7. Add focused tests for meaningful behavior, especially validation, extraction boundaries, scoring after criteria are confirmed, API response parsing, and persistence after retention is decided.
8. Run available checks and report exactly which passed. Clearly identify any check that requires the user's local MySQL server or Gemini credentials.
9. Keep setup instructions accurate to the implementation. Do not claim the project is complete or tested beyond the evidence.

## Confirmed scope and decisions

- Repository: `Priyadhanalakota61/resume_analyzer`.
- Product branch: `resume_analyzer`.
- Agreed stack: Flask, MySQL, Gemini API.
- Confirmed product input/output from README: resume PDF; ATS score, interview questions, and suggestions based on skills.
- MySQL Workbench is installed on the user's device; that alone does not confirm the MySQL server is running or configured.
- The user may have a Gemini free-tier API key; key presence and quota are not confirmed.
- Exact scoring formula, additional inputs such as a job description, database schema, retention policy, UI details, and deployment target are not yet specified. Do not assume them.
