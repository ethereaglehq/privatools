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
shows. Answers from the app pass through as before: `proxy_intercept_errors`
stays off, so the app's own 413 or 504 keeps its JSON and its single
`Access-Control-Allow-Origin`. `backend/tests/test_nginx_api_error_cors.py`
checks the file's structure, and the origin map against docker-compose.yml.

### Apply it

The deploy never edits nginx; apply this by hand. The block below works
whether or not the zero-downtime cut-over
([README](README.md#production-rollout-runbook)) has routed the site through
the `privatools_app` upstream, and before the cut-over it keeps
`proxy_pass http://127.0.0.1:8000`. It changes nothing if the installed site
already has this change, or is not the file this change was written against:
main's before this change (`c39b151`), or v2.6.1's before the cut-over. It
reloads nginx only after `nginx -t` passes, and puts the previous site back if
the test fails.

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
site=/etc/nginx/sites-enabled/privatools
new=/tmp/nginx-privatools.conf
if sudo grep -q '^include /etc/nginx/privatools-upstream.conf;$' "$site"; then
  echo "The site routes through the privatools_app upstream: the zero-downtime cut-over has run."
  before=/tmp/nginx-privatools.main.conf
else
  echo "The site proxies to 127.0.0.1:8000: the zero-downtime cut-over has not run, so it keeps doing that."
  before=/tmp/nginx-privatools.v2.6.1.conf
  sed -i -e '\#^include /etc/nginx/privatools-upstream.conf;$#d' \
         -e 's#proxy_pass http://privatools_app;#proxy_pass http://127.0.0.1:8000;#' "$new"
fi
if sudo cmp -s "$new" "$site"; then
  echo "Already applied. Nothing to do."
  exit 0
fi
if ! sudo cmp -s "$before" "$site"; then
  echo "The installed site differs from $before, so it has changes of its own. Nothing was changed." >&2
  echo "Add the two maps and the API host's error pages from $new to it by hand." >&2
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

The diff it prints adds the two maps, the four `error_page` lines and the four
named locations: 58 lines in all. Before the cut-over it also adds the
comments #207 wrote about the upstream (13 lines, and one line reworded), which
change nothing.

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
the 503s read `503  text/html`.

nginx answers 502 only while the app is down, and 504 only after the app has
said nothing for 300 s, so the live site cannot show either on demand. On the
VM this prints 8, the four `error_page` lines and the four named locations
nginx loaded:

```bash
sudo nginx -T 2>/dev/null | grep -cE 'error_page (413|502|503|504) @api_|location @api_'
```

The old stop-and-start deploy leaves a gap while it restarts the container
(the zero-downtime rollout never does); during it, this loop prints
`502 https://privatools.me`:

```bash
while sleep 1; do curl -s -o /dev/null -H 'Origin: https://privatools.me' \
  -w '%{http_code} %header{access-control-allow-origin}\n' https://api.privatools.me/api/health; done
```

**4. To undo it,** put back the backup the block named:

```bash
sudo cp /home/ubuntu/nginx-backups/privatools.STAMP.bak /etc/nginx/sites-enabled/privatools \
  && sudo nginx -t && sudo systemctl reload nginx
```

### Rehearsed in nginx 1.18.0

On 24 September 2026, in the `nginx:1.18` image, the version on the VM:

- `nginx -t` passed on the file as shipped, with the TLS files and the
  upstream file standing in for the VM's.
- A copy that differed only in listen ports, `proxy_read_timeout 3s` and a
  stub upstream answered, for `Origin: https://privatools.me`, nginx's 413 (to
  a request announcing 600 MB over HTTP/1.1, and to a real 510 MB upload over
  HTTP/2), 502 (upstream down), 503 (17 of a burst of 40) and 504 (after 3 s).
  Each came with that origin, `Vary: Origin`, HSTS and the JSON detail. For
  `Origin: https://evil.example` the same answers carried no `Access-Control-*`
  header and no `Vary`. The stub's own 200 and 413 came through with exactly
  one `Access-Control-Allow-Origin`, the stub's.
- The same copy made from the previous file answered all of these as
  `text/html`, with no `Access-Control-Allow-Origin`.
- The block in step 2, run as written with `sudo` and `systemctl` stubbed, did
  the right thing in seven states of the installed site. It installed main's
  file, and v2.6.1's with `proxy_pass 127.0.0.1:8000` and no upstream file;
  `nginx -t` passed on both results. It said "Already applied" for both
  results. It changed nothing for a hand-edited copy of either file. When
  `nginx -t` failed (a certificate removed), it put the previous site back.

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
