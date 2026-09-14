# API onboarding Implementation Plan

**Goal:** Let developers and workflow users run, integrate, and troubleshoot the free API.

**Architecture:** Extend the existing API page and account surfaces; add bounded metadata in the shared SQLite database. Ship static starter downloads and a finite benchmark using the existing API contract.

**Tech Stack:** FastAPI, SQLite, React/TypeScript, Python, Node, existing test runners.

**Spec:** `docs/superpowers/specs/2026-09-14-api-onboarding-design.md`

## Constraints

- Existing Oracle server, same CPU/memory budget, no new services.
- Seven-day metadata retention, 1,000 recent records/key, 100,000 globally; 50 returned.
- No document contents, filenames, raw messages, query strings, or credentials in history.
- Normal quotas for playground; no automatic synchronous retry.
- Saved background results retain the existing one-hour lifetime and immediate deletion.

## Execution

- [x] Backend worker: add activity store/schema, instrument authenticated processing, expose account-scoped activity, test ownership/privacy/expiry/caps/failure isolation.
- [x] Playground worker: add sample PDFs, safe bounded HTTP client/UI, explicit run/download/cancel, allowance comparison, targeted tests.
- [x] Starter worker: Python/JS lifecycle clients, resume/delete modes, n8n workflows, Postman collection, deterministic public downloads, mock HTTP behavior tests.
- [x] Root: account API adapters and validated dashboard in both account surfaces; test empty/error/filter/stale account states and responsive behavior.
- [x] Root: bounded synthetic capacity harness and isolated Oracle measurements; do not increase current limits without supporting evidence.
- [x] Review combined diff, run backend/frontend/type/lint/build and artifact tests, exercise actual conversions and browser UI, fix material findings.
- [ ] Prepare reviewed release and validate candidate/production through existing signed-image rollout.

## Interfaces and ownership

Backend owns `backend/**` and backend tests. Playground owns `ApiPage.tsx`, dedicated playground modules/CSS/tests. Starters own `examples/api/**`, `frontend/public/api-starters/**`, `scripts/api-starters*`, and `docs/api-starters.md`. Root owns account client/component, account integration, benchmark, this plan, and release evidence.

The dashboard consumes GET `/api/account/api-activity?key_id=...`: `keys[{key_id,label,revoked,units:{used,limit,remaining},bytes:{used,limit}}]`, `resets_at`, `days[{date,requests,succeeded,failed,avg_duration_ms}]`, and `recent[{request_id,key_id,operation,method,status_code,error_code,duration_ms,created_at}]`. Queries and aborted responses are scoped to the active account. Public download URLs begin `/api-starters/` and match the generated manifest.
