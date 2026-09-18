import { useDocumentReader } from "@/skins/experience/useDocumentReader";
import { DocumentStudio } from "@/skins/experience/DocumentStudio";
/** Terms of service: original policy content in the shared Air/Play document reader. */
import { Link } from "react-router-dom";

import { FileText, ArrowLeft, ArrowUp, Link2, Check, List, History, Mail } from "lucide-react";



const LAST_UPDATED = "September 18, 2026";
const GIT_HISTORY_URL = "https://github.com/ethereaglehq/privatools/commits/main/frontend/src/pages/TermsPage.tsx";

interface Section { id: string; title: string; flag?: boolean }
const SECTIONS: Section[] = [
  { id: "acceptance",            title: "1. Acceptance of Terms" },
  { id: "description",           title: "2. Description of Service" },
  { id: "acceptable-use",        title: "3. Acceptable Use", flag: true },
  { id: "file-processing",       title: "4. File Processing" },
  { id: "no-warranty",           title: "5. No Warranty", flag: true },
  { id: "liability",             title: "6. Limitation of Liability", flag: true },
  { id: "intellectual-property", title: "7. Intellectual Property" },
  { id: "availability",          title: "8. Service Availability" },
  { id: "changes",               title: "9. Changes to Terms" },
  { id: "contact",               title: "10. Contact" },
];

export default function TermsPage() {
  const {articleRef,progress,activeId,showTop,copied,scrollToHeading,scrollToTop,copyLink}=useDocumentReader(SECTIONS);
  return <DocumentStudio title="Terms of service" description="The rules for using PrivaTools, written in plain language and kept in the open." updated={LAST_UPDATED} historyHref={GIT_HISTORY_URL} sections={SECTIONS} activeId={activeId} onSection={scrollToHeading} progress={progress} articleRef={articleRef} copied={copied} onCopy={copyLink} onTop={scrollToTop} showTop={showTop}>
            <div className="blog-prose prose-headings:scroll-mt-20">
              <h2 id="acceptance">1. Acceptance of Terms</h2>
              <p>
                By accessing or using PrivaTools (<a href="https://privatools.me">privatools.me</a>),
                you agree to these Terms of Service. If you do not agree, do not use the service.
                PrivaTools is provided as a free, open-source tool suite and may be used without
                creating an account.
              </p>

              <h2 id="description">2. Description of Service</h2>
              <p>
                PrivaTools provides browser-based file processing tools for PDF, image, video, and
                developer workflows. Server-side tools use isolated temporary per-request storage and
                remove files after processing, with a background sweep for leftovers. Some tools run
                entirely in your browser with no server interaction. The service is free to use with
                fair-use limits, such as per-IP rate limits and a 500 MB request cap. The tools need no
                registration; the developer API has a free daily allowance.
              </p>
            </div>

            {/* Highlighted clause — Acceptable Use */}
            <section id="acceptable-use" className="my-10 scroll-mt-20">
              <h2 className="font-display font-bold text-[1.625rem] tracking-[-0.02em] leading-tight mt-10 mb-3 text-foreground">
                3. Acceptable Use
              </h2>
              <aside className="relative rounded-2xl border border-accent/30 bg-accent/[0.05] overflow-hidden">
                <div className="relative p-5 sm:p-6">

                  <p className="font-display text-[15.5px] text-foreground leading-relaxed mb-3">You agree not to:</p>
                  <ul className="font-display text-[15.5px] text-foreground leading-relaxed space-y-1.5 list-disc pl-6">
                    <li>Use the service to process files that violate applicable laws</li>
                    <li>Attempt to access, tamper with, or disrupt the server infrastructure</li>
                    <li>Use automated scripts to overload the service (reasonable API usage is fine)</li>
                    <li>Redistribute the service under a different name while claiming original authorship</li>
                  </ul>
                  <p className="font-display text-[15.5px] text-muted-foreground leading-relaxed mt-3">
                    The MIT license grants you full rights to fork, modify, and self-host the PrivaTools
                    codebase for any purpose.
                  </p>
                </div>
              </aside>
            </section>

            <div className="blog-prose prose-headings:scroll-mt-20">
              <h2 id="file-processing">4. File Processing</h2>
              <p>
                Files you upload are processed in isolated temporary per-request storage and deleted
                immediately after your result is delivered. We do not retain, inspect, or back up your files.
                See our <Link to="/privacy">Privacy Policy</Link> for full details on file handling.
              </p>
            </div>

            {/* Highlighted clauses — No Warranty + Limitation of Liability (the two clauses users actually need to see) */}
            <section id="no-warranty" className="my-10 scroll-mt-20">
              <h2 className="font-display font-bold text-[1.625rem] tracking-[-0.02em] leading-tight mt-10 mb-3 text-foreground">
                5. No Warranty
              </h2>
              <aside className="relative rounded-2xl border border-accent/30 bg-accent/[0.05] overflow-hidden">
                <div className="relative p-5 sm:p-6">

                  <p className="font-display text-[15.5px] text-foreground leading-relaxed">
                    PrivaTools is provided <strong>"as is"</strong> without warranty of any kind, express or
                    implied. We do not guarantee that the service will be uninterrupted, error-free, or that
                    processing results will be perfect for every file. You are responsible for verifying
                    output files meet your requirements before relying on them.
                  </p>
                </div>
              </aside>
            </section>

            <section id="liability" className="my-10 scroll-mt-20">
              <h2 className="font-display font-bold text-[1.625rem] tracking-[-0.02em] leading-tight mt-10 mb-3 text-foreground">
                6. Limitation of Liability
              </h2>
              <aside className="relative rounded-2xl border border-accent/30 bg-accent/[0.05] overflow-hidden">
                <div className="relative p-5 sm:p-6">

                  <p className="font-display text-[15.5px] text-foreground leading-relaxed">
                    To the maximum extent permitted by law, PrivaTools and its contributors shall not
                    be liable for any indirect, incidental, special, consequential, or punitive damages
                    arising from your use of the service, including but not limited to data loss, file
                    corruption, or service unavailability.
                  </p>
                </div>
              </aside>
            </section>

            <div className="blog-prose prose-headings:scroll-mt-20">
              <h2 id="intellectual-property">7. Intellectual Property</h2>
              <p>
                The PrivaTools codebase is open source under the{" "}
                <a href="https://opensource.org/licenses/MIT" target="_blank" rel="noopener noreferrer">
                  MIT License
                </a>
                . You retain all rights to the files you upload and the outputs you download. We claim
                no ownership or license over your content.
              </p>

              <h2 id="availability">8. Service Availability</h2>
              <p>
                We aim to keep PrivaTools available 24/7, but we do not guarantee uptime. The service
                may be temporarily unavailable due to maintenance, updates, or infrastructure issues.
                If the hosted service is unavailable, you can always self-host using the open-source
                codebase.
              </p>

              <h2 id="changes">9. Changes to Terms</h2>
              <p>
                We may update these terms at any time. Changes take effect when posted to this page
                with an updated "Last updated" date. Continued use of the service after changes
                constitutes acceptance. Every change is tracked in the public git history linked above.
              </p>

              <h2 id="contact">10. Contact</h2>
              <p>
                For questions about these terms, contact us at{" "}
                <a href="mailto:hello@privatools.me">hello@privatools.me</a> or open an issue on{" "}
                <a href="https://github.com/ethereaglehq/privatools/issues" target="_blank" rel="noopener noreferrer">
                  GitHub
                </a>.
              </p>
            </div>
  </DocumentStudio>;
}
