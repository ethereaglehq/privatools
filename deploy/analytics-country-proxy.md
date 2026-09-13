# Regional analytics country boundary

This is a staged configuration change. It has not been deployed, and it does not choose countries where analytics may run without opt-in. The deployment's reviewed country policy remains separate from the network signal.

## Contract

The browser requests `GET /api/analytics/policy` on its **page origin**. It must not use `PUBLIC_API_BASE_URL` / `resolveApiOrigin()` for this request: `api.privatools.me` is intentionally DNS-only and has no trusted Cloudflare country signal.

Only the exact policy location on `privatools.me` forwards `X-PrivaTools-Country`. Nginx computes that header from `CF-IPCountry` only when the **original connecting socket peer** belongs to a published Cloudflare ingress range. It overwrites the incoming internal header; it never trusts a browser-supplied `X-PrivaTools-Country`, `X-Forwarded-For`, timezone or language.

`$realip_remote_addr` is used instead of `$remote_addr` so enabling real-IP restoration elsewhere does not change the trust decision to the visitor's address. This requires nginx's HTTP real-IP module. Its absence must fail the configuration check; do not substitute a forwarded header to make the check pass.

The map accepts uppercase two-letter country syntax. Missing/malformed values, Cloudflare's `XX` / `T1` values, and Worker subrequests yield an empty internal header. Syntax does not confer policy permission: the backend must still classify the value against its deployment policy. Empty/unclassified means opt-in. Country-level IP geolocation is approximate and cannot determine all facts relevant to consent.

Every other proxy location in the Oracle configuration explicitly strips both `X-PrivaTools-Country` and raw `CF-IPCountry`, including HTML/static routes and the direct API host. The older `deploy/nginx.conf` also strips them and always produces unknown country. Header removal is repeated in each proxy location because `proxy_set_header` inheritance changes when a child supplies its own directives.

Backend agreement with the analytics owner:

- Read only `X-PrivaTools-Country`, and only when `GA_TRUSTED_COUNTRY_HEADER=true` explicitly attests that this boundary is installed and verified.
- `GA_DEFAULT_ON_COUNTRIES` is a deployment-selected positive allowlist, empty by default. This document does not populate it or make legal geography assumptions.
- `GET /api/analytics/policy` is public, same-origin and always returns `Cache-Control: private, no-store`. It returns policy, not an IP address or detailed location.
- Unknown country, failed/pending policy requests and unconfigured deployments require opt-in. A regional default is separate from stored affirmative consent. Saved opt-out, GPC and DNT override a regional default.

## Caching

The exact policy locations set `proxy_cache off`, `proxy_cache_bypass 1` and `proxy_no_cache 1`. They preserve the backend's private/no-store header. They do not add response headers that would accidentally replace the existing server security-header inheritance.

Keep this endpoint out of Cloudflare custom cache rules and service-worker caches. Do not inject visitor country/policy into `_get_seo_html` or shared cached HTML. Ordinary pages never receive the internal country header, so an incoming header cannot create a country-dependent page variant. If the proxy/header contract or cache behavior cannot be verified, leave `GA_TRUSTED_COUNTRY_HEADER` off.

## Free provider and range provenance

Cloudflare's country-only **IP Geolocation** setting is available on the Free plan. It does not require a paid geolocation API, Worker or a location permission prompt. Use the country-only option rather than adding city/coordinates that this feature does not need. [Cloudflare IP Geolocation](https://developers.cloudflare.com/network/ip-geolocation/)

The inline range list and `deploy/cloudflare-country-ranges.json` were verified on **14 September 2026** against Cloudflare's published [IPv4 list](https://www.cloudflare.com/ips-v4) and [IPv6 list](https://www.cloudflare.com/ips-v6): 15 IPv4 and 7 IPv6 networks. They are proxy networks, not permitted visitor countries. Update both representations from the official lists when Cloudflare changes them, review the diff, and rerun the focused tests. Do not broaden the list to all IPs, private networks or an arbitrary forwarded proxy chain.

Cloudflare documents `XX` as unavailable country data and `T1` for Tor. Worker subrequests are conservatively treated as unknown by this implementation. [Cloudflare HTTP headers](https://developers.cloudflare.com/fundamentals/reference/http-headers/)

Nginx documents the original-peer variable and trusted-address behavior in the [real-IP module](https://nginx.org/en/docs/http/ngx_http_realip_module.html), CIDR matching in the [geo module](https://nginx.org/en/docs/http/ngx_http_geo_module.html), and header/cache controls in the [proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).

## Review before activation

No commands in this section were run against production.

1. Review the active nginx configuration and verify `nginx -V` includes `--with-http_realip_module`. Confirm the backend remains reachable only through the trusted host proxy, as the current Compose loopback binding intends. Another proxy in front of nginx requires an explicit new trust design; this configuration conservatively treats an unknown socket peer as untrusted.
2. Install the reviewed Oracle vhost configuration using the existing backup/rollback procedure. Run `nginx -t` before reload. The file contains the complete CIDR map; no additional nginx include is required. Leave the backend country-trust flag off during validation.
3. Verify the country-only Cloudflare feature and the policy endpoint's cache bypass. Keep the direct API record DNS-only for existing uploads. No DNS change is required by this feature.
4. Check a normal apex request and a direct-origin request. A forged `X-PrivaTools-Country` or `CF-IPCountry` sent directly to the origin must not enable the default. An API-host request must remain opt-in even if it supplies these headers. Test absent, malformed and unknown country values. Do not expose a debug endpoint that echoes country/IP to verify this.
5. Verify repeated policy requests do not report a cache hit and carry the private/no-store header. Confirm normal HTML does not contain per-visitor policy. Validate the backend/frontend policy tests, then configure only the country policy the operator has approved and enable the explicit trust flag.
6. Verify that opt-out/GPC/DNT prevent loading the analytics tag and that unknown/error/pending policy stays opt-in. A rollback can immediately turn the trust flag off; unknown remains opt-in.

## Validation performed locally

`backend/tests/test_nginx_country_boundary.py` parses the actual shipped directives and validates the official range snapshot, IPv4/IPv6 ingress behavior, malformed/unknown country cases, Worker exclusion, original-peer input, header overwrites in every proxy location, direct-API isolation and policy cache directives. **24 tests passed.**

There is no nginx executable or container runtime available in this local environment. Native `nginx -t`, actual proxy request handling, deployed firewall rules and Cloudflare configuration remain target-environment checks. The tests are configuration-contract checks, not a claim that nginx or the regional analytics feature has been activated.
