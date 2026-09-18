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
| Ingress | Host nginx → upstream `privatools_app` → `127.0.0.1:8000` → FastAPI + built SPA | Compose binds only loopback. TLS is managed outside the container. During a deploy the upstream briefly names `127.0.0.1:8001` ([zero-downtime deploys](#zero-downtime-deploys)). |
| Durable state | Docker `app-data` volume at `/app/data` | Local identity mirror, legacy accounts and API-key records persist here. It requires backups. |
| Temporary processing | `app-temp` at `/app/temp`; small `/tmp` tmpfs | User uploads/results are temporary, not account backups. |

`deploy/deploy.sh`, `deploy/nginx.conf` and `deploy/privatool-backend.service` describe an older `/opt/privatool` systemd arrangement. **Do not install those files over the Oracle Docker deployment.** The previous README mixed these layouts, included `.com` certificate instructions, and incorrectly described the app as stateless. The Oracle files above are the release path being prepared.

## What this preparation fixes

- The release's reusable test workflow now checks the actual app TypeScript project, zero-warning lint, generated-content tests and component tests. The duplicate unlocked Python 3.11 and nonblocking/uninstalled Playwright jobs were removed from `ci.yml`; they were not reliable evidence. Existing isolated browser audit reports remain separate from CI.
- Docker excludes local environments, databases, backups and audit evidence from its build context. The image build asserts FFmpeg subtitle-filter, H.264 and AAC support, alongside existing native dependencies. The frontend build verifies U²-Net-P by SHA-256 and stages it with the CPU ONNX Runtime WASM/bootstrap on the same origin; the backend cache links to the same weights instead of downloading a second copy. Base digests and Python hashes stay pinned; package repositories/model-download availability still affect whether a new build succeeds.
- The deploy timer defaults to release tags only. A missing cosign binary, bad signature or absent digest prevents deployment. Verification and execution use the same immutable digest, and the image revision must match the selected tag's commit. An explicit legacy `DEPLOY_MODE=auto` or `branch` remains an operator override, not the default.
- Rollback retains the previous immutable image ID and its build SHA (`.privatools-deploy.previous` in the checkout). Nothing prunes images. Since 18 September a release that fails never replaces the running one, so no automatic rollback is needed; `privatools-rollout --rollback` restores the recorded release with the **current** Compose configuration and existing database. It does not undo configuration/schema changes. Those require the manual procedure below.
- Manual and automated release health gates use `/readyz`, not the liveness-only `/api/health`, plus a real-page probe before any traffic moves.
- Oracle nginx restores visitor addresses only from the 22 verified Cloudflare networks. Country decisions still use the original socket peer and only the sanitized policy endpoint header; the direct API host remains unknown. See [country trust boundary](analytics-country-proxy.md).

## Zero-downtime deploys

Added 18 September 2026. Until then `auto-deploy.sh` replaced the running container with `docker compose up` and only afterwards waited for `/readyz`. A release that failed to start took the site offline until the rollback finished, and even a good release left a gap while the new container booted. The manual `deploy.sh` never rolled back at all.

Now `privatools-rollout` ([`oracle-vm/rollout.sh`](oracle-vm/rollout.sh)) replaces the release and nothing ever stops before its successor serves. `auto-deploy.sh` still chooses the release and verifies the tag, cosign signature, digest and revision, then hands the verified digest to the rollout.

1. **Candidate.** Start the new image as a second compose project, `privatools-interim`, on `127.0.0.1:8001`, with the same compose file and the live container's two volumes ([`compose.interim.yml`](oracle-vm/compose.interim.yml)). Wait up to 180 s for `/readyz` to report the new build (a crash loop is caught early). Then run the real-page probe, `scripts/ci/probe-image.py --running`: the same checks CI runs on a freshly booted image, namely readiness, a real 404, the homepage's advertised tool count, two server-rendered tool pages and the sitemap. On any failure, remove the interim and exit 1. The old release never stopped serving.
2. **Switch.** Tell the old container's job supervisor to finish its current job and hand the queue over (SIGUSR1). Point host nginx at 8001 through the root helper (`nginx -t`, graceful reload). Check through nginx that `https://privatools.me/readyz` reports the new build; if not, switch back and reject.
3. **Drain.** Keep the old container until no request has been open on it for 3 s. Also wait until the nginx worker generation that the reload retired has exited, capped at 300 s: nginx buffers a request body before it connects upstream, so an upload that began before the switch still reaches the old container afterwards. Then wait until its job supervisor has released the queue, capped at 360 s: one job may run for up to 300 s.
4. **Steady state.** Recreate `privatools-privatools-1` on 8000 with the new image (Compose stops the drained old container). Gate it on readiness and the page probe again, drain the interim's supervisor and switch nginx back to 8000. Then drain the interim like step 3 and remove it.

If step 4 cannot bring the canonical container up (retried once), the interim keeps serving the new release: exit 3, "degraded", with a ping to `DEPLOY_PING_URL`. Each timer run retries after a 10-minute backoff. A run interrupted at any point is reconciled by the next one from the upstream file: an interim that nginx points at is moved back to 8000, and one it does not point at is drained and removed. The rollout refuses (exit 2, nothing started) when the nginx switch is not installed, the site does not proxy through it, port 8001 is taken, or less than 1536 MB of memory is available. It never falls back to a stop-and-start deploy.

### Why it is built this way

**The steady state does not change.** The installed backup script (`CONTAINER=privatools-privatools-1`), the rollback commands, the CI image probe, the unit's `HEALTH_URL` and every operator habit address the canonical container on 127.0.0.1:8000. Blue/green slots that alternate would move the live container between names and ports on every deploy. The first deploy that landed on the other slot would silently break the untouched backup timer. Passing traffic through a temporary interim costs a second boot of the new image (about 10 s here) and a second nginx reload, and keeps every one of those contracts.

**Shared state during the overlap.** Both containers mount the same `app-data` and `app-temp` volumes for about a minute.

- *Accounts, API keys, quotas, admission leases and the job queue* are one SQLite database in WAL mode (`backend/app/store.py`). Two containers on one host share the kernel, the file's inode, its POSIX locks and its `-shm` mapping. SQLite's multi-process rules therefore hold exactly as they already do between the two uvicorn workers and the job supervisor inside one container. That would not be true on a network filesystem, which this is not.
- *Migrations* run in `store.init()` when the new container starts, while the old one still serves. The old code must work on the new schema, as it already must for any rollback. Keep migrations additive. Never add a column to a table written with a positional `INSERT ... VALUES`: `api_async_worker`, `api_async_ingest`, `api_async_submit_window`, `api_v1_leases`, `api_v1_rate_buckets`.
- *Temporary files* are safe to share. The janitor deletes only files older than ten minutes and nothing wipes `app-temp` at startup, so a second container is no different from a second worker.
- *Per-process state* doesn't need a handover. The website's per-IP limits are in memory per worker, so a client can briefly get a second allowance during the overlap. API admission leases identify their owner by PID and start time. A container cannot see the other's PIDs, so it treats their leases as dead only once expired, and a live request renews its lease. That is what already happens after every restart.
- *Async jobs, which production runs* (its public `/readyz` lists `api_job_worker`). The supervisor's singleton is an `flock` on `app-data/jobs/worker.lock`, which is shared across containers because it is the same inode on one kernel. Before this change, a second container's supervisor gave up after 30 s and exited, and the launcher then stopped that whole container. Its `/readyz` also failed, because the heartbeat row named the old build. A naive overlap could never pass the gate. Now a supervisor that finds the lock taken waits as a standby. `docker kill --signal SIGUSR1` (relayed by the launcher, PID 1) drains it: it finishes the job it is running, stops claiming and releases the lock. It then waits as a passive standby that retakes the lock only if nobody heartbeats for 30 s, so a failed handover heals itself; SIGUSR2 makes it eager again. Readiness counts this container's own live standby of the same build through a state file in its private `/tmp`. No job is interrupted and none runs twice, because only the lock holder claims. Jobs accepted by the old web are simply processed by the new supervisor, since the queue is durable.
- *The one exception is the first deploy after the cut-over.* Its old container runs v2.6.x, whose supervisor cannot drain. The rollout stops that container as soon as nothing is queued or running, waiting up to 60 s for that, otherwise as soon as nothing is running. A job claimed in the instant before SIGTERM is interrupted and retried once, never lost. Under a deliberately saturated job stream in the load test, that happened to one job in four of five such runs. The retry risk disappears whenever the queue goes quiet within the 60 s wait.

**Resources.** Compose caps each container at 4 GB, 1.8 CPUs and 512 PIDs. During the overlap the caps add up to more than a 2-core, 12 GB VM shared with other projects can promise, but the caps are not usage. An idle, ready instance used about 340 MiB on the dev VM. In the load test the two containers together peaked at 791 MiB during an overlap, with async jobs running. The overlap lasts under a minute, and the old container takes no new work after the switch, so the combined load is the old one's in-flight tail plus new requests. A burst of heavy conversions during a deploy could raise that, which is why the rollout refuses rather than overcommits: it needs at least `MIN_AVAILABLE_MB` (default 1536) available. CPU is shared while the new container boots, about 10 s. In the test, p99 latency rose from 63 ms before the rollouts to 183 ms during them. Production's current free memory was not verified for this change (no host access from where it was built), so the runbook checks it first.

**The nginx switch.** One upstream, `privatools_app`, is defined in `/etc/nginx/privatools-upstream.conf`, and the site includes it and proxies every location to it. The root helper [`nginx-upstream.sh`](oracle-vm/nginx-upstream.sh) (installed as `/usr/local/sbin/privatools-nginx-upstream`) writes the file beside the old one and renames it over it. It runs `nginx -t` on the whole configuration, then `systemctl reload nginx`. On any failure it puts the previous file back, so the file always matches what nginx runs. The upstream has a single server and no keepalive, exactly like the `proxy_pass http://127.0.0.1:8000` it replaces: nginx never marks a lone server down, and each request has its own upstream connection, which is what draining counts. A backup server would be worse. After one slow request timed out, nginx would send all traffic to an empty port for `fail_timeout`.

**Privileges.** The deploy service stays `User=ubuntu` with the docker group. Its only root step is `sudo -n /usr/local/sbin/privatools-nginx-upstream set 8000|8001`, allowed by [`/etc/sudoers.d/privatools-deploy`](oracle-vm/privatools-deploy.sudoers) for exactly those two argument lists. The helper validates the port, ignores its environment as root and writes one fixed file. The drain and resume signals and the containers go through the docker group like every other deploy action. The unit must not set `NoNewPrivileges`, or sudo stops working and every deploy refuses at the switch while the previous release keeps serving.

**Cut-over.** The timer runs the installed copies in `/usr/local/bin`, not the checkout, and a deploy resets the checkout but never reinstalls them. It does use the checkout's `docker-compose.yml` at the target tag. The compose change is therefore backward compatible: the host port defaults to 8000 and the service is unchanged, so the old installed script deploys a release that contains this change exactly as before, gap included. The new scripts refuse to run (exit 2) until the nginx site routes through the upstream, so installing in the wrong order changes nothing. The runbook below installs from the release's own files, then runs the first zero-downtime deploy by hand.

### Load test on the dev VM

Run on 18 September 2026 on the shared 2-core ARM dev VM (not production), with other projects' containers running. Every row uses the final scripts in this change.

**Setup.** The image was built once from this branch. Each "release" is a throwaway image `FROM` that build:

- A good release changes only a label.
- The release that never becomes ready appends `raise RuntimeError(...)` to `main.py`. Uvicorn keeps respawning its workers, so it never answers and never exits.
- The release that is ready but broken deletes `frontend/dist/index.html`, so `/readyz` passes while `/` and tool pages return 404.
- The pre-handover release copies main's four job, launcher and storage files back in, which is what v2.6.1 runs.

The canonical and interim projects ran from this checkout's `docker-compose.yml` on 127.0.0.1:8016 and 8017, because another application owns 8000 on that VM. The nginx stand-in was `nginx:alpine` in a host-network container on 127.0.0.1:8015, with production's proxying: the included upstream file, `Host $host`, and the `/api/` limits and timeouts. The switch ran the real `nginx-upstream.sh` through its unprivileged testing hook, with `nginx -t` and the reload executed in that container. Async jobs were enabled as in production. `READY_TIMEOUT` was 120 s (production default 180 s).

**Load and pass criteria.** Through nginx, `GET /` and `GET /readyz` each every 100 ms, a fresh connection per request. A request failed on any transport error or timeout, a non-200 status, a page without `<div id="root">`, or a `/readyz` that was not `ready`. At the same time an API client kept async `compress` jobs flowing through nginx, keeping up to two outstanding, and then audited every accepted job's final state and attempt count.

| Scenario | Rollout | Page + `/readyz` requests | Failed | Jobs: first attempt / accepted |
| --- | --- | --- | --- | --- |
| (a) Good release (image changes) | exit 0, 62 s | 1464 | **0** | 14 / 14 |
| (b) Release that never becomes ready | exit 1 after the readiness deadline, 129 s | 2796 | **0** | 28 / 28 |
| (c) Ready release that fails the page probe | exit 1, 8 s | 386 | **0** | 5 / 5 |
| `privatools-rollout --rollback` | exit 0, 38 s | 976 | **0** | 12 / 12 |
| nginx switch fails (`nginx -t` rejects) | exit 1, 21 s | 626 | **0** | 8 / 8 |
| Rollout SIGKILLed right after its switch, then rerun | second run exit 0, 41 s | 1720 | **0** | 19 / 19 |
| First deploy after the cut-over (old container runs the pre-handover supervisor) | exit 0, 52 s | 1250 | **0** | 13 / 13 |

- **Build SHA.** In every run `/readyz` through nginx reported the old build until the switch and the new one after it. The rejected releases never appeared.
- **Latency.** In the seconds before each rollout started: p50 7 ms, p99 63 ms. During the rollouts: p50 12 ms, p99 183 ms. No run's p99 exceeded 250 ms on either path, and the slowest single request took 1.04 s (a `/readyz` while candidate (b) booted).
- **Timeline of (a).** The interim was ready at 8 s and passed the page probe by 14 s; the switch happened at 15 s. The old container had drained by 21 s, and its supervisor finished the job it was running and released the queue at 24 s. The new supervisor took over at 27 s. The canonical container was ready at 44 s, and traffic switched back at 49 s. The interim drained by 54 s, handed the queue on at 58 s and was removed at 62 s. In every switch the retired nginx workers had exited by the end of the 3 s quiet period.
- **Memory.** The two containers together peaked at 791 MiB during an overlap; each peaked at 491 MiB, with jobs running.
- **Refusals.** Every run also saw `429 job_queue_full`. The global 1 GiB job-storage budget reserves 250 MB per outstanding job, and it had filled with an hour of retained results from earlier runs: 752 MB in 429 results at the end, reservations equal to result sizes, no claims or ingests left over. No submission was refused with a 503 in any run.
- **Cut-over caveat.** Five cut-over runs were made while developing this, all under the same saturated job stream. Four of them interrupted and retried one job each, out of 56, 28, 54 and 14. The final run retried none. Nothing was lost in any of them. That is the documented one-time exception for the first deploy after the cut-over, and a busy queue can still produce one retry.
- **nginx 1.18.** The shipped production site with the upstream include also passed `nginx -t` on `nginx:1.18.0-alpine`, production's version, with the upstream file naming 8000 and naming 8001.

Reproduce with a stand-in of your own. Never point these at production.

### Production rollout runbook

For someone with production access. Nothing here has been run against production. The environment that built this change could not reach `ssh priva`, so the live host was inspected only through its public `/readyz`: build `b2cb85c`, async jobs enabled. Run everything on the VM as `ubuntu` in `/home/ubuntu/privatools` unless a step says otherwise. The backup timer is not touched at any point.

**0. Read-only checks. Record the output; stop if any line disagrees.**

```bash
cd /home/ubuntu/privatools
git status --short                                     # nothing
git describe --tags --exact-match HEAD                 # the deployed tag (v2.6.1 on 18 September)
curl -fsS http://127.0.0.1:8000/readyz                 # ready, that build_sha, "api_job_worker":true
docker compose version                                 # v2 or later; deploys already use --pull never
docker ps --format '{{.Names}}\t{{.Ports}}'            # privatools-privatools-1 on 127.0.0.1:8000
docker inspect privatools-privatools-1 --format \
  '{{index .Config.Labels "com.docker.compose.project"}} {{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}'
                                                       # privatools 4294967296 1800000000
grep -c '^COMPOSE_PROJECT_NAME=' .env || true          # 0 (a key-name check; prints no values)
free -m                                                # "available" comfortably above 1.5 GB
docker stats --no-stream                               # what the other projects use right now
ss -ltn | grep ':8001 ' || echo "8001 free"            # the interim port must be free
nginx -v; cat /run/nginx.pid                           # 1.18 on Ubuntu 22.04, and a PID
diff <(git show v2.6.1:deploy/oracle-vm/nginx-privatools.conf) /etc/nginx/sites-enabled/privatools \
  && echo "installed site = repository copy"
systemctl list-timers privatools-backup.timer privatools-auto-deploy.timer --no-pager
sudo -n true && echo "non-interactive sudo works"
```

If 8001 is taken, choose a free port. Change it in `rollout.sh` (`INTERIM_PORT`), `nginx-upstream.sh` (`ALLOWED_PORTS`), the sudoers file and `test_zero_downtime_rollout.py`, and release that change first. If the installed site differs from the repository copy, do not copy the new file over it in step 6. Apply the two edits to the installed file instead: add `include /etc/nginx/privatools-upstream.conf;` at the top, and change every `proxy_pass http://127.0.0.1:8000;` to `proxy_pass http://privatools_app;`.

**1. Stop automatic deploys.**

```bash
sudo systemctl stop privatools-auto-deploy.timer
systemctl is-active privatools-auto-deploy.service     # inactive
```

**2. Merge and release.** Merge the pull request; a merge to `main` ships nothing. Tag the release from `main` and wait for the release workflow to push and sign its image. With the timer stopped, the tag does not deploy yet.

**3. Take the release's deploy files without moving the checkout.**

```bash
git fetch --tags origin
rm -rf /tmp/privatools-cutover && mkdir /tmp/privatools-cutover
git archive vX.Y.Z deploy | tar -x -C /tmp/privatools-cutover
```

**4. Back up what the cut-over replaces.**

```bash
stamp=$(date +%s); mkdir -p /home/ubuntu/nginx-backups
sudo cp /etc/nginx/sites-enabled/privatools /home/ubuntu/nginx-backups/privatools.$stamp.bak
sudo cp /usr/local/bin/privatools-auto-deploy /home/ubuntu/nginx-backups/privatools-auto-deploy.$stamp.bak
sudo cp /etc/systemd/system/privatools-auto-deploy.service /home/ubuntu/nginx-backups/privatools-auto-deploy.service.$stamp.bak
```

**5. Install the scripts, the helper, the sudoers rule and the upstream file.** This changes no traffic: the upstream file names 8000 and nothing includes it yet.

```bash
sudo bash /tmp/privatools-cutover/deploy/oracle-vm/install-auto-deploy.sh   # no --start: install and validate only
cat /etc/nginx/privatools-upstream.conf                                      # server 127.0.0.1:8000;
sudo -n -l /usr/local/sbin/privatools-nginx-upstream set 8001                # prints the allowed command
```

**6. Route the site through the upstream.** This also changes no traffic: the upstream still names 8000.

```bash
sudo cp /tmp/privatools-cutover/deploy/oracle-vm/nginx-privatools.conf /etc/nginx/sites-enabled/privatools
sudo nginx -t && sudo systemctl reload nginx
curl -fsS https://privatools.me/readyz                                   # still the running build
python3 /tmp/privatools-cutover/deploy/release-preflight.py --host       # the zero-downtime checks pass
```

**7. First zero-downtime deploy, by hand and watched.** From another machine, watch the public site throughout:

```bash
while true; do printf '%s %s ' "$(date +%T)" "$(curl -s -o /dev/null -w '%{http_code}' https://privatools.me/)"
  curl -s https://privatools.me/readyz | cut -c1-70; sleep 0.5; done
```

On the VM:

```bash
sudo systemctl start --no-block privatools-auto-deploy.service
journalctl -fu privatools-auto-deploy.service
```

Expect: `cosign signature verified`, `phase 1: starting …`, `page probe passed` and `predates handover` (the v2.6.1 supervisor cannot drain). Then the switch to 8001, `drained`, `no async job running`, `phase 2`, the switch back to 8000, `done` and `deploy complete`. It takes about two to three minutes. The watch loop shows only 200s and the build SHA changes once. If the journal says `REJECTED`, the old release kept serving; read the probe lines above it. `refused` means a precondition from step 0 failed and nothing changed.

**8. Verify.**

```bash
curl -fsS http://127.0.0.1:8000/readyz                         # the new build_sha, "api_job_worker":true
docker ps --format '{{.Names}}\t{{.Ports}}'                    # privatools-privatools-1 only; no interim
cat /etc/nginx/privatools-upstream.conf                        # 127.0.0.1:8000
cat .privatools-deploy.previous                                # the v2.6.1 image ID and b2cb85c…
docker exec privatools-privatools-1 python -m backend.app.api_v1.jobs.worker --status   # local role "active"
systemctl list-timers privatools-backup.timer --no-pager       # unchanged; check tomorrow's 03:17 run in its journal
```

**9. Re-enable automatic deploys.** The timer stays enabled across a stop:

```bash
sudo systemctl start privatools-auto-deploy.timer
```

From the next tag on, deploys run through the timer with zero downtime and a draining job handover.

**Undo the cut-over** if anything above misbehaves. If the upstream names 8001, an interim container is serving, so finish or reverse that first: rerun `sudo env REPO_DIR=/home/ubuntu/privatools privatools-rollout IMAGE SHA` with the release it serves, or confirm the canonical container serves and run `sudo /usr/local/sbin/privatools-nginx-upstream set 8000`. Then:

```bash
sudo systemctl stop privatools-auto-deploy.timer
sudo cp /home/ubuntu/nginx-backups/privatools.$stamp.bak /etc/nginx/sites-enabled/privatools
sudo nginx -t && sudo systemctl reload nginx                  # proxy_pass 127.0.0.1:8000 again
sudo install -m 0755 /home/ubuntu/nginx-backups/privatools-auto-deploy.$stamp.bak /usr/local/bin/privatools-auto-deploy
sudo install -m 0644 /home/ubuntu/nginx-backups/privatools-auto-deploy.service.$stamp.bak /etc/systemd/system/privatools-auto-deploy.service
sudo rm -f /etc/sudoers.d/privatools-deploy /usr/local/sbin/privatools-nginx-upstream \
  /usr/local/bin/privatools-rollout /etc/nginx/privatools-upstream.conf
sudo systemctl daemon-reload && sudo systemctl start privatools-auto-deploy.timer
```

The containers need nothing: the steady state is the same container on the same port. The old script then deploys with its old gap again.

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
| Analytics | Reviewed remote tag settings, correct authorized account, intercepted fresh-browser validation | Root reports site-search/form/download/history automation and automatic user-data detection disabled. Scroll/outbound/video remain enabled by user choice. Browser collection is enabled in production and default-on for every visitor since 17 September 2026; the Privacy page switch is the only opt-out. |
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
2. Confirm the existing auto-deploy timer is stopped and no deployment service is running before a coordinated manual release. `install-auto-deploy.sh` installs and validates only; with `--start` it also enables the timer **and immediately starts deployment**. Updating the checked-out script alone does not update `/usr/local/bin/privatools-auto-deploy` or `/usr/local/bin/privatools-rollout`; the installed copies/service must be reviewed and installed deliberately after approval.
3. Make a consistent account DB snapshot with `oracle-vm/backup-app-data.sh` and verify it, retain an encrypted off-host copy, and retain the previous image plus protected copies of Compose, `.env`, nginx and installed service/script. Do not back up transient uploads as account state. See rollback below.
4. Run the reviewed CI checks and a no-push image build first. For the approved publication, create the release artifact via the existing workflow. Record its digest and full revision, verify cosign with the repository's tag-workflow identity and GitHub OIDC issuer, then deploy that same digest. Signature verification binds the artifact to an allowed identity, not merely a mutable image label. [Sigstore documentation](https://docs.sigstore.dev/cosign/verifying/verify/)
5. Validate and install the reviewed Oracle nginx file with a rollback copy. `nginx -t` must pass before reloading. Maintain apex/API certificates and the existing API split. Never install the legacy `.com` config. Compare edge robots behavior and bypass caching for `/api/*`; `/api/analytics/policy` must remain `private, no-store` on both hosts. Preserve direct API unknown-region behavior.
6. Use the approved digest and SHA with `privatools-rollout DIGEST SHA`. The auto-deploy script does exactly that for tagged releases after signature verification. The rollout starts the release beside the running one, gates it on `/readyz` and the real-page probe, and only then moves traffic ([zero-downtime deploys](#zero-downtime-deploys)). Inspect normal error rates afterwards. Compose recreation preserves named volumes; do not use `down -v`. [Docker documentation](https://docs.docker.com/reference/cli/docker/compose/up/)
7. Verify public home plus Air/Play/theme transitions, one real PDF/image/media output, pipeline/batch output, new blog and comparison deep links, canonical/404/noindex behavior, search/Markdown handoff, service-worker update and offline browser tool. Check anonymous tools and signed-in API-key controls separately. The hosted production Google flow has been verified. The new release must still verify its production key/account/API wiring, passkey enrollment/sign-in, recovery email and deletion webhook with explicit real account/device actions.
8. Enable only independently verified integrations. Retain disabled analytics until approved; release defaults now expose the verified Google and GitHub providers. Explicit provider overrides remain respected. Once regional analytics is deliberately configured, test direct spoofed country headers, unknown country, GPC/DNT, saved opt-out, and shared-cache isolation before exposing default-on behavior. No raw country should be returned to the browser.
9. Re-enable the tag-only timer only after the deployment is accepted and its installed script/settings match the reviewed files. Preserve the prior image until the release is accepted; schedule bounded image cleanup separately. Submit discovery changes only after the actual public URLs return their intended status/content. Existing auto-deploy includes a best-effort IndexNow request after success, not a ranking or indexing guarantee.

## Rollback and state preservation

For a code-only failure, stop the timer first, then restore the **recorded** previous release without downtime. Every successful rollout writes the release it replaced (image ID and full source SHA) to `/home/ubuntu/privatools/.privatools-deploy.previous`. Do not run the manual `deploy.sh` as a rollback tool: it pulls main and rebuilds.

```bash
# Authorized rollback between releases that both contain the drainable job
# supervisor (the zero-downtime release and later).
sudo systemctl stop privatools-auto-deploy.timer
cat /home/ubuntu/privatools/.privatools-deploy.previous        # IMAGE SHA to restore
bad_sha="$(git -C /home/ubuntu/privatools rev-parse HEAD)"      # the release being withdrawn
sudo env REPO_DIR=/home/ubuntu/privatools privatools-rollout --rollback
curl --fail --silent http://127.0.0.1:8000/readyz               # build_sha = the recorded old SHA
# Keep the timer from redeploying the withdrawn tag until a newer one exists.
echo "$bad_sha" > /home/ubuntu/privatools/.privatools-auto-deploy.failed
sudo systemctl start privatools-auto-deploy.timer
```

A release older than the drainable supervisor (v2.6.1 and earlier) cannot start beside a newer one while async jobs are enabled: its supervisor gives up on the shared lock and its `/readyz` rejects the newer heartbeat, so the rollout rejects it and nothing changes. Restore such a release with the stop-and-start form, which has the old gap of a few seconds:

```bash
# Rollback to a pre-handover release. Fill only from the recorded values.
cd /home/ubuntu/privatools
sudo env PRIVATOOLS_IMAGE="$RELEASE_PREVIOUS_IMAGE" GIT_SHA="$RELEASE_PREVIOUS_SHA" \
  docker compose up -d --no-build --pull never
curl --fail --silent http://127.0.0.1:8000/readyz
```

Confirm the returned `build_sha` equals the recorded old SHA. The automatic script marks a rejected new SHA so it does not retry it every minute. Keep that marker until a fixed release or an explicit reviewed retry. An image rollback is not a database rollback: if a change modifies schema or configuration, restore the reviewed old Compose/configuration separately and check compatibility first. Do not overwrite a newer database casually; records created since the snapshot would be lost.

The backup script uses SQLite `VACUUM INTO` for a consistent snapshot and verifies the `users` table. Rehearse restoring a copied snapshot into an **isolated** empty data volume, run SQLite integrity checks, and check account/API-key behavior with synthetic data before trusting it. A same-VM backup is not disaster recovery. A production restore requires a maintenance window, stopped writers, a current emergency backup, correct appuser ownership, and intentional preservation/removal of matching WAL/SHM files; do not copy a live WAL-mode database with plain `cp`.

For nginx failure, restore the recorded old config, validate with `nginx -t`, then reload. If the browser tag configuration is uncertain, keep `GA_BROWSER_TAG_ENABLED=false`. Do not change DNS merely to roll back the app; the [API split runbook](api-subdomain-split.md) explains the upload-cap implications of reverting that separate setting.

## Local evidence and remaining work

- `python3 deploy/release-preflight.py`: source/shell checks and explicit missing native tools. With `--host` it also checks the zero-downtime prerequisites: the upstream file, the site's `proxy_pass`, the sudo rule, a free port 8001 and enough memory.
- `backend/tests/test_release_deploy_contract.py`: inert command-double executions of the tag, signature and digest paths, and of what auto-deploy does with each rollout outcome. No network or Docker commands run in these tests.
- `backend/tests/test_zero_downtime_rollout.py`: `rollout.sh` against a simulated host. It covers the order of every switch, drain and handover; rejection of never-ready, page-broken and unswitchable releases; degraded mode and its backoff; resuming after a killed run; rollback; preconditions; and the root helper's port allowlist and restore-on-failure.
- `backend/tests/test_api_v1_jobs.py` and `test_launcher.py`: two real supervisors on one lock. A standby takes over only after a drain, the drained job finishes where it started, a drained supervisor heals itself, and readiness accepts only this container's live standby of the same build. The launcher relays the drain signals to the worker only.
- `backend/tests/test_nginx_country_boundary.py`: source-level proxy/header/CIDR checks, including visitor-IP restoration, original-peer preservation, and every location proxying through `privatools_app` with `Host $host`. It is not native nginx validation; the load test above ran real nginx.
- Keep deployment, browser, provider and account-specific evidence privately with the release record.

Deployment remains **prepared, not published** until a release candidate, host/native image checks, rollback evidence and final approval are recorded. Verified hosted OAuth and remaining new-release auth, analytics, webhook and edge-policy steps remain individually visible; they are not hidden behind a generic “all done” status.
