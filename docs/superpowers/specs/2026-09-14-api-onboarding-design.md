# API onboarding and visibility

The user approved the next milestone: a sample playground, complete starter integrations, lightweight account usage visibility, and measured capacity on the existing Oracle server. This extends the existing free API without new infrastructure or relaxed limits.

## User experience

The API page offers explicit sample runs for merge, compress, and PDF text extraction. A key supplied by the visitor stays in memory. A run sends only bundled synthetic PDFs and uses normal metering. The result includes a download, HTTP status, request ID, elapsed time, and before/after allowance when both measurements are available. Examples contain environment-variable placeholders, never the real key. A cancellation or key change invalidates pending results and releases browser object URLs.

Downloadable Python and Node starters use background jobs, stable idempotency per logical submission, finite retries that respect Retry-After, polling, download, and deletion after successful saving. Resume and retain options recover interrupted downloads. Postman requests and n8n workflows demonstrate equivalent complete integrations with credential-store configuration. Downloads are generated deterministically from reviewed source.

The account page shows current allowance by key, seven UTC days of request counts, HTTP successes/errors, average request duration, and 50 recent requests. Accepted background submission is an HTTP success, not evidence of a finished job. Account authentication and optional key filters enforce ownership. No API key needs to be pasted into this dashboard.

## Storage and privacy

Use the existing SQLite database. Record canonical operation, key ID, safe request ID, method, HTTP status, bounded error code, request duration, and timestamp. Never retain uploaded content, filenames, query strings, credentials, raw exception messages, or response bodies. Exclude informational requests and background status/download/deletion polling. Keep exact daily aggregate rows for seven days; cap recent records at 1,000 per key and 100,000 overall, and expire them after seven days. Account deletion cascades. Telemetry is best effort and cannot prevent an otherwise successful conversion or admission release.

GET `/api/account/api-activity` uses the existing local/Clerk session dependency. Optional `key_id` must belong to the account. Response contains `retention_days`, `recent_limit`, `resets_at`, `keys` with current units/bytes, zero-filled `days` with counts and average duration, and newest-first `recent` request metadata.

## Capacity and release

Provide a controlled benchmark with synthetic representative PDFs, finite concurrency and request budgets, temporary test keys, and a machine-readable result. Measure Oracle resource pressure and latency in an isolated candidate without changing production fair limits. Treat the results as fixture measurements rather than throughput guarantees. Preserve the existing 4 GiB / 1.8 CPU container and one background worker.

Verify ownership, retention, cancellation, quota semantics, retries, response parsing, credential privacy, responsive rendered UI, complete sample integrations, and the signed release gates before deployment. No dependency or infrastructure additions are required.
