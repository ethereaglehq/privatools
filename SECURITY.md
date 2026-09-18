# Security Policy

PrivaTools is an open-source, privacy-first file tool suite. This policy explains how to report security issues and what to expect after a report.

## Reporting a Vulnerability

Please report suspected vulnerabilities by email:

- Contact: hello@privatools.me
- Subject prefix: `[Security]`
- Public policy page: https://privatools.me/security

You can also report privately through GitHub: **Security → Report a vulnerability** on the repository ([direct link](https://github.com/ethereaglehq/privatools/security/advisories/new)).

Include enough detail for us to reproduce the issue safely:

- Affected URL, route, or package
- Browser, operating system, and approximate time of testing
- Steps to reproduce
- Impact, including whether file contents, temporary outputs, or user metadata could be exposed
- Proof-of-concept details that avoid exposing another person's data

Do not publicly disclose a vulnerability before we have had a reasonable chance to investigate and ship a fix.

## Scope

In scope:

- https://privatools.me
- https://api.privatools.me, which serves the same backend's `/api/` routes directly
- Public frontend and backend code in the PrivaTools repository
- File-processing routes, temporary-file cleanup, security headers, and browser-side privacy boundaries

Out of scope:

- Denial-of-service testing, volumetric load testing, or automated scanning that degrades service
- Social engineering, phishing, or physical attacks
- Issues in third-party services outside our control unless they create a concrete PrivaTools exposure
- Reports that rely only on missing best-practice headers without a practical exploit path

## Response Expectations

We aim to acknowledge security reports within 72 hours. Fix timing depends on severity, reproducibility, and deployment risk. High-impact issues involving file exposure, remote code execution, authentication bypass, or persistent cross-site scripting are prioritized first.

## Supported Version

The live service runs the latest signed `v*` release tag on the public repository's `main` branch; merging a fix to `main` alone does not deploy it. Security fixes ship in a new release rather than being backported to older versions.

## Safe Harbor

Good-faith research is welcome when it avoids privacy harm, data destruction, service disruption, and access to data that is not yours. If you accidentally access sensitive data while testing, stop immediately and include only the minimum evidence needed in your report.
