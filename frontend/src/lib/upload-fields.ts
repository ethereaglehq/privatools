/**
 * The form field each backend route reads an upload from.
 *
 * Almost every tool route reads its upload either as `file: UploadFile` or as
 * `files: list[UploadFile]`; backend/tests/test_upload_fields.py names the
 * exceptions, whose pages build their own forms. The single-file helpers in
 * api.ts once appended the file under both names so one request suited either
 * kind, which sent every file twice and left one file only half of the 500 MB
 * request cap. They now send it once, under the name `uploadFieldFor` gives.
 *
 * FILES_FIELD_ROUTES lists the routes that read `files`; the helpers send
 * `file` to every other route. backend/tests/test_upload_fields.py compares
 * this list with the FastAPI app in both directions, so a route that starts or
 * stops reading `files` fails CI until the list agrees, instead of answering
 * 422 in production. Keep it a plain list of quoted paths, sorted, one per
 * line, without the /api prefix.
 */
export const FILES_FIELD_ROUTES: readonly string[] = [
    "/audio-merge",
    "/batch-compress-pdf",
    "/bates-numbering-batch",
    "/compress",
    "/create-zip",
    "/image-to-pdf",
    "/make-collage",
    "/merge",
    "/merge-images",
    "/pdf-page-counter",
    "/protect",
    "/remove-exif",
    "/strip-metadata",
    "/unlock",
    "/video-merge",
];

const READS_FILES = new Set(FILES_FIELD_ROUTES);

export type UploadField = "file" | "files";

/** The field `endpoint`'s route reads an upload from. Takes the endpoint in
 *  any form the api.ts helpers accept: "/compress", "/api/compress" or
 *  "compress". */
export function uploadFieldFor(endpoint: string): UploadField {
    let path = endpoint.split(/[?#]/, 1)[0];
    if (path.startsWith("/api/")) path = path.slice(4);
    else if (!path.startsWith("/")) path = `/${path}`;
    return READS_FILES.has(path) ? "files" : "file";
}
