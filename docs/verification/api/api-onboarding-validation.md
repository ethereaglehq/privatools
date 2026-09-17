# API onboarding validation

Implementation covers the playground, downloadable integration recipes, and account usage/activity on the existing infrastructure. Release deployment is tracked separately once the signed candidate is available.

## Verified locally

- Backend suite: 1,310 passed, 40 skipped before the final upgrade test; the new 20-test activity subset also passes. New activity coverage includes session/key isolation, privacy, caps, UTC retention, deletion cascades, stream completion and telemetry lock/outage behavior.
- Frontend suite: 863 passed, including the final dashboard regressions; the account/client subset has 28 passing tests. TypeScript, ESLint with zero warnings, content checks, production build and bundle limits passed; final combined counts are recorded with release evidence.
- Full local HTTP server: 43 checks passed. Both Python and Node starters completed merge, compress, and PDF text extraction with real output validation and deletion after save. Polling/download/deletion did not add request-history rows or consume units. Synthetic accounts, jobs, and files were removed.
- Browser: actual sample merge/compress/text requests, download files, observed quota changes, clear-key behavior, and signed-in account activity succeeded. Air/Play and light/dark layouts at 1,440px and 390px had no page overflow. Tests used temporary synthetic credentials with external requests blocked.
- Independent reviews covered backend history, frontend stale-account/credential handling, and starter lifecycle/recovery. Scoped re-review confirmed fixes for slow-drip deadlines and malformed-response credential reflection. Starter checks passed 47 real CLI scenarios across 11 tests, 10 artifact/workflow checks, and the official Postman v2.1 schema.

## Oracle measurements

The benchmark ran inside a separate container using signed v2.3.1, separate synthetic data/temp volumes, and the production limit of 4 GiB / 1.8 CPU. No production credentials, user documents, quota changes, or new services were used. The container and its volumes were removed after measurement; production readiness remained healthy.

Two keys produced bursts of 1, 3, and 6 simultaneous requests with a six-second interval between bursts. The final run issued 60 requests across two repetitions per case. All returned validated outputs. Peak cgroup memory was 601,612,288 bytes (approximately 574 MiB); no OOM event was reported.

| Fixture | Size | 1 concurrent, p95 | 3 concurrent, p95 | 6 concurrent, p95 |
| --- | --- | --- | --- | --- |
| Merge two two-page text PDFs | 1,190 bytes each | 49 ms | 86 ms | 161 ms |
| Extract text from 40 pages | 13,882 bytes | 73 ms | 150 ms | 358 ms |
| Compress 20 distinct image pages | 5,843,023 bytes | 681 ms | 1,420 ms | 2,869 ms |

These are synthetic fixture measurements, not a throughput guarantee or an estimate for every operation. Samples per cell are small; p95 is close to the maximum observation. Keep the existing fair limits. OCR, Office, video, and large pathological documents need their own cost/capacity evaluation before expanding background adapters or advertising higher throughput.

The finite harness is `scripts/api/capacity.py`. It requires `PRIVATOOLS_CAPACITY_SANDBOX=1`, an isolated container's own database, and a loopback API; it creates and removes its own account. Never point it at production. Detailed measurements are in `api-onboarding-capacity.json`; local API and browser checks are in the neighboring JSON reports.
