# PrivaTools release preparation

**Prepared for review on September 14, 2026. Nothing in this runbook has been deployed.** The current workspace contains uncommitted implementation work. No release commit, tag or image digest has been selected or pushed. These commands describe a future approved release; reading this document is not authorization to execute the publication steps.

## Destination established from repository evidence

| Item | Source configuration | Verification limit |
| --- | --- | --- |
| Repository | `https://github.com/ethereaglehq/privatools.git` | Local `git remote` matches. No remote settings changed. |
| Application origin | `https://privatools.me`; `www` redirects to apex | Oracle nginx source. Current installed config was not read. |
| Optional direct API origin | `https://api.privatools.me` | Enabled only with `PUBLIC_API_BASE_URL`; preserve the operator's existing choice. |
| Host | Oracle VM `140.245.15.140`, user `ubuntu` | Address documented in existing deployment files, not a new provisioning target or a live host inspection. |
| Checkout / service | `/home/ubuntu/privatools`, Docker Compose service `privatools` | `deploy/oracle-vm/privatools-auto-deploy.service`, root Compose. |
| Artifact | `ghcr.io/ethereaglehq/privatools`, Linux arm64 | `.github/workflows/release.yml`; signed by this repository's release workflow. |
| Ingress | Host nginx → `127.0.0.1:8000` → FastAPI + built SPA | Compose binds only loopback. TLS is managed outside the container. |
| Durable state | Docker `app-data` volume at `/app/data` | Local identity mirror, legacy accounts and API-key records persist here. It requires backups. |
| Temporary processing | `app-temp` at `/app/temp`; small `/tmp` tmpfs | User uploads/results are temporary, not account backups. |

`deploy/deploy.sh`, `deploy/nginx.conf` and `deploy/privatool-backend.service` describe an older `/opt/privatool` systemd arrangement. **Do not install those files over the Oracle Docker deployment.** The previous README mixed these layouts, included `.com` certificate instructions, and incorrectly described the app as stateless. The Oracle files above are the release path being prepared.

## What this preparation fixes

- The release's reusable test workflow now checks the actual app TypeScript project, zero-warning lint, generated-content tests and component tests. The duplicate unlocked Python 3.11 and nonblocking/uninstalled Playwright jobs were removed from `ci.yml`; they were not reliable evidence. Existing isolated browser audit reports remain separate from CI.
- Docker excludes local environments, databases, backups and audit evidence from its build context. The image build asserts FFmpeg subtitle-filter, H.264 and AAC support, alongside existing native dependencies. The frontend build verifies U²-Net-P by SHA-256 and stages it with the CPU ONNX Runtime WASM/bootstrap on the same origin; the backend cache links to the same weights instead of downloading a second copy. Base digests and Python hashes stay pinned; package repositories/model-download availability still affect whether a new build succeeds.
- The deploy timer defaults to release tags only. A missing cosign binary, bad signature or absent digest prevents deployment. Verification and execution use the same immutable digest, and the image revision must match the selected tag's commit. An explicit legacy `DEPLOY_MODE=auto` or `branch` remains an operator override, not the default.
- Rollback retains the previous immutable image ID and its build SHA. The script no longer prunes the rollback image before readiness succeeds. Automatic rollback restores the image with the **current** Compose configuration and existing database; it does not undo configuration/schema changes. Those require the manual procedure below.
- Manual and automated release health gates use `/readyz`, not the liveness-only `/api/health`.
- Oracle nginx restores visitor addresses only from the 22 verified Cloudflare networks. Country decisions still use the original socket peer and only the sanitized policy endpoint header; the direct API host remains unknown. See [country trust boundary](analytics-country-proxy.md).

## Review gates before any publication

| Gate | What must be recorded | Current preparation status |
| --- | --- | --- |
| Exact candidate | Reviewed full commit SHA, release tag and immutable image digest; app and content diffs reviewed | Pending. No commit/tag/push performed. |
| Source checks | Final frontend/backend suites, app typecheck, lint, content generation, bundle/SRI checks | Record results privately for the exact release revision. |
| Container | Successful no-push candidate build and functional outputs using the Linux image, including subtitle burn-in | Docker/Podman unavailable locally. Build-time capability assertion is prepared, not an executed image result. |
| Host validation | Compose model, installed nginx syntax/real-IP module, disk/memory, TLS files, running build/image, timer state | Not inspected on the VM. No SSH or live mutation performed. |
| Auth | Matching production public key at build/runtime, enabled providers, real HTTPS login, passkey and recovery tests | Configuration instructions prepared; production end-to-end behavior is not verified. |
| Google OAuth | Production configuration and real hosted provider sign-in | Verified on September 14: hosted Google login completed and the production Clerk user shows a verified, linked Google identity. The callback still uses the older deployed website; new release key/account/API integration remains pending. |
| Clerk deletion | Signed `user.deleted` webhook delivery removes local API access | Handler/tests exist; live delivery and production secret configuration remain unverified. |
| Analytics | Reviewed remote tag settings, correct authorized account, intercepted fresh-browser validation | Root reports site-search/form/download/history automation and automatic user-data detection disabled. Scroll/outbound/video remain enabled by user choice. Browser collection stays off pending verification. |
| Regional analytics | Installed proxy trust boundary and explicit reviewed positive country list | Default trust false/list empty. Unknown regions require opt-in. |
| Edge discovery | Served robots, sitemap, redirects and cache rules match reviewed intent | Previous public robots included Cloudflare-managed directives. Local files cannot change that dashboard policy. |
| Backup / rollback | Consistent DB backup and restore rehearsal; old image/config retained | Backup script exists; no live backup/restore or off-host copy verified in this task. |

Google/Clerk/GA and DNS settings are outside the image. A clean build does not activate or prove them. This deployment-preparation task did not access Google accounts or browser profiles. Root coordinates the separately authorized account setup and reports its current verification state.

## Expected configuration — names, never secrets

Use [the Oracle Compose template](oracle-vm/.env.example) for `/home/ubuntu/privatools/.env`, protected with mode `0600`. Compose substitutes only variables referenced in `docker-compose.yml`; it does not pass every key in `.env` to the container. Do not print `docker compose config` or `docker inspect .Config.Env` into shared reports. `docker compose config --quiet` validates without printing resolved values. [Docker documentation](https://docs.docker.com/reference/cli/docker/compose/config/)

| Name | Where | Required relationship / safe setting |
| --- | --- | --- |
| `CLERK_PUBLISHABLE_KEY` | GitHub repository variable and Compose runtime | Same `pk_live_…` instance, correct production domain. Public key only; never a secret build argument. |
| `CLERK_SOCIAL_PROVIDERS` | GitHub repository variable | Workflow defaults `google,github` after verified production Google sign-in. An explicit repository variable still overrides this default; review it before release. |
| `VITE_CLERK_SOCIAL_PROVIDERS` | Local Docker build argument via Compose | Defaults to `google,github`; an explicit Compose/build value still wins. Does not modify an already-built image. |
| `VITE_AUTH_PROVIDER` | Build | `clerk` for this consumer deployment. Missing key shows unavailable accounts; it does not silently create native accounts. |
| `VITE_CLERK_USERNAME_ENABLED`, `VITE_CLERK_PASSKEYS_ENABLED` | Build | Match enabled Clerk instance features; workflow currently enables both. |
| `CLERK_WEBHOOK_SECRET` | Runtime only | Signed deletion endpoint `https://privatools.me/api/clerk/webhook`; subscribe to `user.deleted`. |
| `PUBLIC_API_BASE_URL` | Runtime | Preserve current approved value. Empty means same-origin; split origin requires its DNS/TLS/CORS checks. |
| `GA4_MEASUREMENT_ID` | Runtime | Preserve the existing public measurement ID; no new property/ID was created. |
| `GA_BROWSER_TAG_ENABLED` | Runtime | `false` until the user-selected Google measurement settings and automatic user-data detection safeguards are verified. Follow the current analytics runbook; do not disable the three explicitly retained features. |
| `GA_TRUSTED_COUNTRY_HEADER` | Runtime | `false` until the exact installed nginx boundary is tested. |
| `GA_DEFAULT_ON_COUNTRIES` | Runtime | Empty until the operator provides an explicit reviewed positive list. No legal geography is inferred. |
| `PRIVATOOLS_IMAGE`, `GIT_SHA` | Release invocation | Verified immutable digest and matching full source SHA. Runtime `PRIVATOOLS_BUILD_SHA` is derived by Compose. |

The backend verifies Clerk with public JWKS and does not need `CLERK_SECRET_KEY`. The legacy GA Measurement Protocol compatibility endpoint may still read `GA4_API_SECRET` for cached older clients; it is not needed to enable the new browser tag and must never appear in frontend variables. See [Clerk setup](clerk-production.md) and [analytics switches and verification](analytics.md).

## Read-only preflight

This is safe to run during review:

```bash
python3 deploy/release-preflight.py
```

On the existing host, after read-only host access is authorized:

```bash
cd /home/ubuntu/privatools
python3 deploy/release-preflight.py --host
```

The report never prints environment values and never fetches, builds, pulls, deploys or reloads. Its exit status flags executed-check failures; `releaseReady: false` is deliberate because the script cannot approve publication or attest to external account configuration. `nginx -t` may need operator privileges to read private TLS files. Check the installed nginx includes `--with-http_realip_module`; do not replace `$realip_remote_addr` with a visitor-controlled header if it does not. The backend and proxy must both use the new country contract before the trust switch is enabled.

Before release, privately record the actual installed Compose project name, current container/image SHA, latest good DB backup, nginx configuration and timer state. Check at least 4 GB container memory plus host headroom, enough disk for **both** old/new images and uploads, and valid apex/API certificates. The two-worker native stack and native codec capabilities need an actual Linux-image smoke check; `/readyz` alone does not test every converter or browser model.

## Future approved release sequence

1. Review the source diff and root's final test report. Choose one exact commit/tag. A tag push triggers the release workflow and may be picked up by the existing VM timer; **do not push a tag merely to preview a build**. The workflow itself pushes/signs an image and publishes a GitHub Release. Its image CVE scan is report-only, so inspect that report separately.
2. Confirm the existing auto-deploy timer is stopped and no deployment service is running before a coordinated manual release. Do not run `install-auto-deploy.sh` during preparation: it enables the timer **and immediately starts deployment**. Updating the checked-out script alone does not update `/usr/local/bin/privatools-auto-deploy`; the installed copy/service must be reviewed and installed deliberately after approval.
3. Make a consistent account DB snapshot with `oracle-vm/backup-app-data.sh` and verify it, retain an encrypted off-host copy, and retain the previous image plus protected copies of Compose, `.env`, nginx and installed service/script. Do not back up transient uploads as account state. See rollback below.
4. Run the reviewed CI checks and a no-push image build first. For the approved publication, create the release artifact via the existing workflow. Record its digest and full revision, verify cosign with the repository's tag-workflow identity and GitHub OIDC issuer, then deploy that same digest. Signature verification binds the artifact to an allowed identity, not merely a mutable image label. [Sigstore documentation](https://docs.sigstore.dev/cosign/verifying/verify/)
5. Validate and install the reviewed Oracle nginx file with a rollback copy. `nginx -t` must pass before reloading. Maintain apex/API certificates and the existing API split. Never install the legacy `.com` config. Compare edge robots behavior and bypass caching for `/api/*`; `/api/analytics/policy` must remain `private, no-store` on both hosts. Preserve direct API unknown-region behavior.
6. Use the approved digest and SHA for `docker compose up -d --no-build --pull never`. The auto-deploy script performs those steps for tagged releases after signature verification. Wait for `/readyz` to return the expected SHA and inspect normal error rates. Compose recreation preserves named volumes; do not use `down -v`. [Docker documentation](https://docs.docker.com/reference/cli/docker/compose/up/)
7. Verify public home plus Air/Play/theme transitions, one real PDF/image/media output, pipeline/batch output, new blog and comparison deep links, canonical/404/noindex behavior, search/Markdown handoff, service-worker update and offline browser tool. Check anonymous tools and signed-in API-key controls separately. The hosted production Google flow has been verified. The new release must still verify its production key/account/API wiring, passkey enrollment/sign-in, recovery email and deletion webhook with explicit real account/device actions.
8. Enable only independently verified integrations. Retain disabled analytics until approved; release defaults now expose the verified Google and GitHub providers. Explicit provider overrides remain respected. Once regional analytics is deliberately configured, test direct spoofed country headers, unknown country, GPC/DNT, saved opt-out, and shared-cache isolation before exposing default-on behavior. No raw country should be returned to the browser.
9. Re-enable the tag-only timer only after the deployment is accepted and its installed script/settings match the reviewed files. Preserve the prior image until the release is accepted; schedule bounded image cleanup separately. Submit discovery changes only after the actual public URLs return their intended status/content. Existing auto-deploy includes a best-effort IndexNow request after success, not a ranking or indexing guarantee.

## Rollback and state preservation

For a code-only failure, stop the timer first, select the **recorded** old image ID/digest and old full source SHA, and restore them with the same Compose project name. Do not run the old manual `deploy.sh` as a rollback tool: it pulls main and rebuilds.

```bash
# Future authorized rollback. Fill only from the recorded pre-release values.
cd /home/ubuntu/privatools
PRIVATOOLS_IMAGE="$RELEASE_PREVIOUS_IMAGE" GIT_SHA="$RELEASE_PREVIOUS_SHA" \
  docker compose up -d --no-build --pull never
curl --fail --silent http://127.0.0.1:8000/readyz
```

Confirm the returned `build_sha` equals the recorded old SHA. The automatic script also marks a failed new SHA so it does not redeploy it every minute. Keep that marker until a fixed release or an explicit reviewed retry. An image rollback is not a database rollback: if a change modifies schema or configuration, restore the reviewed old Compose/configuration separately and check compatibility first. Do not overwrite a newer database casually; records created since the snapshot would be lost.

The backup script uses SQLite `VACUUM INTO` for a consistent snapshot and verifies the `users` table. Rehearse restoring a copied snapshot into an **isolated** empty data volume, run SQLite integrity checks, and check account/API-key behavior with synthetic data before trusting it. A same-VM backup is not disaster recovery. A production restore requires a maintenance window, stopped writers, a current emergency backup, correct appuser ownership, and intentional preservation/removal of matching WAL/SHM files; do not copy a live WAL-mode database with plain `cp`.

For nginx failure, restore the recorded old config, validate with `nginx -t`, then reload. If regional analytics trust cannot be verified, set `GA_TRUSTED_COUNTRY_HEADER=false` and leave the country list empty. If the browser tag configuration is uncertain, keep `GA_BROWSER_TAG_ENABLED=false`. Do not change DNS merely to roll back the app; the [API split runbook](api-subdomain-split.md) explains the upload-cap implications of reverting that separate setting.

## Local evidence and remaining work

- `python3 deploy/release-preflight.py`: source/shell checks and explicit missing native tools.
- `backend/tests/test_release_deploy_contract.py`: inert command-double executions of tag, signature, digest and rollback paths; no network/Docker commands are executed by these tests.
- `backend/tests/test_nginx_country_boundary.py`: source-level proxy/header/CIDR checks, including visitor-IP restoration and original-peer preservation; not native nginx validation.
- Keep deployment, browser, provider and account-specific evidence privately with the release record.

Deployment remains **prepared, not published** until a release candidate, host/native image checks, rollback evidence and final approval are recorded. Verified hosted OAuth and remaining new-release auth, analytics, webhook and edge-policy steps remain individually visible; they are not hidden behind a generic “all done” status.
