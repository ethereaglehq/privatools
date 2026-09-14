import { useDocumentReader } from "@/skins/experience/useDocumentReader";
import { cn } from "@/lib/utils";
import { DocumentStudio } from "@/skins/experience/DocumentStudio";
/** Privacy disclosures aligned with the hosted runtime and optional services. */
import { useEffect, useState } from "react";
import { Shield } from "lucide-react";


import {
  googleAnalyticsAvailable,
  readAnalyticsPrivacyPreference,
  setAnalyticsOptOut,
  type AnalyticsPrivacyPreference,
} from "@/lib/analyticsPrivacy";

const LAST_UPDATED = "September 14, 2026";
const GIT_HISTORY_URL = "https://github.com/ethereaglehq/privatools/commits/main/frontend/src/pages/PrivacyPage.tsx";

interface Section { id: string; title: string; flag?: boolean }
const SECTIONS: Section[] = [
  { id: "short-version",       title: "The Short Version", flag: true },
  { id: "files-you-upload",    title: "1. Files You Upload" },
  { id: "client-side-tools",   title: "2. Client-Side Tools" },
  { id: "what-we-dont-collect",title: "3. Analytics Data Boundaries", flag: true },
  { id: "developer-accounts", title: "4. Optional Accounts" },
  { id: "server-infrastructure",title: "5. Server Infrastructure" },
  { id: "third-party",         title: "6. Third-Party Services" },
  { id: "open-source",         title: "7. Open Source Transparency" },
  { id: "childrens-privacy",   title: "8. Children's Privacy" },
  { id: "changes",             title: "9. Changes to This Policy" },
  { id: "contact",             title: "10. Contact" },
];

/** Preserve the same browser consent preference used by the analytics runtime. */
function AnalyticsOptOutPanel() {
  const [preference, setPreference] = useState<AnalyticsPrivacyPreference>(() => readAnalyticsPrivacyPreference());

  useEffect(() => {
    const refresh = () => setPreference(readAnalyticsPrivacyPreference());
    window.addEventListener("storage", refresh);
    window.addEventListener("privatools:analytics-policy", refresh);
    return () => { window.removeEventListener("storage", refresh); window.removeEventListener("privatools:analytics-policy", refresh); };
  }, []);

  const toggleOptOut = () => {
    setPreference(setAnalyticsOptOut(!preference.effectiveDisabled));
  };

  return (
    <aside className="not-prose my-5 rounded-xl border border-border bg-card overflow-hidden">
      <div className="p-4 sm:p-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] text-accent font-semibold">
              Analytics control
            </span>
            <span className="font-medium rounded-full border border-border bg-paper-2/60 px-2 py-0.5 text-[11px] text-muted-foreground">
              {preference.effectiveDisabled || !googleAnalyticsAvailable() ? "Analytics off" : "Analytics allowed"}
            </span>
          </div>
          <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
            {preference.browserPrivacySignal
              ? "Your browser’s privacy signal keeps analytics off, even if you previously allowed it."
              : !googleAnalyticsAvailable()
                ? "Analytics is currently unavailable. You can save your choice for when it becomes available."
                : !preference.effectiveDisabled
                  ? preference.consented
                    ? "You have allowed Google Analytics in this browser. You can withdraw that choice here at any time."
                    : "Analytics is enabled by the reviewed policy for your region. You can turn it off here at any time."
                  : "Google Analytics stays off unless you allow it. All tools work either way."}

          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={!preference.effectiveDisabled}
          disabled={preference.browserPrivacySignal}
          onClick={toggleOptOut}
          className={cn(
            "group inline-flex h-9 shrink-0 items-center gap-2 rounded-full border px-2.5 transition-colors",
            !preference.effectiveDisabled
              ? "border-accent/45 bg-accent/[0.08] text-accent"
              : "border-border bg-paper-2/60 text-muted-foreground hover:text-foreground"
          )}
        >
          <span
            aria-hidden="true"
            className={cn(
              "relative h-5 w-9 rounded-full border transition-colors",
              !preference.effectiveDisabled ? "border-accent/60 bg-accent/20" : "border-border bg-background"
            )}
          >
            <span
              className={cn(
                "absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 rounded-full bg-current transition-transform",
                !preference.effectiveDisabled ? "translate-x-[18px]" : "translate-x-1"
              )}
            />
          </span>
          <span className="font-medium text-[11px]">
            Allow Google Analytics
          </span>
        </button>
      </div>
    </aside>
  );
}

export default function PrivacyPage() {
  const { articleRef, progress, activeId, showTop, copied, scrollToHeading, scrollToTop, copyLink } = useDocumentReader(SECTIONS);
  return <DocumentStudio title="Privacy policy" description="Your files, your data, your choices. Here is how PrivaTools handles each of them." updated={LAST_UPDATED} historyHref={GIT_HISTORY_URL} sections={SECTIONS} activeId={activeId} onSection={scrollToHeading} progress={progress} articleRef={articleRef} copied={copied} onCopy={copyLink} onTop={scrollToTop} showTop={showTop}>
    <section id="short-version" className="mb-10 scroll-mt-20">
      <h2 className="sr-only">The Short Version</h2>
      <aside className="rounded-2xl border border-accent/30 bg-accent/[0.05] p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-3"><Shield size={15} className="text-accent"/><span className="text-[11px] text-accent font-semibold">The short version</span></div>
        <p><strong>Choose where your task runs.</strong> Browser tools process on your device. Server tools upload your file for temporary processing. AI provider tools send the content needed for your request to the provider you choose.</p>
        <p><strong>Accounts and analytics are separate choices.</strong> Interactive file tools do not require an account. Optional accounts use Clerk for identity and sign-in. Optional analytics measures public-site usage, including scrolling, outbound links and supported video engagement. It uses identifiers and cookies, so it is not anonymous.</p>
      </aside>
    </section>
    <div className="blog-prose prose-headings:scroll-mt-20">
      <h2 id="files-you-upload">1. Files You Upload</h2>
      <p>When you run a server tool, the selected file is sent to the processing service. The public deployment uses HTTPS. Its processing libraries read the document, image, audio or other content needed to perform your task.</p>
      <ul>
        <li><strong>Temporary processing:</strong> Inputs and outputs use isolated temporary per-request storage. This storage is part of the processing workflow, not an account file library.</li>
        <li><strong>Cleanup:</strong> Response cleanup removes the job’s temporary files. A background sweep also removes older files left by interrupted requests, failed workers or cleanup errors. Failures can delay removal; deletion is not a guarantee of immediate erasure or forensic unrecoverability.</li>
        <li><strong>Your copies:</strong> The original on your device and the result you download remain under your control. Server cleanup does not delete those copies or files saved in your browser’s local Vault.</li>
        <li><strong>Limits:</strong> File-size, image-dimension, resource and rate limits apply. Availability and acceptable inputs vary by tool and deployment.</li>
      </ul>
      <p><strong>Optional API background jobs:</strong> When background processing is available, inputs are held while the job is queued or running and removed when they are no longer needed. Completed results are available to the submitting API key for up to one hour, including repeat downloads after a connection failure. You can request deletion immediately through the job API; a running job must stop before its files are removed. Expired results cannot be downloaded, and a background sweep removes their files. Minimal job and retry records are eligible for cleanup 24 hours after the job finishes; these are separate from the result files.</p>
      <p>Read the processing label and any engine selector before running. The <a href="/trust">trust center</a> explains the workflow; the <a href="/blog/what-deleted-means">deletion guide</a> distinguishes temporary files, local copies and operational records.</p>

      <h2 id="client-side-tools">2. Client-Side Tools</h2>
      <p>Browser processing uses JavaScript or WebAssembly on your device. Tools such as text formatting, hashing, Markdown editing and subtitle conversion do not need to upload their input for that operation. Choosing a subsequent server or provider step changes the data path.</p>
      <p>Local AI engines also run inference in the browser. They first need model and runtime files. Background Remover’s U²-Net-P model and runtime are served from this site. Other local models can download resources from Hugging Face or a CDN; those hosts receive normal connection information such as IP address, user agent and requested resource URL. A model download does not include the document or audio being processed locally.</p>
      <p>Some AI workflows contain more than one step. Smart Redact can detect candidate text locally, then sends the PDF and the strings you approve to the backend to apply the redactions. Saving a translation as a PDF sends the translated text to the backend. Check the selected tool’s disclosure for the full workflow.</p>
      <p>Preferences, recent-tool history, saved recipes, Vault items and provider settings can be stored in this browser. The PWA caches application resources and supported model resources for reuse. Browser storage can be cleared or evicted; signing in does not turn these items into a cloud backup, and installation does not make server tools available offline.</p>

      <h2 id="what-we-dont-collect">3. Analytics Data Boundaries</h2>
      <p><strong>These exclusions describe analytics.</strong> Specifically, they cover the page and tool-success events constructed by PrivaTools. They do not mean the service receives no personal data: an account requires identity information, a server task receives the selected file, and a support message contains what you send.</p>
      <ul>
        <li>PrivaTools’ manual analytics events do not include account identity, email addresses, passwords or API keys.</li>
        <li>Those manual events do not include uploaded file contents, filenames, document text, prompts or tool output.</li>
        <li>Public page events use canonical route URLs and route-derived titles, without URL queries or fragments. Account, settings and personal-workspace routes are excluded from tracking.</li>
      </ul>
      <p>Enabled outbound-link and video events have their own metadata, described in Section 6. An outbound-link event can include query parameters from its destination URL; the clean page URL does not remove those destination parameters.</p>

      <h2 id="developer-accounts">4. Optional Accounts</h2>
      <p>Interactive file tools can be used as a guest. An optional account provides account settings and access to developer API keys. Clerk manages the hosted site’s identity, authentication and sessions, including the email address, username and any profile information or connected sign-in provider you supply.</p>
      <p>Clerk supports the enabled email verification, password-reset and sign-in flows. Security or verification messages may be sent to your email address. Passkeys can be added where supported; their availability depends on the configured account service and your browser or device. Hosted Clerk accounts do not use the legacy signup recovery-code flow.</p>
      <p>The PrivaTools backend associates an account identifier with issued API keys and usage or quota records. It stores API-key hashes and identifiers, labels, creation/revocation information and last-use information so keys can be managed and checked. API use can therefore be associated with an account even though processed files are not saved as an account library.</p>
      <p>The account-deletion action requests removal of the PrivaTools account records and keys, then deletion of the Clerk identity. A failed request can require another attempt. This does not clear browser-local Vault items, downloaded files, or operational records held separately by infrastructure providers.</p>
      <p>Self-hosted operators can configure a different identity service or the legacy native-account mode. The operator’s configuration and privacy policy govern that deployment. Clerk’s <a href="https://clerk.com/docs/guides/how-clerk-works/cookies" target="_blank" rel="noopener noreferrer">authentication-cookie documentation</a> explains its session cookies, which support sign-in independently of optional analytics.</p>

      <h2 id="server-infrastructure">5. Server Infrastructure</h2>
      <p>Hosting and delivery providers handle network requests and technical connection data. Static application assets can be cached by the delivery layer. Processing API responses use <code>no-store</code> headers and are configured to bypass response caching.</p>
      <p>Operational records support diagnostics, abuse prevention and service reliability. They can include timestamps, request identifiers, routes, status codes, duration, byte counts and error categories. Account operations can also record an account identifier. Hosting and proxy logs may contain IP addresses and other connection data. These records are separate from the temporary file cleanup described above; retention depends on the deployment’s operational configuration.</p>
      <p>Self-hosting changes who operates the service. Inspect that operator’s infrastructure, logging and backup settings rather than assuming every installation has identical behavior.</p>

      <h2 id="third-party">6. Third-Party Services</h2>
      <h3>Google Analytics and your choice</h3>
      <p>When available and permitted by your choice or a reviewed regional policy, Google Analytics measures public page visits, sessions, engagement time and selected successful tool actions. Google receives browser and cookie identifiers, device/browser information and network connection information, including your IP address.</p>
      <ul>
        <li><strong>Enabled automatic events:</strong> Scroll depth, outbound-link clicks and supported embedded-video engagement. Outbound events can include the destination URL and domain, including destination query parameters, link identifiers and CSS classes. Video events can include the provider, video title and URL, duration, current position and playback progress. See <a href="https://support.google.com/analytics/answer/9216061?hl=en" target="_blank" rel="noopener noreferrer">Google’s event and parameter documentation</a>.</li>
        <li><strong>Disabled automatic events:</strong> Form interactions, file downloads, site search and browser-history page views. PrivaTools sends its own canonical public-page events without queries or fragments and selected tool-success events without file or input details.</li>
        <li><strong>User-provided data:</strong> The Google tag configuration permits this capability, but automatic detection and snippet-based collection are disabled. PrivaTools does not supply identity data through a <code>user_data</code> parameter.</li>
        <li><strong>Advertising settings:</strong> Advertising storage, advertising user data, personalized advertising and Google Signals are disabled in the site’s tag configuration.</li>
      </ul>
      <p>Analytics requires opt-in unless a verified regional policy permits an opt-out default. An unknown region uses opt-in. Do Not Track and Global Privacy Control override an allowance. The control below saves your choice in this browser; withdrawing it stops further analytics collection through this site. Clearing site data resets the saved choice. Development previews do not send analytics. See <a href="https://business.safety.google/privacy/" target="_blank" rel="noopener noreferrer">Google’s information about data use</a>.</p>
      <AnalyticsOptOutPanel/>
      <h3>Identity, AI and delivery services</h3>
      <ul>
        <li><strong>Clerk and connected sign-in providers:</strong> Receive information needed for the account and authentication flows you use, including session and technical security information. Choosing an external sign-in provider also involves that provider.</li>
        <li><strong>Your AI provider:</strong> BYOK requests go from your browser to the provider or endpoint you select. Depending on the task, that request can contain extracted document text, prompts, images or audio, along with your provider key. Review that provider’s terms and retention settings. PrivaTools does not proxy the provider key through its backend.</li>
        <li><strong>Saved provider keys:</strong> The default local store encrypts saved keys in browser storage; session-only mode keeps keys in memory for the session. A key is readable in memory when needed for a provider request. Clearing a local key does not revoke it at the provider.</li>
        <li><strong>Model and delivery hosts:</strong> Model hosts and configured delivery services, such as Cloudflare, can receive connection metadata for requests they handle. Fonts are served from this site’s <code>/fonts</code> assets. Model downloads and account requests are separate from the analytics choice.</li>
      </ul>

      <h2 id="open-source">7. Open Source Transparency</h2>
      <p>The PrivaTools application source is available at <a href="https://github.com/ethereaglehq/privatools" target="_blank" rel="noopener noreferrer">github.com/ethereaglehq/privatools</a>. You can inspect its processing, cleanup and analytics implementation or operate a self-hosted copy. Third-party libraries, models and services have their own licenses and terms. Source availability does not certify a particular deployment’s configuration or every possible output.</p>

      <h2 id="childrens-privacy">8. Children's Privacy</h2>
      <p>The service is not directed at children under 13. Guest access still involves the network and processing data described in this policy. If you believe a child has supplied personal information to the service, contact us so we can review the request and appropriate removal steps.</p>

      <h2 id="changes">9. Changes to This Policy</h2>
      <p>We update the date above when this policy changes. Its public version history records source changes. Review the current policy and tool disclosures when your processing or account needs change.</p>

      <h2 id="contact">10. Contact</h2>
      <p>For questions about this policy or a request concerning your information, contact <a href="mailto:hello@privatools.me">hello@privatools.me</a>. You can also report general issues on <a href="https://github.com/ethereaglehq/privatools/issues" target="_blank" rel="noopener noreferrer">GitHub</a>. Public issues are visible to others; use email for account or personal-data requests.</p>
    </div>
  </DocumentStudio>;
}
