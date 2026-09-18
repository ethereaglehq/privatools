# Repository scripts

Run these commands from the repository root. Application code lives in
`backend/` and `frontend/`; these scripts support development and verification.

| Folder | Purpose |
| --- | --- |
| `api/starters/` | Build downloadable API examples and test them against synthetic responses. |
| `api/` | Measure API capacity inside an isolated candidate container. |
| `analytics/` | Inspect public Google tag configuration without executing it. |
| `dev/` | Start the backend with the pinned local virtual environment. |
| `seo/` | `check-manifest-http.py` checks generated public assets against a local HTTP server; `export-tool-guides.py` exports per-tool guide JSON from the Python content module; `merge-tool-copy.py` is a one-shot script that inserts `seoTitle`/`metaDescription` into the registries from JSON copy files — not idempotent, so only run it on a clean checkout of the registries. |

## API starter downloads

The source examples are in `examples/api/`. After editing them, rebuild the
downloads in `frontend/public/api-starters/`, then run both test suites:

```sh
python3 scripts/api/starters/build.py
python3 scripts/api/starters/build.py --check
python3 scripts/api/starters/test.py
node --test scripts/api/starters/artifacts.test.mjs
```

The Python tests start a temporary loopback HTTP server and use synthetic data.
They do not call the production API. `api/capacity.py` is an opt-in benchmark for
an isolated candidate container with its own database. Use `--help` for its
requirements; do not run it against production or a shared account database.

## Local development

```sh
npm run setup:backend
npm start
```

`npm start` builds the frontend and invokes `dev/local-backend.py`. For separate
development servers, use `npm run backend:dev` and `npm run frontend` in two
terminals. Local account data is stored in `data/local/` and processing files in
`temp/local/` unless explicitly overridden.

## Read-only checks

```sh
python3 scripts/analytics/check-public-google-tag.py --help
python3 scripts/seo/check-manifest-http.py --help
```

The analytics check can inspect a saved public script with `--from-file PATH`;
without that option it makes one public Google script request. It does not send
analytics events or change settings. The SEO check requires a built frontend and
a running loopback backend; choose a report path with `--output PATH`.

## Tool guide export

```sh
.venv/bin/python scripts/seo/export-tool-guides.py
.venv/bin/python scripts/seo/export-tool-guides.py --check
```

`export-tool-guides.py` writes `frontend/src/data/tool-guide/*.json` from
`backend/app/tool_content.py`; run it after editing steps or FAQ, and
`--check` in CI-style verification.

Production deployment scripts and service definitions remain in `deploy/`.

Generated local reports belong in `temp/verification/<area>/`, which is excluded
from Git. The SEO checker uses `temp/verification/seo/` by default.
