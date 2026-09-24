import { withErrorKind } from "./api";
import { getToolEndpoint } from "./tool-endpoints";

/** Why a batch cannot run with these settings, tagged as bad input, or null when it can. */
export function batchConfigError(slug: string, query = ""): Error | null {
    if (slug === "highlight-pdf" && !query.trim()) {
        return withErrorKind(new Error("Enter the text to highlight before processing these PDFs."), "bad_input");
    }
    return null;
}

/** Alias pages and batch processing must ask the shared endpoint for the same format. */
export function batchRequestFields(slug: string, query = ""): Record<string, string> {
    const endpoint = getToolEndpoint(slug);
    const target = slug.split("-to-")[1];
    const format = target === "jpg" ? "jpeg" : target;
    if (endpoint === "/image-converter" && format) return { target_format: format };
    if (endpoint === "/pdf-to-image" && format && format !== "image") return { format };
    if (endpoint === "/video-converter" && format) return { target_format: format };
    if (endpoint === "/audio-converter" && format) return { format };
    if (slug === "mp4-to-mp3") return { format: "mp3" };
    if (slug === "highlight-pdf") return { query: query.trim() };
    return {};
}

export function buildBatchForm(slug: string, file: File, query = ""): FormData {
    const form = new FormData();
    form.append("file", file);
    form.append("files", file);
    for (const [key, value] of Object.entries(batchRequestFields(slug, query))) form.append(key, value);
    return form;
}
