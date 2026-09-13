import { FileCode } from "lucide-react";
import { SimpleProcessUI } from "./SimpleProcessUI";

export function MarkdownToPdfUI() {
    return (
        <SimpleProcessUI
            handoffSlug="markdown-to-pdf"
            endpoint="/markdown-to-pdf"
            accepts=".md,.markdown,.txt"
            outputSuffix="converted"
            outputExt="pdf"
            dropIcon={FileCode}
            dropTitle="Drop a Markdown file"
            dropSubtitle=".md or .markdown — converted to a styled PDF"
            actionLabel="Convert to PDF"
            processingLabel="Converting…"
            doneTitle="Converted to PDF"
        />
    );
}
