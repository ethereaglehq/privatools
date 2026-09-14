import { ArrowDownToLine, ArrowRight } from "lucide-react";
import "./api-starters.css";

export default function ApiStarters() {
    return <section className="pt-api-starters" aria-labelledby="api-starters-title">
        <header><div><span className="pt-workspace-caption">Take the next step</span><h2 id="api-starters-title">A working start for your workflow.</h2><p>Merge PDFs, compress a document, or extract text. These examples cover background jobs, checking progress, downloading, and deleting results.</p></div><a className="pt-studio-button" href="/api-starters/privatools-api-starters.zip" download><ArrowDownToLine size={16} aria-hidden="true" />Download starter kit</a></header>
        <div className="pt-starter-options">
            <article><span className="pt-workspace-caption">For your application</span><h3>Python & JavaScript</h3><p>Command-line clients with bounded retries, resume support, and deletion after a successful save. Supply your key through an environment variable.</p><div><a href="/api-starters/privatools.py" download>Python client <ArrowDownToLine size={14} aria-hidden="true" /></a><a href="/api-starters/privatools.mjs" download>Node.js client <ArrowDownToLine size={14} aria-hidden="true" /></a></div></article>
            <article><span className="pt-workspace-caption">For your automation</span><h3>n8n workflows</h3><p>Import a sample workflow, connect your header credential, and run it. The workflow returns a file for your next step and keeps the result available for one hour.</p><div><a href="/api-starters/n8n-merge.json" download>Merge <ArrowDownToLine size={14} aria-hidden="true" /></a><a href="/api-starters/n8n-compress.json" download>Compress <ArrowDownToLine size={14} aria-hidden="true" /></a><a href="/api-starters/n8n-pdf-to-text.json" download>Extract text <ArrowDownToLine size={14} aria-hidden="true" /></a></div></article>
            <article><span className="pt-workspace-caption">Explore each request</span><h3>Postman collection</h3><p>Inspect discovery, usage, conversion requests, and the background job lifecycle. Add your own key and select your local input files.</p><div><a href="/api-starters/privatools.postman_collection.json" download>Download collection <ArrowDownToLine size={14} aria-hidden="true" /></a></div></article>
        </div>
        <footer><a href="/api-starters/README.md">Read the setup guide <ArrowRight size={14} aria-hidden="true" /></a><a href="/account/keys">View your API activity <ArrowRight size={14} aria-hidden="true" /></a><p>All examples use the same free allowance. Store shared keys on your server or in your workflow’s credential store.</p></footer>
    </section>;
}
