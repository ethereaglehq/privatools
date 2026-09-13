import { Link2 } from "lucide-react";
import { SimpleProcessUI } from "./SimpleProcessUI";

export function AddHyperlinksUI() {
    return (
        <SimpleProcessUI
            handoffSlug="add-hyperlinks"
            endpoint="/add-hyperlinks"
            accepts=".pdf"
            outputSuffix="linked"
            outputExt="pdf"
            dropIcon={Link2}
            dropTitle="Drop PDF to add hyperlinks"
            dropSubtitle="Auto-detect URLs · convert to clickable links"
            actionLabel="Add hyperlinks"
            processingLabel="Adding hyperlinks…"
            doneTitle="Hyperlinks added"
        />
    );
}
