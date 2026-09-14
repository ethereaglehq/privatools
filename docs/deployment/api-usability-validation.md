# API usability upgrade validation

Date: 2026-09-14. Branch: `codex/api-usability-upgrade`.

## Delivery scope

The API stays free and uses the existing Oracle server. The implementation adds
shared admission/accounting, a public reference for 147 operations, a v1-only
OpenAPI document, and optional durable jobs. Initial job adapters are PDF merge,
preset compression, grayscale conversion, and text extraction. Results remain
available for one hour after completion, support repeat downloads, and have an
explicit deletion endpoint.

The job supervisor runs beside two web workers in the existing container's
combined 4 GB / 1.8 CPU envelope. No new server or external queue is introduced.
`API_V1_JOBS_ENABLED` defaults to false. These changes have not been deployed.

## Automated verification

- Full backend suite: 1,291 passed, 40 skipped. On this Mac, Cairo tests required
  `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/opt/cairo/lib:/opt/homebrew/lib`.
  The CI image installs its native libraries separately.
- Full frontend suite: 834 passed, including the final job-template corrections.
- TypeScript and ESLint passed. Content-generation checks: 9 passed.
- Production frontend build, asset integrity injection, and bundle budget passed.
- Independent review covered jobs, launcher/readiness, and v1-only CORS. The
  identified retry/scratch and disabled-worker retention issues were fixed.
  Final disabled-worker cleanup/startup regressions passed independently.

The AnyIO import is now a direct dependency at the version already present in
both hash-pinned locks. No dependency versions or artifact hashes changed.

## Local end-to-end evidence

`api-usability-local-check.json` records a disposable local run using the actual
launcher, two web processes, one job supervisor, synthetic account/key, and PDF
fixtures. The run verified worker readiness, anonymous discovery, synchronous
merge, validation refunds, submit/poll/download, repeat downloads, idempotent
replay without another charge, and deletion of the actual result file.

The API page was inspected against the local server. Search, operation fields,
required job headers, HTTP limits and exemptions, and current async availability
were checked. Job templates use PDF inputs and explain idempotent retries. No
browser errors were observed. The page had no horizontal overflow at either the
default 1,280-pixel viewport or a 390-pixel mobile viewport.

## Production validation still required

The local fixture run does not measure Oracle throughput. Before enabling jobs,
validate the signed container image, worker readiness, restart/deletion/expiry,
and rollback on the existing host. Check available disk space before reserving
job storage. Measure representative workload latency, queue wait, failures,
CPU and memory before raising limits or publishing throughput guarantees.

Synchronous processing defaults to three admitted requests per key, six across
web workers, and a 30/minute token bucket with burst six. Job execution is one
at a time with separate outstanding/storage limits. Admitted HTTP counts do not
guarantee that an arbitrary native thread stops when a client disconnects.
