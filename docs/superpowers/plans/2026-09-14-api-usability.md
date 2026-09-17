# Free API usability implementation plan

> For agentic workers: implement the independently testable slices below in parallel, preserving file ownership, then review their integration together.

**Goal:** Make the free API discoverable and predictable for developers and AI workflows on the existing Oracle server.

**Architecture:** Retain synchronous handlers and SQLite persistence. Add shared admission/accounting, a public v1-only catalog/schema, and an optional durable job worker within the existing container resource envelope.

**Tech stack:** FastAPI, Python 3.12, standard-library SQLite/subprocess, React/TypeScript, pytest and Vitest. No additional runtime service dependencies.

**Spec:** `docs/superpowers/specs/2026-09-14-api-usability-design.md`.

## Global constraints

- Existing Oracle VM only; free access; developers and AI/workflow users equally supported.
- Preserve synchronous success contracts and anonymous website access.
- Results expire 3,600 seconds after completion and support explicit deletion.
- Use synthetic keys and fixtures for tests. Never store the owner's key in source or test artifacts.
- No production load generation or deployment during implementation.

## Task 1: request admission and accounting

Ownership: `backend/app/api_v1/{deps,quota,router}.py`, new admission/policy/body-accounting modules, `backend/app/rate_limit.py`, relevant store migrations and tests. Root integrates middleware in `main.py`.

- [x] Add actual ASGI body counting with `V1AccountingMiddleware`; wrap `receive`, do not buffer a second request copy.
- [x] Use shared SQLite reservations and leases; all settlement uses the recorded original UTC day.
- [x] Enforce three admitted HTTP requests per verified key and shared per-key minute limits; preserve legacy IP limits.
- [x] Preserve `quota.cost_for(path)` for catalog callers; make costs explicit and charge pipeline steps consistently.
- [x] Distinguish framework validation using `request.state.v1_validation_rejected`, including response headers after refunds.
- [x] Add two-process SQLite races, body accounting, independent-key, cancellation cleanup and midnight settlement tests.

Run targeted checks with:

```sh
.venv/bin/python -m pytest backend/tests/test_api_v1.py backend/tests/test_api_v1_admission.py -q
```

Admission acceptance must include assertions equivalent to:

```python
assert len(successfully_admitted_same_key_requests) == 3
assert rejected_response.status_code == 429
assert "Retry-After" in rejected_response.headers
assert quota_after_validation_error == quota_before_validation_error
```

## Task 2: discovery and integration documentation

Ownership: new `backend/app/api_v1/catalog.py`, `schema.py`, docs router and tests; `frontend/src/pages/ApiPage.tsx`, associated tests/CSS; `frontend/scripts/gen-llms.mjs`. Root mounts docs after the v1 and jobs routes.

- [x] Publish public non-metered `/api/v1/operations` and `/api/v1/openapi.json`.
- [x] Derive only effective v1 routes using the installed FastAPI router contexts; ensure unique IDs and resolved schema references.
- [x] Add reviewed response/constraint metadata and explicit browser-only exclusions; costs call the shared quota facade.
- [x] Correct alternative X-API-Key/Bearer schema names in coordination with Task 1.
- [x] Add searchable catalog-driven human docs, runtime-derived API base, exact fields and working curl/Python/JavaScript/HTTP-workflow examples.
- [x] Test catalog coverage, binary/JSON responses, anonymous discovery, loading/search/error states and authentication privacy.

```sh
.venv/bin/python -m pytest backend/tests/test_api_v1_discovery.py -q
cd frontend
npx tsc --noEmit -p tsconfig.app.json
npm run lint -- --max-warnings 0
npm run test -- --run
npm run build
```

## Task 3: error compatibility and native processing lifetime

Ownership: root; `backend/app/middleware/error_handlers.py`, `utils/concurrency.py`, `routes/developer.py`, corresponding tests.

- [x] Reproduce cancellation releasing capacity while native work still runs.
- [x] Tie semaphore release to native future completion and move pipeline work to this executor.
- [x] Add stable v1 code/message fields while preserving legacy detail/error/request-ID behavior.
- [x] Mark framework validation rejections explicitly and sanitize v1 server errors.
- [x] Update the v1 developer status response to point to the curated schema/catalog.

```sh
.venv/bin/python -m pytest backend/tests/test_concurrency.py backend/tests/test_developer_pipeline.py backend/tests/test_api_v1_error_contract.py backend/tests/test_error_handler_mappings.py -q
```

## Task 4: durable optional job execution

Ownership: jobs worker; new `backend/app/api_v1/jobs/` package and job tests. Root owns app/launcher/deployment integration and retention documentation.

- [x] Add independently initialized job schema and validated explicit adapters for grayscale, preset compression, PDF merge and text extraction.
- [x] Mount authenticated additive submit/status/result/delete endpoints. Require idempotency for submission and enforce exact-once charging within the shared SQLite transaction.
- [x] Persist and fsync input files before queue acceptance; enforce per-job, aggregate storage and queue budgets.
- [x] Run one supervisor with claim fencing and child process-group termination; set scratch directories before importing services.
- [x] Add bounded recovery, per-key/account fairness, revocation, TTL access enforcement, explicit deletion and orphan cleanup.
- [x] Test concurrent duplicate submissions, another key's job access, worker interruption, stale claims, storage limits and result deletion/expiry.
- [x] Expose `capability()` and `python -m backend.app.api_v1.jobs.worker --healthcheck` for discovery/readiness.

```sh
.venv/bin/python -m pytest backend/tests/test_api_v1_jobs.py -q
```

## Task 5: integration, resource envelope and release evidence

Ownership: root; `main.py`, launcher, Dockerfile/Compose/deploy contract, README/retention pages and integration evidence.

- [x] Integrate accounting middleware, job initialization/router and public docs in an order verified by tests.
- [x] Launch one worker beside the two existing web processes under the existing container's combined CPU/memory limits. Disabled mode preserves the old command behavior.
- [x] Gate enabled-job readiness on worker health/build and implement bounded shutdown/recovery. Keep new database structures additive for rollback compatibility.
- [x] Document exact default limits, body/cost semantics, error retry rules and one-hour result retention.
- [x] Run targeted integration tests, complete backend/frontend checks and inspect the rendered API page.
- [x] Run bounded local fixture workloads and retain measured results as local evidence, explicitly not an Oracle capacity promise.
- [x] Review the final diff and report what is implemented, tested and still requires production rollout validation.

## Implementation status

Implemented on `codex/api-usability-upgrade`. The changes remain undeployed and
`API_V1_JOBS_ENABLED` defaults to false. Local checks validate behavior, not the
Oracle host's throughput or a production image rollout. See
`docs/verification/api/api-usability-validation.md` for the final checks and remaining
production validation.
