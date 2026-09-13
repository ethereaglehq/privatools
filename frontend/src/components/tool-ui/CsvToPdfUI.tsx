import { FileSpreadsheet } from "lucide-react";
import { SimpleProcessUI } from "./SimpleProcessUI";

export function CsvToPdfUI() {
    return (
        <SimpleProcessUI
            handoffSlug="csv-to-pdf"
            endpoint="/csv-to-pdf"
            accepts=".csv"
            outputSuffix="converted"
            outputExt="pdf"
            dropIcon={FileSpreadsheet}
            dropTitle="Drop CSV to convert to PDF"
            dropSubtitle="Renders as a styled table — first row becomes header"
            actionLabel="Convert to PDF"
            processingLabel="Converting…"
            doneTitle="Converted to PDF"
        />
    );
}
