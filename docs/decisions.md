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

## 2026-10-11: User-authorized job discovery upgrade

- Repository renamed to Priyadhanalakota61/ai_resume_analyser; continue on resume_analyzer. The prior version is merged into main; this upgrade is not automatically merged.
- New input: selectable-text resume PDF and one to three preferred locations, with Remote supported. User requested up to ten recent jobs, links, fit estimates, strengths/gaps and per-role interview practice.
- Keep the existing manual comparison available. Add profile evidence and editable role suggestions before search.
- Implementation choice: direct OpenWeb Ninja JSearch search-v2, country default in, last-month search, bounded first-page retrieval. Adzuna was considered but its documented search descriptions are snippets. No provider subscription/key or live access has been provisioned or verified.
- Sort source-dated retrieved subset; exclude explicit expired/inactive jobs, deduplicate and cap at ten across locations. Do not promise all jobs worldwide or independently confirmed employer openness.
- Reuse the equal-weight estimate with exact job/resume excerpt checks. No score if requirements/description are insufficient. Model reasoning is still advisory.
- Save each completed job comparison in the existing analysis_records generated_result JSON with profile/source metadata. Do not store raw job descriptions or PDF; quoted evidence belongs to generated results.
- In-process transient workflow state expires after 30 minutes (pruned on access), bounded at 20, with browser ownership/CSRF. Sequential per-job HTTP requests reuse outcomes in that workflow. This is not durable multi-worker hosting.
- Keep working Gemini env override. Up to nine provider and eleven Gemini calls per completed workflow; no fabricated fallback results or automatic unlimited retries.

## Profile evidence recovery

Reject unsupported profile entries individually rather than aborting all discovery. Keep valid excerpts; allow exact whole-token short skill names. Show an omission notice and editable manual role inputs when no suggestions survive. Do not invent fallback skills/roles or relax per-job evidence/scoring checks. Malformed provider/model responses still report an error.

### Job-provider response fix
The user's successful local HTTP 200 diagnostic confirmed search-v2 returns `data` as an object with `jobs` and `cursor`. Parse `data.jobs`, retain list-envelope compatibility, and distinguish malformed envelopes from valid empty results. Regression tests use synthetic postings; no live credentials are included.

### Structured analysis compatibility
A local synthetic test succeeds without structured output while the analysis request returns HTTP 400 INVALID_ARGUMENT with no field detail. Simplify the provider schema by inlining definitions and omitting length/count constraints and titles/defaults from the wire representation. Preserve the original Pydantic response validation and evidence checks. This addresses a schema compatibility suspect; live success must be confirmed locally and no specific rejected keyword is established.

### Experience-aware search
User requested filtering jobs by resume experience rather than analysing clearly over-level listings. Require a user-confirmed total in whole months, optionally prefilled from one unambiguous explicit resume duration; do not infer from graduation or silently sum overlaps. Parse explicit English experience minima conservatively and filter above-total postings before the ten-result cap and Gemini analysis. Unknown requirements remain visible and labelled, never declared suitable. Do not interpret preferred-only or upper-bound wording as a minimum. Preserve newest-first ordering among retained postings and manual comparison.

### Strict experience filtering correction
A screenshot showed a four-year frontend requirement passing as unknown for a twelve-month candidate. Extend explicit duration extraction to handle intervening domain words (for example, hands-on frontend engineering). Change discovery to exclude unrecognised experience requirements before analysis rather than displaying uncertain fits. Accept explicit no-experience-required or freshers-welcome statements as zero only when no larger mandatory parsed requirement exists. Fewer than ten results is preferable to filling the list with unclear experience matches. No live coverage or complete semantic parsing is claimed.
