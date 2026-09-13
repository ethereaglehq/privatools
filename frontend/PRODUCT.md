# Product

<!-- impeccable:product-schema 1 -->

## Current Design Decision — 13 September 2026

The user selected two experiences and authorized the full application build: **Air**, with Morning Mist light and Graphite dark, and **Play**, with Blush light and Charcoal dark. Keep both behind a persistent style toggle, with a separate light/dark/device appearance choice. The experiences have distinct navigation, layouts, typography and motion, while retaining the same mounted tool state and processing engines. This decision supersedes the earlier rejected designs and Home A/Home C approvals.

Production source lives in `src/skins/experience/`; its integration uses the existing stable application and real feature extensions. Reference studies and verification are in `../docs/design-directions/2026-09-13/`. The requested scope includes all tool pages, Pipeline, Batch, My Stuff, Vault, AI, sign-in/sign-up, account settings, API, trust/status/support/about/privacy/terms and PWA support. Deployment remains separate.

## Platform

web

## Users

Casual users, working professionals, developers, and teams. People need to finish file and utility tasks quickly, obtain dependable outputs, and repeat work through batches or saved workflows. Advanced controls should be available without overwhelming occasional users.

## Product Purpose

An accessible collection of useful file-processing and developer tools. The requested improvement prioritizes simple workflows, reliable results, and powerful repeatable work. Useful capabilities should survive consolidation of overlapping interfaces and navigation.

## Operating Context

The existing application includes public tool pages, discovery and search, workflows, My Stuff, a local vault, optional AI, accounts, API access, documentation, and supporting public pages. Its audited catalogue contains 221 tools; the source catalogue, not this snapshot, remains the authority for future counts.

People use desktop and mobile browsers. The initial language and market scope is global English.

## Capabilities and Constraints

- The product remains free to users, without advertising or paid tiers. Owner funding and voluntary donations are acceptable. Infrastructure still has a cost.
- Retain the current small-server operating budget; avoid an architecture that depends on paid SaaS services or unbounded background workloads.
- Prefer browser processing where practical. If a tool needs server processing, disclose this before transfer and use accurate retention and privacy language.
- “Files stay on-device” means no cloud document library or document synchronization. It does not authorize an undisclosed upload or eliminate the explicitly accepted server-processing fallback.
- Synchronization is limited to settings, favorites, workflows, and team configuration. Workflow definitions must not silently embed document contents or credentials.
- Teams should support membership, roles, shared workflows, and managed API access. Collaborative cloud document editing and file storage are outside this approved scope.
- Retain optional on-device AI and optional bring-your-own-key providers. Actual provider charges, capability limits, and data transfers must be disclosed accurately.
- Support as many practical sign-in methods as can operate without paid authentication services. Provider requirements and quotas need verification; “free” is not a promise of unlimited external service capacity.
- Follow the device color theme, with a remembered manual override.
- The requested review includes every page and material state, tools and outputs, security, OAuth, API access, secret handling, My Stuff, vault behavior, performance, accessibility, SEO, answer-engine readiness, and AI-search readiness.
- Use local automated verification plus a separate staging environment for live OAuth, account, API, and deployment-flow checks.
- Remove proven stale or duplicate code and consolidate obsolete deployment paths; archive useful historical documentation. Present broader removal candidates for review first. Pre-existing untracked user materials are not evidence of staleness.
- The user reviewed the plan and consumer mockups and explicitly authorized the build on 7 September 2026: “okay i liked what you have shown me build it … dont miss any features we already ahve.” Continue the approved implementation and review completed phases. Deployment remains a separate decision.

## Brand Commitments

The current product is PrivaTools. The user is open to a new name and identity. No replacement name or ownership/trademark claim has been approved. Keep PrivaTools. The approved visual directions are Air and Play, as recorded above. Earlier compositions remain historical references only.

On 7 September 2026 the user named Coinbase and Robinhood as products they love and asked for a consumer-friendly experience. Both their public websites and their everyday apps matter equally. Use them as references for craft, approachability, hierarchy, and interaction; a specific copied palette, font, or layout has not been requested. Sejda, iLovePDF, and https://www.ihatepdf.cv/ are the user-confirmed competitors. Competitor status is not an endorsement of every design or product choice.

The home must support all three starting paths together: prominent search and popular tools, direct file selection followed by relevant operations, and a personal area with favorites, recent tasks, and saved workflows. How those paths are composed remains a visual-design decision. Adapt the personal area to actual local history and preferences rather than inventing activity or requiring sign-in for basic tools.

## Evidence on Hand

The source code and `../docs/audits/2026-09-06/` contain the current audit, findings, route inventory, runtime evidence, and test limitations. Findings are not fixed merely because they have been documented. No customer counts, endorsements, certifications, search rankings, or real-world performance claims should be invented.

## Product Principles

1. Make the next useful action clear, while preserving depth for repeat work.
2. Earn trust through reliable outputs and visible, truthful handling of files and secrets.
3. Keep local files and private credentials outside ordinary account synchronization.
4. Provide a useful free product within a bounded operating budget.
5. Verify outcomes and failure states, not just the existence of a page or control.

## Accessibility & Inclusion

Support keyboard operation, readable contrast, mobile layouts, and reduced-motion preferences. The user wants both purposeful polish and richer expressive motion; task completion and accessibility take precedence over decorative movement.

## Open Decisions

The home composition and consumer visual identity are approved for implementation. A replacement brand name and the release process remain open. Authentication-provider rollout and detailed team permissions will be proposed with evidence before implementation.

On 7 September 2026 the user rejected all visual directions shown in this exploration, including the five additional interactive concepts. Those earlier proposals remain rejected. The later consumer mockups were approved for build; do not revive the earlier styles.
