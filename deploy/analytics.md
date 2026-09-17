# Google Analytics integration

The current frontend uses the Google browser tag for sessions, first visits and foreground engagement. It sends one manually controlled page view for each canonical public route, plus `tool_success` from the existing successful-result signals in Merge PDF, Compress PDF, Image to PDF and JSON/XML Formatter. This is partial tool-action coverage, not a complete usage count. Manual pageviews exclude query strings and fragments; account, settings and personal-workspace routes are excluded. The owner explicitly retained automatic scroll, outbound-click and video-engagement measurement. Those automatic events may include external link destinations and video metadata, so this is not a manual-events-only integration. The app does not deliberately send file/form contents or account identity. Ads storage, ads personalization, ad user data and Google Signals are disabled.

The previous first-party Measurement Protocol browser sender is removed. Its backend endpoint remains for cached older clients; reserved `user_engagement` is translated to `foreground_time`, unknown events are dropped, and no time/session values are invented. Do not run a second browser pageview sender alongside the tag.

## Required Google settings before enabling

The following changes were saved on September 14, 2026 in the existing PrivaTools property `530357002`, web stream `14273376292`, measurement ID `G-B3VWQ44MX1`. They preserve the owner's latest choices:

1. Enhanced measurement remains enabled with **scrolls, outbound clicks and video engagement unchanged**. Site search, file downloads and form interactions are off. Under Page views > advanced settings, **Page changes based on browser history events** is off. Automatic history pageviews operate independently of `send_page_view:false` and would duplicate our route events.
2. Under Google tag > Configure tag settings > **Allow user-provided data capabilities**, **Automatically detect user-provided data** is off. The broader capability remains unchanged and enabled; no email, phone, address, CSS-selector or JavaScript-variable collection was configured by this work. Do not enable automatic detection or add a user-data snippet.
3. Keep advertising/Google Signals features off. Do not mark pageviews or timing events as key events to manipulate engagement or bounce metrics.
4. Run `python3 scripts/analytics/check-public-google-tag.py`. This makes one public script GET, does not execute it, does not access a dashboard and sends no collection events. Inspect its redacted report, then verify a fresh browser with every Google collection request intercepted. Unknown script formats or any unsafe flag must leave the switch off.

The public script verifier reports the three retained automatic features separately. The actual SDK was also checked in isolated browser contexts with collection intercepted. Keep network captures and account-specific evidence private. The verifier is an inspection aid, not a supported Google configuration API or an automatic guarantee. Inspect actual SDK payloads, then verify the deployed network/CSP path. Recheck after Google tag settings change.

## Runtime switches and visitor choices

`GA_BROWSER_TAG_ENABLED=true` is the operator's explicit attestation that the above configuration and actual SDK behavior have been reviewed. It defaults off. Local configuration and actual SDK checks now pass; the prepared configuration keeps the flag off pending reviewed release activation and verification of the production network/CSP path. No production environment variable was changed. The backend then permits the narrow Google script/collection origins only on public documents and provides a runtime meta flag. No frontend build flag or second measurement ID is needed. Development builds never load the tag.

By default the visitor must opt in using **Allow Google Analytics** on the Privacy page. No popup is used. The browser stores a versioned consent record with the choice time; existing old analytics IDs are not treated as consent. Withdrawing the choice immediately disables collection. Do Not Track, Global Privacy Control and saved opt-out always override consent or regional defaults. Analytics cookies/identifiers are pseudonymous, not anonymous. Clearing site data resets the choice. Historic consent records are not sent to a new tracking database.

Optional regional default-on requires all of:

- `GA_BROWSER_TAG_ENABLED=true` after safe tag verification.
- `GA_TRUSTED_COUNTRY_HEADER=true` only after the [nginx ingress trust boundary](analytics-country-proxy.md) is installed and verified. The application server must not be directly reachable by untrusted clients.
- `GA_DEFAULT_ON_COUNTRIES` containing a **reviewed positive list** of uppercase ISO country codes where this deployment may use an opt-out default. It defaults empty. This configuration is not a legal conclusion; do not infer that every country outside the EEA permits default-on.

The browser requests `/api/analytics/policy` on its current origin with no credentials and `cache:no-store`. The response contains only `mode: opt_in` or `mode: default_on`, with `Cache-Control: private, no-store`. No country or IP is sent to the browser or Google by this policy check. The server ignores raw `CF-IPCountry` and `X-Forwarded-For`; only the nginx-overwritten `X-PrivaTools-Country` is considered when explicitly trusted. Unknown/invalid/unclassified regions and policy failures remain opt-in. Nothing regional is inserted into cacheable HTML. A regional default never becomes a stored affirmative-consent record.

## Reading the existing report

The supplied Tag diagnostics screenshot says the browser tag has not been detected for 48 hours. This is compatible with an older Measurement Protocol-only sender: server events can arrive without the browser tag being detected. It does not by itself identify the deployed fault. The replacement is not deployed yet; a public script-configuration pass or local mocked test cannot clear that warning. After activation, verify actual network delivery and GA Realtime/Tag Assistant with the correct property, then allow diagnostics time to refresh.

Views count page-view events; Event count includes all event types. A row with equal views and events is consistent with collecting only pageviews for that row, but the screenshot alone does not show active event filters. Active users are users, whereas bounce rate is the share of sessions that were not engaged. They have different denominators. Average engagement time does not prove the bounce rate is correct or incorrect.

The former MP-only implementation did not generate Google's browser `first_visit` lifecycle. Zero New users despite Active users is consistent with that limitation. Duplicate senders also used separate anonymous IDs, and foreground time was attributed to the destination route. Existing screenshots are therefore insufficient to judge acquisition quality. The fix cannot reconstruct historic first visits, merge duplicate historical identities, recover unreported time or retroactively repair past reports. The new Google cookie identity may introduce another reporting discontinuity; inspect trends from the deployment date onward.

Official references:

- [Measurement Protocol overview](https://developers.google.com/analytics/devguides/collection/protocol/ga4)
- [Reserved Measurement Protocol names](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference)
- [Manual pageviews and enhanced history measurement](https://developers.google.com/analytics/devguides/collection/ga4/views)
- [Enhanced measurement fields](https://support.google.com/analytics/answer/9216061)
- [User-provided data collection](https://support.google.com/analytics/answer/14078702)
- [Engagement and bounce rate](https://support.google.com/analytics/answer/12195621)
- [EU user consent policy](https://www.google.com/about/company/user-consent-policy/)
- [Consent mode behavior](https://developers.google.com/tag-platform/security/concepts/consent-mode)
