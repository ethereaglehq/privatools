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
npm test
npm run test:content
npm run build:check
```

The build prepares pinned browser model assets, regenerates the AI crawler
indexes, bundles the application and injects integrity metadata. Check generated
changes before committing. Use the npm version pinned in CI when regenerating
`package-lock.json`.

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
source files rather than the generated copies. Deployment uses the repository's
[deployment workflow](../deploy/README.md).
