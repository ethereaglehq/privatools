# PrivaTools documentation

Start with the [project README](../README.md) for setup and the
[contribution guide](../CONTRIBUTING.md) for development conventions.

| Folder or guide | Contents |
| --- | --- |
| [API usage](api/usage.md) | Authentication, fair limits, jobs, retention and rollout |
| [API starters](api/starters.md) | Download generation and integration verification |
| [Example integrations](../examples/api/README.md) | Python, JavaScript, n8n and Postman usage |
| [Browser extension](../packages/extension/README.md) | Loading the Manifest V3 pipeline extension |
| [Deployment](../deploy/README.md) | Deployment profiles, server configuration and operations |
| [Google Analytics](../deploy/analytics.md) | Analytics runbook: events, Google property settings and the visitor switch |
| [Clerk accounts](../deploy/clerk-production.md) | Clerk configuration for local development and production |
| [API host split](../deploy/api-subdomain-split.md) | The app's API traffic on the DNS-only `api.privatools.me`, pages behind Cloudflare; activation and rollback |
| [Repository scripts](../scripts/README.md) | Maintenance commands: API starters, image probe, tool guide export, review dates |
| [Security policy](../SECURITY.md) | Reporting a vulnerability, scope and response expectations |
| [Changelog](../CHANGELOG.md) | Notable changes in each release |
| [Account verification](verification/accounts/) | Account settings and webhook validation evidence |
| [API verification](verification/api/) | API capacity, migration and integration evidence |
| [GEO runbook](seo/geo-runbook.md) | Search and AI-answer visibility steps that need an external account |
| [Engineering plans](superpowers/plans/) | Implementation plans for maintained features |
| [Engineering specifications](superpowers/specs/) | API, storage, AI and processing contracts |
| [Frontend guide](../frontend/README.md) | UI development commands and source layout |
| [Design system](../frontend/DESIGN.md) | The current Air and Play interfaces |
| [Product decisions](../frontend/PRODUCT.md) | Current scope and constraints |
| [Browser model provenance](../frontend/public/models/README.md) | Source, checksum and licences of the background-removal model |
| [Agent notes](../CLAUDE.md) | Repository facts for coding agents: verification, accounts, deployment, analytics and the AI stack |
| [Historical snapshots](archive/) | Earlier roadmap, backend research and the 1 September 2026 GEO analysis; not current status. The [regional analytics boundary](../deploy/analytics-country-proxy.md) is historical too. |

Keep user-facing integration examples in `examples/`, executable maintenance
tools in `scripts/`, and deployable configuration beside its deployment profile
in `deploy/`. Put new validation evidence under the relevant `verification/`
subfolder. Generated local output, credentials and runtime data do not belong in
documentation or Git.
