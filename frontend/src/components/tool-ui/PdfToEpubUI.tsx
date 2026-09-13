import { BookOpen } from "lucide-react";
import { SimpleProcessUI } from "./SimpleProcessUI";

export function PdfToEpubUI() {
    return (
        <SimpleProcessUI
            handoffSlug="pdf-to-epub"
            endpoint="/pdf-to-epub"
            accepts=".pdf"
            outputSuffix="converted"
            outputExt="epub"
            dropIcon={BookOpen}
            dropTitle="Drop PDF to convert to EPUB"
            dropSubtitle="For ereaders — reflowable text + images"
            actionLabel="Convert to EPUB"
            processingLabel="Converting…"
            doneTitle="EPUB ready"
        />
    );
}
