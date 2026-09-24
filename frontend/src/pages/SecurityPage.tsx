import { useDocumentReader } from "@/skins/experience/useDocumentReader";
import { DocumentStudio } from "@/skins/experience/DocumentStudio";
/**
 * SecurityPage - factual trust and vulnerability reporting page.
 *
 * Keep claims tied to things the codebase currently does: open source,
 * no account needed, no paid tier, temporary processing, no-store API responses,
 * and browser-side tools where applicable. Do not imply external audits,
 * certifications, SOC 2, ISO, or formal bug bounty coverage.
 */

import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowUp,
  Check,
  FileText,
  History,
  KeyRound,
  Link2,
  List,
  Mail,
  Shield,
  TriangleAlert,
} from "lucide-react";



const LAST_UPDATED = "September 24, 2026";
const GIT_HISTORY_URL = "https://github.com/ethereaglehq/privatools/commits/main/frontend/src/pages/SecurityPage.tsx";

interface Section { id: string; title: string; flag?: boolean }
const SECTIONS: Section[] = [
  { id: "short-version", title: "The Short Version", flag: true },
  { id: "reporting", title: "1. Reporting Vulnerabilities" },
  { id: "threat-model", title: "2. Threat Model" },
  { id: "file-handling", title: "3. File Handling" },
  { id: "transparency", title: "4. Transparency Report" },
  { id: "rights", title: "5. Privacy Rights" },
  { id: "subprocessors", title: "6. Subprocessors" },
  { id: "security-txt", title: "7. security.txt" },
  { id: "limitations", title: "8. Limitations" },
  { id: "contact", title: "9. Contact" },
];

const SUBPROCESSORS = [
  { name: "Oracle Cloud Infrastructure", purpose: "Hosting the PrivaTools processing server and static deployment environment." },
  { name: "Cloudflare", purpose: "Optional edge CDN, TLS acceleration, and static asset delivery. File-processing API responses are marked no-store." },
  { name: "Google Analytics 4", purpose: "Usage analytics through the Google tag on public pages, on by default with a switch on the Privacy page: page visits, where visits come from, and tool runs with their outcome and, for most failures, a failure category. File contents, filenames and error messages are never sent." },
  { name: "Hugging Face CDN", purpose: "Browser-side AI model downloads for local WebAssembly tools. Model requests do not include user file contents." },
  { name: "GitHub", purpose: "Source hosting, issue reports, and public change history." },
];

export default function SecurityPage() {
  const {articleRef,progress,activeId,showTop,copied,scrollToHeading,scrollToTop,copyLink}=useDocumentReader(SECTIONS);
  return <DocumentStudio title="Security" description="How your files are handled, where the boundaries are, and how to report a problem." updated={LAST_UPDATED} historyHref={GIT_HISTORY_URL} sections={SECTIONS} activeId={activeId} onSection={scrollToHeading} progress={progress} articleRef={articleRef} copied={copied} onCopy={copyLink} onTop={scrollToTop} showTop={showTop}>
            <section id="short-version" className="mb-10 scroll-mt-20">
              <h2 className="sr-only">The Short Version</h2>
              <aside className="relative rounded-2xl border border-accent/30 bg-accent/[0.05] overflow-hidden">
                <div className="relative p-5 sm:p-6">

                  <div className="flex items-center gap-2 mb-3">
                    <KeyRound size={13} className="text-accent" />
                    <span className="text-[11px] text-accent font-semibold">The short version</span>
                  </div>
                  <p className="font-display text-[15.5px] text-foreground leading-relaxed mb-3">
                    Security reports go to <a className="text-accent hover:underline underline-offset-2" href="mailto:hello@privatools.me">hello@privatools.me</a>.
                    PrivaTools is open source, needs no account to use, and keeps file-processing routes on
                    temporary server storage or in your browser, depending on the tool.
                  </p>
                  <p className="font-display text-[15.5px] text-foreground/85 leading-relaxed">
                    The public service is not a certified or externally audited compliance product.
                    For the strictest control, use the MIT-licensed codebase to self-host your own instance.
                  </p>
                </div>
              </aside>
            </section>

            <div className="blog-prose prose-headings:scroll-mt-20">
              <h2 id="reporting">1. Reporting Vulnerabilities</h2>
              <p>
                Please email security reports to <a href="mailto:hello@privatools.me">hello@privatools.me</a> with
                the subject prefix <code>[Security]</code>. Include the affected route, steps to reproduce,
                impact, browser or operating system details, and proof-of-concept notes that avoid exposing
                anyone else's data.
              </p>
              <p>
                We aim to acknowledge security reports within 72 hours. Fix timing depends on severity,
                reproducibility, and deployment risk. Please avoid public disclosure until we have had a
                reasonable chance to investigate and ship a fix.
              </p>

              <h2 id="threat-model">2. Threat Model</h2>
              <p>
                PrivaTools is designed around a simple assumption: files can be sensitive, even when a tool
                looks routine. The main risks we design against are accidental file retention, shared-cache
                exposure, third-party upload leakage, cross-site scripting, overly broad browser permissions,
                and operational logs that reveal more than they need to.
              </p>
              <ul>
                <li><strong>No account layer:</strong> there are no user accounts, passwords, billing records, or saved workspaces on the public service.</li>
                <li><strong>Temporary processing:</strong> server-side tools use temporary paths and cleanup routines rather than permanent document storage.</li>
                <li><strong>Browser-side tools:</strong> many developer utilities and selected AI tools run locally in the browser.</li>
                <li><strong>Cache controls:</strong> dynamic <code>/api/</code> responses carry <code>no-store</code> headers in the backend.</li>
                <li><strong>Source visibility:</strong> the code is public, MIT-licensed, and self-hostable.</li>
              </ul>

              <h2 id="file-handling">3. File Handling</h2>
              <p>
                Server-side tools receive files over HTTPS, process them inside the PrivaTools container,
                and return the result. The service does not intentionally retain uploaded files, outputs,
                thumbnails, or extracted text after a request is complete. Browser-side tools process data
                locally and do not send file contents to the PrivaTools backend.
              </p>
              <p>
                Standard infrastructure metadata can still exist: request path, status code, timestamp,
                user agent, and connection metadata may be visible to the server or infrastructure providers.
                Uploaded file bodies are not used for analytics, advertising, profiling, or model training.
              </p>

              <h2 id="transparency">4. Transparency Report</h2>
              <p>
                PrivaTools does not publish a formal incident archive yet. As of {LAST_UPDATED}, the public
                trust artifacts are this page, <code>SECURITY.md</code>, the RFC 9116 <code>security.txt</code>,
                the privacy policy, and the public source history.
              </p>
              <ul>
                <li><strong>External certifications:</strong> none claimed.</li>
                <li><strong>External security audit:</strong> none claimed.</li>
                <li><strong>Bug bounty:</strong> no paid bounty program is advertised.</li>
                <li><strong>Public cleanup metrics endpoint:</strong> deferred; the current slice does not add <code>/api/transparency/janitor</code>.</li>
              </ul>

              <h2 id="rights">5. Privacy Rights</h2>
              <p>
                PrivaTools does not intentionally retain uploaded file contents, so most file-specific
                access, deletion, or export requests cannot be fulfilled after processing: the service
                should no longer have the file. If you have created an optional developer account, the
                data held against it is your email address and your API keys — you can view it and delete
                it permanently from your account at any time, without contacting us. For privacy questions
                about operational logs, analytics, or infrastructure metadata, contact
                <a href="mailto:hello@privatools.me">hello@privatools.me</a>.
              </p>
              <p>
                The <Link to="/privacy">Privacy Policy</Link> explains analytics, subprocessors,
                and browser-side processing in more detail.
              </p>

              <h2 id="subprocessors">6. Subprocessors</h2>
              <p>
                These providers may see ordinary web or infrastructure metadata. They should not receive
                uploaded file contents from PrivaTools file-processing API responses.
                Fonts are self-hosted from <code>/fonts</code> on <code>privatools.me</code>.
              </p>
            </div>

            <div className="my-5 overflow-hidden rounded-xl border border-border bg-card">
              <table className="w-full text-left text-[13px]">
                <thead className="font-medium border-b border-border bg-paper-2/50 text-[11px] text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Provider</th>
                    <th className="px-4 py-3 font-medium">Purpose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {SUBPROCESSORS.map(item => (
                    <tr key={item.name}>
                      <td className="px-4 py-3 font-semibold text-foreground align-top">{item.name}</td>
                      <td className="px-4 py-3 text-muted-foreground leading-relaxed">{item.purpose}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="blog-prose prose-headings:scroll-mt-20">
              <h2 id="security-txt">7. security.txt</h2>
              <p>
                The security contact file is published at{" "}
                <a href="/.well-known/security.txt">/.well-known/security.txt</a>. It follows RFC 9116
                with contact, expiration, preferred language, canonical URL, and policy fields.
              </p>
              <pre><code>{`Contact: mailto:hello@privatools.me
Expires: 2027-06-17T23:59:00Z
Preferred-Languages: en
Canonical: https://privatools.me/.well-known/security.txt
Policy: https://privatools.me/security`}</code></pre>

              <h2 id="limitations">8. Limitations</h2>
              <p>
                PrivaTools is provided for general-purpose file processing. Do not treat it as a regulated
                compliance environment unless you have reviewed, deployed, and controlled your own instance.
                The public site does not claim SOC 2, ISO 27001, HIPAA, PCI DSS, or GDPR certification.
              </p>
              <p>
                Please do not run destructive tests, denial-of-service tests, social engineering,
                credential attacks, or scans that degrade service for other users.
              </p>

              <h2 id="contact">9. Contact</h2>
              <p>
                Security and privacy questions: <a href="mailto:hello@privatools.me">hello@privatools.me</a>.
                Source code and public issues:{" "}
                <a href="https://github.com/ethereaglehq/privatools" target="_blank" rel="noopener noreferrer">
                  GitHub
                </a>.
              </p>
            </div>
  </DocumentStudio>;
}
