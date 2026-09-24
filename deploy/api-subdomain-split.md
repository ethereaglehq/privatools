# api-subdomain split — activation runbook

> **Status: active in production** (checked 18 September 2026). `privatools.me`
> and `www` are served through Cloudflare, `api.privatools.me` resolves
> directly to the VM, and the homepage carries
> `<meta name="privatools:api-base" content="https://api.privatools.me">`.
> The steps below record how it was activated; keep them for rollback and for
> rebuilding the host.

**Goal:** put `privatools.me` + `www` behind Cloudflare's proxy (edge cache,
Brotli, DDoS protection — makes the "edge CDN" claim true) **without** breaking
large uploads. Cloudflare's free/pro plans cap a proxied request body at
**100 MB**, but PrivaTools accepts **500 MB**. So the SPA's `/api` traffic is
moved to `api.privatools.me`, a **grey-clouded** (DNS-only) host that goes
straight to the VM — uncapped, and never transiting a third party (good for a
privacy-first tool). Static/SSR stays on the proxied apex.

```
browser ──▶ privatools.me        (orange/proxied) ──▶ Cloudflare edge ──▶ VM nginx ──▶ FastAPI   (HTML + assets, cached)
browser ──▶ api.privatools.me     (grey/DNS-only)  ─────────────────────▶ VM nginx ──▶ FastAPI   (/api uploads, direct)
```

## What's in the repo (flag-gated, default off)

The whole split is gated on one backend env var, **`PUBLIC_API_BASE_URL`**.
Empty (default) = same-origin, identical to today. Set to
`https://api.privatools.me` and the backend:

- injects `<meta name="privatools:api-base" content="https://api.privatools.me">`
  into `index.html` at serve time — the already-built SPA reads it
  (`frontend/src/lib/api.ts` → `resolveApiOrigin()`) and sends `/api` there.
  **No frontend rebuild needed.**
- widens the CSP `connect-src` to allow the cross-origin fetches
  (`backend/app/main.py` → `_content_security_policy`).
- auto-adds `api.privatools.me` to `TRUSTED_HOSTS` so the proxied Host header
  isn't rejected.

nginx gets a dedicated `api.privatools.me` vhost
(`deploy/oracle-vm/nginx-privatools.conf`) that proxies **only** `/api/*` to the
same FastAPI upstream (everything else 404s — no duplicate SPA on the api host).

## Activation order (no upload-breaking window)

Do these **in order**. The apex is only proxied *after* the SPA is already
talking to the grey api host, so there's never a moment where a proxied apex
`/api` upload could hit the 100 MB cap.

1. **Cloudflare DNS — add the api record (grey).** Dashboard → DNS → Add record:
   `A · api · 140.245.15.140 · Proxy status: DNS only (grey)`. Leave apex/`www`
   grey for now. Confirm: `dig +short api.privatools.me` → `140.245.15.140`.

2. **Issue the cert on the VM** (api is grey/direct, so HTTP-01 reaches the VM
   without Cloudflare in the way). The api `:80` vhost serves the challenge from
   `/var/www/certbot`, but it isn't deployed yet (its `:443` block references the
   cert that doesn't exist — chicken-and-egg), so bootstrap issuance with a
   throwaway `:80` block, then issue via webroot:
   ```bash
   ssh -i "<key>" ubuntu@140.245.15.140
   sudo mkdir -p /var/www/certbot
   sudo tee /etc/nginx/sites-enabled/api-acme-bootstrap.conf >/dev/null <<'CONF'
   server {
       listen 80;
       server_name api.privatools.me;
       location /.well-known/acme-challenge/ { root /var/www/certbot; }
       location / { return 404; }
   }
   CONF
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot certonly --webroot -w /var/www/certbot -d api.privatools.me \
        --non-interactive --agree-tos
   sudo rm /etc/nginx/sites-enabled/api-acme-bootstrap.conf
   sudo nginx -t && sudo systemctl reload nginx
   ```
   This touches only a separate file — the main `privatools` vhost is never
   edited. Renewal afterward is automatic: the real api `:80` vhost (step 3)
   keeps serving `/.well-known/acme-challenge/` from `/var/www/certbot`, so
   `certbot renew` works unattended.
   **Do not continue until the cert exists** — the api `:443` vhost references
   `/etc/letsencrypt/live/api.privatools.me/`, so a missing cert makes
   `nginx -t` (step 3) fail. Verify:
   ```bash
   sudo ls -l /etc/letsencrypt/live/api.privatools.me/fullchain.pem \
              /etc/letsencrypt/live/api.privatools.me/privkey.pem
   ```
   If certbot failed, it's almost always the `api` DNS record (step 1) not yet
   propagated or an HTTP-01 timeout — re-check `dig +short api.privatools.me`,
   wait, and re-run certbot.

3. **Deploy the nginx config** (now contains the api vhost) and reload. The
   `&&` chain only reloads if `nginx -t` passes, so a config error leaves the
   *running* nginx untouched; the backup lets you restore the sites file:
   ```bash
   scp deploy/oracle-vm/nginx-privatools.conf ubuntu@140.245.15.140:/tmp/
   ssh ubuntu@140.245.15.140 'sudo cp /etc/nginx/sites-enabled/privatools \
       /home/ubuntu/nginx-backups/privatools.$(date +%s).bak && \
     sudo cp /tmp/nginx-privatools.conf /etc/nginx/sites-enabled/privatools && \
     sudo nginx -t && sudo systemctl reload nginx'
   ```
   Verify: `curl -s https://api.privatools.me/api/health` → JSON health;
   `curl -so /dev/null -w '%{http_code}\n' https://api.privatools.me/` → `404`.

4. **Flip the backend flag.** Set `PUBLIC_API_BASE_URL=https://api.privatools.me`
   in the VM's container env (compose `.env` / systemd `Environment=`) and
   restart the container. Verify:
   - `curl -s https://privatools.me/ | grep -o 'privatools:api-base'` → present.
   - `curl -sI https://privatools.me/ | tr ';' '\n' | grep api.privatools.me`
     → CSP `connect-src` lists the api origin.
   - In a browser, run a tool and watch DevTools → Network: the upload goes to
     `api.privatools.me`, returns 200, and a **>100 MB** file still succeeds.

5. **Orange-cloud the apex + www.** Cloudflare → DNS → set `privatools.me` and
   `www` to **Proxied**. SSL/TLS → **Full (strict)**. Add a cache rule to cache
   `*/assets/*` and **bypass `/api/*`**. Leave `api` **grey**. Verify after
   warm-up: `curl -sI https://privatools.me/assets/<hashed>.js | grep -i cf-cache-status`
   → `HIT`, and uploads still work (they go to the grey api host).

   > Note: the apex **still serves `/api`** after the split — it's the same
   > FastAPI app behind nginx — the SPA just no longer sends *uploads* there.
   > `curl https://privatools.me/api/health` returns `200`, not 404. The apex
   > `/api` surface that's still used is the small `og-image` GET (social-card
   > URLs stay on the apex). The bypass rule keeps any apex `/api` response off
   > the edge cache; it isn't load-bearing for the SPA but is correct hygiene
   > (and harmless to og-image, which already sets its own cache headers).

## nginx's own error answers on the API host (added 24 September 2026)

The page reads every API answer cross-origin, and a browser gives a
cross-origin page nothing of an answer without `Access-Control-Allow-Origin`:
not its status, not its text. The app puts CORS headers on everything it
answers, its errors included. But nginx answers some requests itself: 413 when
an upload is over `client_max_body_size`, 502 while the app is down, 504 when
the app says nothing for `proxy_read_timeout`, and 503 from `limit_req` and
`limit_conn`. Those answers carried no CORS headers, so the page saw each one
as a network failure: it said "Couldn't reach the server", reported
`error_kind` `network`, and sent the upload again.

The API host's `location /api/` now sends those four statuses to named
locations (`@api_too_large`, `@api_unavailable`, `@api_busy`, `@api_timeout`).
Each adds `Access-Control-Allow-Origin` and `Vary: Origin` for the origins in
`ALLOWED_ORIGINS` (the `$pt_cors_origin` map) and nothing for any other
origin. It re-declares HSTS, since a location with its own `add_header`
inherits none of the server's, and answers with a JSON `detail` the page
shows. An empty `types {}` keeps a URI's extension from choosing another
Content-Type. Answers from the app pass through as before:
`proxy_intercept_errors` stays off, so the app's own 413 or 504 keeps its JSON
and its single `Access-Control-Allow-Origin`.
`backend/tests/test_nginx_api_error_cors.py` checks the file's structure, and
the origin map against docker-compose.yml.

**What the page can read.** Every upload is preflighted: the page watches its
progress, so the browser first sends an `OPTIONS` request, and a preflight must
be answered with a 2xx, which the app gives.

- nginx's **413** (an upload over 500 MB) and its **504** (the app silent for
  300 s) answer the upload itself, after the app has answered the preflight.
  The page reads both, and counts them as `too_large` and `timeout`.
- While the app is down, nginx answers the preflight too, with the **502**. The
  browser then refuses to send the upload at all, and the page sees a network
  error as before. It reads the 502 only when the browser still holds a
  preflight for that endpoint, cached for up to 600 s after one succeeded; the
  upload is then sent, and its 502 comes once nginx has received all of it.
- A **503** from `limit_req` or `limit_conn` is read when it refuses the upload
  and seen as a network error when it refuses the preflight, which counts
  against the same limits.
- A request that is not preflighted reads all four: a form without a file, or
  a `GET`.

### Apply it

The deploy never edits nginx; apply this by hand with the block in step 2.
What it does, and what it never does:

- It checks its three inputs against the SHA-256 of the files step 1 copies,
  and never modifies them: the site it installs is written to a temporary
  copy. Running it again later, even without step 1, uses the same files.
- It reads from the installed site whether the zero-downtime cut-over
  ([README](README.md#production-rollout-runbook)) has run. If the site
  includes `/etc/nginx/privatools-upstream.conf`, it installs this
  repository's file unchanged, which proxies only through the
  `privatools_app` upstream the rollout manages, and it checks that first. If
  not, it installs the same file with `proxy_pass http://127.0.0.1:8000` and
  no upstream include, as that site has.
- It never writes the upstream file, so it never moves traffic between 8000
  and 8001. It refuses to run as root, which would create the deploy lock the
  timer then cannot open; while a deploy holds that lock; and while a deploy
  has left a switch of the upstream unfinished
  (`/home/ubuntu/privatools/.privatools-deploy.switching`).
- It changes nothing if the installed site already has this change, or is not
  the file this change was written against: main's before this change
  (`c39b151`, which v2.7.1 also ships), or v2.6.1's before the cut-over.
- It reloads nginx only after `nginx -t` passes, and puts the previous site
  back if the test fails.

**1. On your Mac,** in the repository at a `main` that contains this change
(run `git fetch --tags` first):

```bash
git show c39b151:deploy/oracle-vm/nginx-privatools.conf > /tmp/nginx-privatools.main.conf
git show v2.6.1:deploy/oracle-vm/nginx-privatools.conf > /tmp/nginx-privatools.v2.6.1.conf
scp deploy/oracle-vm/nginx-privatools.conf /tmp/nginx-privatools.main.conf \
    /tmp/nginx-privatools.v2.6.1.conf priva:/tmp/
ssh priva
```

**2. On the VM,** as `ubuntu`, paste this whole block:

```bash
bash -eu <<'RUNBOOK'
# As ubuntu: root would create the deploy lock below, which the timer then cannot open.
[ "$(id -u)" != 0 ] || { echo "Run this as ubuntu, not as root. Nothing was changed." >&2; exit 1; }
# Exactly the three files step 1 copies. This block never modifies them.
cd /tmp
sha256sum --check --quiet <<'SUMS' || { echo "These are not the files step 1 copies. Repeat step 1. Nothing was changed." >&2; exit 1; }
c04a89a48a54c166205d280dab19d169384b0ac216b2fc782d05abc2f7be74f6  nginx-privatools.conf
7a1c808192f5b468e8991f7c13527a2ea18e4fded99f541bd749513e9e8d38fd  nginx-privatools.main.conf
e0ad18f21170441d2f2867a104a4f539fc0fd9bc722986133caea0082918a379  nginx-privatools.v2.6.1.conf
SUMS
# No deploy may run meanwhile, and none may have left a switch of the upstream half done.
exec 9>>/tmp/privatools-auto-deploy.lock
flock -n 9 || { echo "A deploy is running. Run this again once it has finished. Nothing was changed." >&2; exit 1; }
if [ -e /home/ubuntu/privatools/.privatools-deploy.switching ]; then
  echo "A deploy left a switch of the upstream unfinished; the next deploy completes it. Run this again after that. Nothing was changed." >&2
  exit 1
fi
site=/etc/nginx/sites-enabled/privatools
src=/tmp/nginx-privatools.conf
new=$(mktemp /tmp/nginx-privatools.install.XXXXXX)
trap 'rm -f "$new"' EXIT
if sudo grep -q '^include /etc/nginx/privatools-upstream.conf;$' "$site"; then
  echo "The site routes through the privatools_app upstream: the zero-downtime cut-over has run."
  before=/tmp/nginx-privatools.main.conf
  cp "$src" "$new"
  # What the rollout requires of the site: every proxy_pass through the upstream it manages.
  grep -q 'proxy_pass http://privatools_app;' "$new" && ! grep -q 'proxy_pass http://127\.0\.0\.1:' "$new" \
    || { echo "The new site would not proxy through the upstream. Nothing was changed." >&2; exit 1; }
else
  echo "The site proxies to 127.0.0.1:8000: the zero-downtime cut-over has not run, so it keeps doing that."
  before=/tmp/nginx-privatools.v2.6.1.conf
  sed -e '\#^include /etc/nginx/privatools-upstream.conf;$#d' \
      -e 's#proxy_pass http://privatools_app;#proxy_pass http://127.0.0.1:8000;#' "$src" > "$new"
fi
if sudo cmp -s "$new" "$site"; then
  echo "Already applied. Nothing to do."
  exit 0
fi
if ! sudo cmp -s "$before" "$site"; then
  echo "The installed site differs from $before, so it has changes of its own. Nothing was changed." >&2
  echo "Add the two maps and the API host's error pages from $src to it by hand." >&2
  exit 1
fi
stamp=$(date +%s)
mkdir -p /home/ubuntu/nginx-backups
sudo cp "$site" "/home/ubuntu/nginx-backups/privatools.$stamp.bak"
sudo diff -u "$site" "$new" || true
sudo cp "$new" "$site"
if sudo nginx -t; then
  sudo systemctl reload nginx
  echo "Reloaded. The previous site is /home/ubuntu/nginx-backups/privatools.$stamp.bak"
else
  sudo cp "/home/ubuntu/nginx-backups/privatools.$stamp.bak" "$site"
  sudo nginx -t
  echo "nginx -t refused the new site. The previous one is back; nothing was reloaded." >&2
  exit 1
fi
RUNBOOK
```

After the cut-over, the diff it prints adds 79 lines and removes 11; before
it, 90 and 10. The added lines are the two maps, the four `error_page` lines
and the four named locations with their comments; every removed line is one
of the file's old apply and rollback comments, which now point here. Before
the cut-over, 13 of the added lines and one reworded line are the comments
#207 wrote about the upstream, which change nothing.

**Run it again after a cut-over with an older release.** The cut-over's step 6
copies the release's own site file over this one. A release older than this
change (v2.7.1 and earlier) has no error pages, so they go. Run step 2 again
then. If it says the files are not the ones step 1 copies (a reboot clears
`/tmp`), repeat step 1 first.

**3. Check it** from any machine. Nothing is uploaded: nginx refuses a request
that announces more than 500 MB from its headers alone, before reading any of
it, and the app never sees it.

```bash
for origin in https://privatools.me https://evil.example; do
  echo "== Origin: $origin"
  curl -s -i --http1.1 -X POST https://api.privatools.me/api/merge -H "Origin: $origin" \
    -H 'Content-Type: application/octet-stream' -H 'Content-Length: 600000000' -H 'Expect:' \
    --data-binary '' | grep -iE '^(HTTP|content-type|access-control|vary)|detail'
done
```

For `https://privatools.me`: `HTTP/1.1 413`, `Content-Type: application/json`,
`Access-Control-Allow-Origin: https://privatools.me`, `Vary: Origin`, and
`{"detail": "This upload is too large: one request to the server can carry up
to 500 MB."}`. For `https://evil.example`: the same status, type and detail,
and no `Access-Control-*` or `Vary` line. Before this change both printed
`Content-Type: text/html` and no `Access-Control-Allow-Origin`.

Optionally, nginx's 503: a burst from one address runs into `limit_req` (10
requests a second, burst 20). It holds back only your own address, for a
second or two. `%header{}` needs curl 7.84 or later, as on current macOS.

```bash
seq 40 | xargs -P 40 -I{} curl -s -o /dev/null -H 'Origin: https://privatools.me' \
  -w '%{http_code} %header{access-control-allow-origin} %header{content-type}\n' \
  'https://api.privatools.me/api/health?n={}' | sort | uniq -c
```

Expect lines `200 https://privatools.me application/json` from the app and
`503 https://privatools.me application/json` from nginx. Before this change
the 503s read `503  text/html`. These `GET`s are not preflighted, so they show
the header an upload's own 503 carries; an upload whose preflight is refused
still fails as a network error (see above).

nginx answers 502 only while the app is down, and 504 only after the app has
said nothing for 300 s, so the live site cannot show either on demand. On the
VM this prints 8, the four `error_page` lines and the four named locations
nginx loaded:

```bash
sudo nginx -T 2>/dev/null | grep -cE 'error_page (413|502|503|504) @api_|location @api_'
```

The old stop-and-start deploy leaves a gap while it restarts the container
(the zero-downtime rollout never does); during it, this loop prints
`502 https://privatools.me`. It shows the answer's headers; a browser upload
reads that 502 only with a cached preflight (see above).

```bash
while sleep 1; do curl -s -o /dev/null -H 'Origin: https://privatools.me' \
  -w '%{http_code} %header{access-control-allow-origin}\n' https://api.privatools.me/api/health; done
```

**4. To undo it,** until the site file next changes, put back the backup the
block named:

```bash
sudo cp /home/ubuntu/nginx-backups/privatools.STAMP.bak /etc/nginx/sites-enabled/privatools \
  && sudo nginx -t && sudo systemctl reload nginx
```

Once the site has changed again, for example at the cut-over's step 6, that
backup would undo the later change too. Remove the two maps, the four
`error_page` lines and the four named locations by hand instead, then run
`sudo nginx -t` and reload.

### Rehearsed in nginx 1.18.0

On 24 September 2026, in Ubuntu 22.04's own nginx package, 1.18.0, the build
the VM reports as `nginx/1.18.0 (Ubuntu)`, with Ubuntu's `nginx.conf` and its
default site beside this one:

- `nginx -t` passed on the file as shipped, with the TLS files and the
  upstream file standing in for the VM's.
- A copy that differed only in listen ports, `proxy_read_timeout 3s` and a
  stub upstream answered, for `Origin: https://privatools.me`, nginx's 413 (to
  a request announcing 600 MB over HTTP/1.1, and to a real 510 MB upload over
  HTTP/2), 502 (upstream down), 503 (15 of a burst of 40) and 504 (after 3 s).
  Each came with that origin, `Vary: Origin`, HSTS and the JSON detail, also
  for `/api/og/card.png` and `/api/report.html`. For
  `Origin: https://evil.example` the same answers carried no
  `Access-Control-*` header and no `Vary`. The stub's own 200 and 413 came
  through with exactly one `Access-Control-Allow-Origin`, the stub's: 18 of 18
  checks. The same copy made from the previous file answered all of them as
  `text/html`, without `Access-Control-Allow-Origin`.
- The block in step 2 ran exactly as written, as `ubuntu` through a real
  `sudo`, with `systemctl reload nginx` standing for nginx's own reload
  signal. Two stub apps inside nginx answered `canonical` on 127.0.0.1:8000
  and `interim` on 8001, so a request through the API host showed where nginx
  routed. Each of these ran in a fresh container:
  - **Before the cut-over** (v2.6.1's site): it installed the 8000 form, and
    nginx's 413 became JSON with the allowed origin. Run again: "Already
    applied".
  - **Then a cut-over with v2.7.1** (the upstream file on 8000, then v2.7.1's
    site file, without the error pages), and the block again **without step
    1**: it installed this file unchanged, which passes the rollout's own site
    check. Run again: "Already applied".
  - **Then a deploy switched to the interim** (upstream on 8001), and
    v2.7.1's file came back: it installed this file, requests still reached
    the interim, and the upstream file was untouched. Run again: "Already
    applied".
  - **A cut-over with a release that contains this change:** "Already
    applied", twice. **The cut-over first, then the block:** installed, then
    "Already applied".
  - **The block before this fix, in the same sequence:** after the v2.7.1
    cut-over with the interim serving, it installed its own edited copy of the
    file, with `proxy_pass http://127.0.0.1:8000` and no include. Requests
    moved from the interim to 8000, and the site failed the rollout's check.
    The block above refuses that edited copy by its checksum and changes
    nothing.
  - **Refused, with nothing changed:** a hand-edited site, before and after
    the cut-over; a run as root, which created no deploy lock either; a
    deploy holding the lock; and a recorded unfinished switch. When
    `nginx -t` failed on the new site (a stand-in `nginx -t` that refused
    it), the previous site was put back and nginx was not reloaded.

## Rollback

- **Fastest (code path):** unset `PUBLIC_API_BASE_URL`, restart the container →
  the SPA is served with no meta tag and reverts to same-origin `/api`. If the
  apex is orange-clouded, also **grey-cloud apex + www** in Cloudflare in the
  same pass, or >100 MB uploads (now back on the apex) would hit the cap.
- **Network only:** grey-cloud apex + www in Cloudflare → all traffic direct to
  the VM again; the api host can stay or go.

## Notes / gotchas

- **Cert renewal.** `certbot --nginx` manages the HTTP-01 challenge during
  renewal even though the `:80` blocks `return 301` (it injects a temporary
  challenge location). `api.privatools.me` is grey, so its renewal is direct and
  unaffected by Cloudflare. For the **apex/www** cert once orange-clouded:
  HTTP-01 still passes through Cloudflare unless *Always Use HTTPS* rewrites the
  challenge — if a renewal fails, add a config rule excluding
  `/.well-known/acme-challenge/*` or switch those domains to DNS-01.
- **One var, not two.** `TRUSTED_HOSTS` does **not** need `api.privatools.me`
  added by hand — the backend derives it from `PUBLIC_API_BASE_URL`.
- **CORS is cookieless.** `allow_credentials=False`; uploads send no cookies, so
  the cross-origin split needs no `SameSite`/credential changes.
- **og:image stays on the apex.** Social-card URLs remain `https://privatools.me/...`
  (small, GET, edge-cacheable) — they are not moved to the api host.
