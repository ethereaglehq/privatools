# Google Analytics integration

The frontend uses the Google browser tag for sessions, first visits and foreground engagement. It sends one manually controlled page view for each canonical public route, including every React Router navigation, one `tool_run` event per tool use, and the older `tool_success` signal from Merge PDF, Compress PDF, Image to PDF and JSON/XML Formatter. Manual pageviews exclude query strings and fragments; account, settings and personal-workspace routes are excluded. The owner explicitly retained automatic scroll, outbound-click and video-engagement measurement. Those automatic events may include external link destinations and video metadata, so this is not a manual-events-only integration. The app does not deliberately send file/form contents or account identity. Ads storage, ads personalization, ad user data and Google Signals are disabled.

## Usage events

`tool_run` fires once per run from the shared engines (`GenericUI`, `SimpleConvertUI`, `useMultiFileProcessor`), once per Batch page run and once per Pipeline step, plus a direct `emitToolRun` call in tools that keep their own processing loop. Tool code dispatches the `privatools:tool-run` DOM event through `frontend/src/lib/toolRun.ts`; the beacon in `frontend/src/lib/analyticsBeacon.ts` decides whether anything is sent.

| Parameter | Values |
| --- | --- |
| `tool_slug` | Registry slug; read from the `/tool/<slug>` or `/tools/<slug>` route when the caller omits it. Unknown slugs are dropped. |
| `tool_category` | The registry category of that slug (`organize`, `optimize`, `image`, `developer`, ...). |
| `run_mode` | `single`, `batch` or `pipeline`. |
| `outcome` | `success`, `partial` (some files failed) or `error`. |
| `file_count` | Files the run handled, when the caller knows it. Never names, sizes or contents. |

Register `tool_slug`, `tool_category`, `run_mode` and `outcome` as event-scoped custom dimensions and `file_count` as an event-scoped custom metric in the GA4 property; standard reports only show registered parameters.

The previous first-party Measurement Protocol browser sender is removed. Its backend endpoint remains for cached older clients; reserved `user_engagement` is translated to `foreground_time`, unknown events are dropped, and no time/session values are invented. Do not run a second browser pageview sender alongside the tag.

## Required Google settings before enabling

The following changes were saved on September 14, 2026 in the existing PrivaTools property `530357002`, web stream `14273376292`, measurement ID `G-B3VWQ44MX1`. They preserve the owner's latest choices:

1. Enhanced measurement remains enabled with **scrolls, outbound clicks and video engagement unchanged**. Site search, file downloads and form interactions are off. Under Page views > advanced settings, **Page changes based on browser history events** is off. Automatic history pageviews operate independently of `send_page_view:false` and would duplicate our route events.
2. Under Google tag > Configure tag settings > **Allow user-provided data capabilities**, **Automatically detect user-provided data** is off. The broader capability remains unchanged and enabled; no email, phone, address, CSS-selector or JavaScript-variable collection was configured by this work. Do not enable automatic detection or add a user-data snippet.
3. Keep advertising/Google Signals features off. Do not mark pageviews or timing events as key events to manipulate engagement or bounce metrics.
4. Run `python3 scripts/analytics/check-public-google-tag.py`. This makes one public script GET, does not execute it, does not access a dashboard and sends no collection events. Inspect its redacted report, then verify a fresh browser with every Google collection request intercepted. Unknown script formats or any unsafe flag must leave the switch off.

The public script verifier reports the three retained automatic features separately. The actual SDK was also checked in isolated browser contexts with collection intercepted. Keep network captures and account-specific evidence private. The verifier is an inspection aid, not a supported Google configuration API or an automatic guarantee. Inspect actual SDK payloads, then verify the deployed network/CSP path. Recheck after Google tag settings change.

## Runtime switches and visitor choices

`GA_BROWSER_TAG_ENABLED=true` is the operator's explicit attestation that the above configuration and actual SDK behavior have been reviewed. It defaults off and is on in production. The backend then permits the narrow Google script/collection origins only on public documents and provides a runtime meta flag. No frontend build flag or second measurement ID is needed. Development builds never load the tag.

Collection is on by default for every visitor. There is no consent prompt, no regional exception, and the app does not read Do Not Track or Global Privacy Control for this setting. The **Allow Google Analytics** switch on the Privacy page is the only visitor control: turning it off stores `pt-analytics-opt-out` in the browser and disables the tag immediately; turning it back on removes the key and resumes collection. Clearing site data resets the choice. Analytics cookies and identifiers are pseudonymous, not anonymous. The consent record written by the 14 to 17 September opt-in bundle is ignored.

`GET /api/analytics/policy` answers `mode: default_on` whenever the tag is enabled and `mode: opt_in` otherwise, with `Cache-Control: private, no-store`. Current bundles never request it. It stays so that browsers still holding the opt-in bundle switch on without a redeploy. The application no longer reads `X-PrivaTools-Country`; the nginx boundary in [analytics-country-proxy.md](analytics-country-proxy.md) is historical.

## Reading the existing report

This section describes reports from before 17 September 2026, when the browser tag was opt-in and almost nothing was collected.

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
