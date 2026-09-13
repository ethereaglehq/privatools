import { Crop } from "lucide-react";
import { SimpleProcessUI } from "./SimpleProcessUI";

export function AutoCropUI() {
    return (
        <SimpleProcessUI
            handoffSlug="auto-crop"
            endpoint="/auto-crop"
            accepts=".pdf"
            outputSuffix="cropped"
            outputExt="pdf"
            dropIcon={Crop}
            dropTitle="Drop PDF to auto-crop margins"
            dropSubtitle="Detects whitespace borders and trims them"
            actionLabel="Auto-crop"
            processingLabel="Cropping…"
            doneTitle="Auto-cropped"
        />
    );
}
