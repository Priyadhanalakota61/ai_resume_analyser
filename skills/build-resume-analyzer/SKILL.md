---
name: build-resume-analyzer
description: Build, test and troubleshoot the Flask/MySQL/Gemini Resume Analyzer, including resume-driven job discovery for up to three locations, ten recent sourced postings, evidence-based match estimates and interview preparation. Use for upgrades, job-provider integration, demo setup and repository work.
---

# Build Resume Analyzer

## Ground the implementation
Read AGENTS.md, README.md and docs/decisions.md in Priyadhanalakota61/ai_resume_analyser. Inspect branch/status. Work on resume_analyzer; preserve main and local edits unless explicitly authorized otherwise. Treat explicit user requirements as overriding older scope. Persist this skill by staging only its folder, committing and pushing the skills workspace current branch.

## Product contract
Accept selectable-text resume PDFs. Preserve manual job-description comparison and add resume-driven discovery. Extract a source-grounded profile, suggest role searches for user review, accept one to three locations (Remote is allowed), and show up to ten deduplicated recent jobs across the selections. Sort the retrieved subset by source-reported date, not model-generated dates. Default country to India with a configurable country code. Show fewer results honestly; never fabricate missing listings.

Display title, company, source location, provider/publisher, source-reported date, retrieval time and specific application link. Label listings as provider-reported; do not claim employer-confirmed openness without evidence. Prefer provider-marked direct links. Reject unsafe links and identifiable generic search pages. Do not fetch arbitrary application URLs server-side or bypass job-board controls.

Use an isolated provider adapter. Verify official endpoint/authentication/response docs before coding. JSearch through OpenWeb Ninja is the initial adapter: GET https://api.openwebninja.com/jsearch/search-v2 with x-api-key, query, country, language, date_posted and optional work_from_home. Never assume live coverage, key availability, quota or full descriptions. Configure JOB_SEARCH_API_KEY privately; do not provision accounts or paid plans. Do not use Gemini's memory as a job source. Report missing credentials, timeouts, quota errors and partial search failures clearly.

## Evidence and scoring
Require exact resume excerpts for profile skills and role suggestions. Let users edit the role searches; suggestions are not eligibility judgments. For each job, generate distinct explicit requirements with exact job-description excerpts. Count matched only when exact resume evidence exists. Normalize whitespace/case for excerpt checks, deduplicate requirements, and reject unsupported evidence. Compute matched / total requirements * 100 equally in Python; return no score for zero requirements or insufficient/truncated descriptions. Label it job-match estimate, not official ATS score. Show requirement evidence, strengths, gaps (not found in resume), suggestions and role-specific practice questions. Do not imply these are actual employer questions. Text evidence checks reduce unsupported output, not guarantee semantic truth.

## Implementation boundaries
Keep Flask, MySQL, Gemini and existing PDF extraction. Never store PDFs or raw job descriptions. Persist extracted resume text and generated results in the existing analysis table; include source metadata in generated results. Explain stored data and absence of expiry/deletion. Require synthetic/anonymized input for unpaid Gemini; preserve terms notice. Keep credentials and user documents out of Git/logs. Do not change a working Gemini model solely based on age; retain env override.

Use bounded server-side transient state with TTL, browser ownership, CSRF and a stable optional SECRET_KEY; never put resume text in signed client cookies. Show jobs before sequential per-job analysis. Cache each completed outcome, handle provider/model failures independently and avoid duplicate calls on refresh. Do not claim durable queueing or cross-worker state for an in-process prototype. Keep MySQL preflight before Gemini. Escape all externally sourced text; sanitize outbound URL schemes. Limit file/text sizes, locations, role searches, provider calls and model output. No autonomous applications or recruiter messaging.

## Validation and handoff
Test provider parsing, dates, expiration, duplicate removal, unsafe/generic URLs, partial failures, missing keys, description limits, evidence validation, no-score cases, ownership/CSRF, per-job caching, database failures and manual flow. Use synthetic fixtures and mocked provider/Gemini calls. Run available tests and a UI/template smoke check. Distinguish mocked checks from live MySQL/Gemini/job-provider verification; never claim the latter without credentials and successful calls.

Commit authorized product changes to resume_analyzer, include this skill's snapshot in the repository for reproducibility, and open a reviewable PR when authorized. Do not merge the upgrade merely because an earlier version was merged. Provide Windows update commands that preserve .env, dependency install instructions and the single remaining provider-key step. Report limitations without calling a credential-blocked live workflow fully verified.
