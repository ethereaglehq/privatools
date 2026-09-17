# PrivaTools product decisions

<!-- impeccable:product-schema 1 -->

## Current experience

PrivaTools is a web application for file-processing and developer tools. Air and
Play are the two supported visual experiences, with a persistent style choice
and independent light, dark or device appearance. Both use the same mounted tool
state and processing engines. The maintained design system is [DESIGN.md](DESIGN.md);
the experience implementation lives in `src/skins/experience/`.

## Users and workflows

Serve occasional users and developers equally. Make individual tools easy to
find and use, with batch processing, saved workflows, API documentation and
integration examples for repeated work. Keep advanced controls available
without overwhelming the main task. Derive tool counts from the registries.

The product includes tool pages, search, Pipeline, Batch, My Stuff, the local
vault, optional AI, accounts and settings, API access and supporting public
pages. Show actual personal history and preferences rather than invented
activity. Basic tools remain available without sign-in.

## Operating constraints

- Keep the product and API free, with fair limits that protect availability.
- Use the existing shared Oracle server. Avoid additional server requirements
  or unbounded processing workloads.
- Prefer browser processing where practical and clearly explain when server
  processing or an external AI provider transfers data.
- Keep local files and private credentials outside ordinary settings sync.
  Workflow definitions must not silently embed documents or secrets.
- API jobs may retain results for up to one hour, with immediate deletion
  available. Describe the real limits and expiry behavior accurately.
- Consumer accounts use Clerk; legacy local authentication is an explicit
  self-hosted option. Account settings expose supported password and passkey
  controls. Provider availability and quotas must remain truthful.
- Preserve optional on-device AI and bring-your-own-key providers, with clear
  capability, cost and data-transfer information.
- Keep the PrivaTools name and current identity. A replacement brand has not
  been selected.

## Quality requirements

Support mobile layouts, keyboard access, readable contrast and reduced motion.
Task completion and reliable results take priority over decorative effects.
Verify failure states, downloads and data handling as well as successful page
rendering. Use synthetic inputs and isolated accounts when testing mutations.
Do not invent customer counts, endorsements, certifications or performance
claims. Current code, tests and dated verification evidence are authoritative;
old redesign explorations are not implementation instructions.
