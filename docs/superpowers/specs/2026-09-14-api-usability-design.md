# Free API usability upgrade

Date: 2026-09-14. Source of product requirements: the owner's answers in this task.

## Product decisions

- Serve application developers and AI/workflow integrations equally.
- Keep public API access free with fair limits that protect service availability.
- Use the existing Oracle VM only. No additional server, paid service, or infrastructure purchase.
- Asynchronous results may remain available for 3,600 seconds after completion, with an immediate deletion action. Inputs are removed when no longer needed for execution/recovery.
- Preserve existing synchronous endpoint paths, authentication, successful response formats, and anonymous website access.

## Baseline and approach

The deployed application exposes 143 authenticated v1 operations through 67 tool routers and two account/usage endpoints. Its SQLite WAL database is persistent and shared by two web workers. Its minute limiter is currently process-local and IP-based; its three-per-key setting is unused. The generic heavy thread pool is per process, and not every route uses it. These are configured implementation facts, not measured throughput guarantees.

Use the existing SQLite database for short atomic admission and quota transactions. Keep native processing outside database transactions. Publish a curated v1 schema and operation catalog from the installed routes. Introduce asynchronous execution additively through explicit service adapters and a bounded worker on the same machine. Redis/Celery and additional hosts are unnecessary for the present workload; reconsider storage or worker topology only if measured contention or demand justifies it.

Implement and validate the following independently reviewable stages in order. Do not describe a later stage as deployed before its runtime and release checks pass.

## Stage 1: admission, accounting, and discovery

### Admission and accounting

Keep the current daily allowance of 500 units and 262,144,000 request-body bytes per key. Publish exactly what bytes and costs mean. Catalog costs must agree with execution costs. Pipelines reserve the sum of their supported steps; information-only discovery and status calls do not consume processing units.

Limit a key to three simultaneously admitted processing HTTP requests across both web workers. Use unique lease/reservation tokens with original quota day, verified key identity, idempotent finalization, and bounded stale-owner recovery. This is an admitted-request guarantee, not a claim that cancellation can terminate an arbitrary native thread. Offload database operations from the event loop.

Count actual ASGI request-body bytes, including multipart overhead, without a second full copy. Reject exceeded admission before invoking a processing service. Header sizes are only an early hint. Rejections and refunds must use the original admission day, including across UTC midnight. Explicit validation or admission failures may refund processing units; response status alone is not proof that no work happened.

Use shared authenticated per-key minute limits. Preserve IP protections for anonymous traffic. Only verified, admitted v1 calls may bypass the old per-route IP decorator; merely presenting a forged key must not create an exemption. Keep response retry information and usage headers coherent.

Route pipeline execution through the bounded heavy executor and ensure executor capacity remains occupied while a canceled native future is still running. Document the remaining limits of in-process execution honestly.

### Discovery and documentation

Add public non-metered `/api/v1/openapi.json` and `/api/v1/operations` endpoints. Include only the public v1 contract; retain the production block on whole-application OpenAPI, legacy/internal/account routes, and Swagger URLs.

Expose stable operation IDs, methods, paths, exact request schemas, response kinds, known constraints, current costs, limits, and async capability. Correct the two alternative authentication schemes in the schema. Do not invent unverified file formats or response fields.

Make the current API page a searchable reference driven by the catalog/schema, with copyable curl, Python, JavaScript, and HTTP-node workflow instructions. Clearly mark browser-only tools as unavailable through the API. Keep a short getting-started path and an accessible loading/error state. Generating frontend assets must not require Python during the frontend-only CI build.

Add stable v1 error `code` and `message` fields while retaining existing `detail`, validation information, and request IDs for compatibility. Existing safe server-error messages remain safe. Provide integration tests for representative binary and JSON operations.

## Stage 2: durable jobs on the existing host

Add authenticated `POST /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `GET /api/v1/jobs/{id}/result`, and `DELETE /api/v1/jobs/{id}`. Existing synchronous endpoints remain synchronous. Publish the exact supported async adapters; never imply all v1 operations support async execution.

Submission accepts an operation identifier, validated JSON options, multipart files, and an `Idempotency-Key`. The response is 202 only after input storage and queue acceptance are durable. The same identity and request fingerprint return the existing job without another processing charge; conflicting reuse returns 409. Status and result retrieval do not spend processing units.

All job lookup and file access are scoped to the verified key. Opaque identifiers are not authorization. Keep credentials out of files, state, and logs. Job states are queued, running, succeeded, failed, canceled, or expired. Completed results expire after 3,600 seconds; access checks enforce expiry even before cleanup runs. Deletion is idempotent and cancels outstanding work before removing its artifacts.

Use a separate worker process within the same signed container image and persistent volume. Start with one executing asynchronous job, bounded pending jobs and staged bytes, and per-key/account fairness. Set scratch paths before service imports. Keep job files outside the ordinary ten-minute temporary-file janitor. Use claim tokens, bounded attempts/deadlines, process-group termination, and conditional result publication to prevent stale attempts publishing over current work. Do not claim exactly-once computation.

Begin with a small reviewed set of service adapters covering single-file binary, multi-file binary, and structured output. Add expensive OCR/Office/media adapters only after their process cleanup and timeout tests pass. Unsupported operations must be rejected explicitly. Catalog async support must match the enabled adapter set and worker availability.

The combined web/worker configuration must remain within the existing host resource budget. Include worker heartbeat/build compatibility in readiness and the release rollback contract before enabling the feature on production. Update user-facing processing/retention documentation to match the one-hour result lifecycle.

## Validation and rollout

Use local/staging fixtures and synthetic keys, never the owner's posted key or real user documents, for concurrency tests. Verify cross-process SQLite admission races, quota boundaries, chunked bodies, midnight settlement, independent identities, cancellation and native-future completion, exact schema route coverage, supported parameter examples, and legacy website behavior.

For jobs, verify duplicate submission races, cross-key isolation, one processing charge, interrupted-worker recovery, stale claim fencing, expiry/delete/download races, bounded queues/storage, revoked keys, and cleanup. Validate the same-host worker configuration and rollback behavior before production enablement.

Measure increasing concurrency with representative small and large fixtures. Record processing latency, queue wait, failures, CPU, and memory. Publish supported concurrency only from measured behavior; do not raise production limits based on HTTP connection counts. Production load generation and infrastructure changes require a concrete rollout review, not a speculative stress run.

## Deliberate exclusions

This upgrade does not introduce billing, paid plans, externally funded AI calls, a second server, arbitrary callback/webhook URLs, remote job input URLs, or a blanket promise to expose the 31 browser-only tools. AI/workflow users gain the same documented HTTP interface and machine-readable discovery as developers.
