# PrivaTools frontend

React, TypeScript and Vite provide the browser application. The current Air and
Play interfaces share the same tools, state and processing engines. See
[DESIGN.md](DESIGN.md) for the design system and [PRODUCT.md](PRODUCT.md) for
current product decisions.

## Local development

From the repository root, install the pinned frontend dependencies with
`npm --prefix frontend ci`, then run `npm run frontend`. This starts Vite on
`http://127.0.0.1:5173`; API requests proxy to the local backend on port 8000.
Configure local development authentication using `.env.example`; credentials
and local environment files stay outside Git.

For the complete application on one origin, run `npm run setup:backend` once
and then `npm start` from the repository root. This builds the frontend and
starts the pinned Python backend on `http://127.0.0.1:8000`. Durable local account
state lives in `data/local/`; temporary processing files use `temp/local/`.

## Verification

Run these commands from `frontend/`:

```sh
npx tsc --noEmit -p tsconfig.app.json
npm run lint -- --max-warnings 0
npm test
npm run test:content
npm run build:check
```

Before opening a pull request, also run `npm run check:review-dates`, which
compares each tool's `lastReviewed` with `origin/main`. Run `git fetch origin`
first; see [scripts/README.md](../scripts/README.md#tool-review-dates). On a
pull request CI runs it against the PR's base branch, as a step of the required
"Frontend tests (vitest)" check.

The build prepares pinned browser model assets, regenerates the AI crawler
indexes, bundles the application and injects integrity metadata. Check generated
changes before committing. CI pins Node 26, not an npm version: regenerate
`package-lock.json` with the npm that a current CI run reports, not an older
local npm, which can prune platform-specific entries and break `npm ci`.

`npm run gen:llms` regenerates just the committed content files: the crawler
indexes, sitemap, feed and content JSON in `public/`, and
`src/data/tool-blog-links.json`. CI runs it and fails when the result differs
from what is committed, so run it after changing `src/data/` and commit the
output with the change.

## Source layout

| Path | Purpose |
| --- | --- |
| `src/skins/experience/` | Air/Play navigation, layout and appearance |
| `src/skins/daylight/` | Shared base integration for real tool components |
| `src/components/` | Reusable UI and tool interfaces |
| `src/pages/` | Application pages and tool routing |
| `src/lib/` | API, authentication, local storage, AI and processing helpers |
| `src/hooks/` | Shared state and interaction hooks |
| `src/data/` | Tool catalogues and content registries |
| `src/styles/` | Shared and generated styles |
| `src/test/` | Test setup and application tests |
| `tests/` | Playwright browser tests |
| `public/` | Static files, model assets and generated API starter downloads |
| `scripts/` | Frontend generators and build checks |

Public starter downloads are generated from `../examples/api/` by
`python3 scripts/api/starters/build.py` from the repository root. Edit their
source files rather than the generated copies.

Production never uses a local build. The Dockerfile's `frontend-build` stage
runs `npm ci` and `npm run build`, and the runtime image copies its `dist/`.
Pushing a `v*` tag builds, scans and signs that image in `release.yml`, and
the server deploys the signed image; see the
[deployment guide](../deploy/README.md).
