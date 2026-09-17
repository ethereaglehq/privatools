# PrivaTools documentation

Start with the [project README](../README.md) for setup and the
[contribution guide](../CONTRIBUTING.md) for development conventions.

| Folder or guide | Contents |
| --- | --- |
| [API usage](api/usage.md) | Authentication, fair limits, jobs, retention and rollout |
| [API starters](api/starters.md) | Download generation and integration verification |
| [Example integrations](../examples/api/README.md) | Python, JavaScript, n8n and Postman usage |
| [Deployment](../deploy/README.md) | Deployment profiles, server configuration and operations |
| [Account verification](verification/accounts/) | Account settings and webhook validation evidence |
| [API verification](verification/api/) | API capacity, migration and integration evidence |
| [SEO](seo/) | Search analysis and the [GEO runbook](seo/geo-runbook.md) |
| [Engineering plans](superpowers/plans/) | Implementation plans for maintained features |
| [Engineering specifications](superpowers/specs/) | API, storage, AI and processing contracts |
| [Frontend guide](../frontend/README.md) | UI development commands and source layout |
| [Design system](../frontend/DESIGN.md) | The current Air and Play interfaces |
| [Product decisions](../frontend/PRODUCT.md) | Current scope and constraints |
| [Historical snapshots](archive/) | Earlier roadmap and backend research; not current status |

Keep user-facing integration examples in `examples/`, executable maintenance
tools in `scripts/`, and deployable configuration beside its deployment profile
in `deploy/`. Put new validation evidence under the relevant `verification/`
subfolder. Generated local output, credentials and runtime data do not belong in
documentation or Git.
