import { ShieldCheck } from "lucide-react";
import { SimpleProcessUI } from "./SimpleProcessUI";

export function SanitizeUI() {
    return (
        <SimpleProcessUI
            handoffSlug="sanitize-pdf"
            endpoint="/sanitize"
            accepts=".pdf"
            outputSuffix="sanitized"
            outputExt="pdf"
            dropIcon={ShieldCheck}
            dropTitle="Drop PDF to sanitize"
            dropSubtitle="Removes scripts, risky links, attachments and hidden layers"
            actionLabel="Sanitize PDF"
            processingLabel="Sanitizing…"
            doneTitle="Sanitized"
        />
    );
}
