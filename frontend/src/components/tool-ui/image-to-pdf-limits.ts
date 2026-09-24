/** Limits of POST /image-to-pdf (backend/app/routes/image_to_pdf.py and
 *  backend/app/services/image_to_pdf_service.py), which Image, JPG, PNG,
 *  HEIC, WebP, TIFF, BMP, GIF and SVG to PDF share.
 *  backend/tests/test_image_to_pdf_route.py checks them against the server. */
export const IMAGE_TO_PDF_MAX_FILES = 100;
export const IMAGE_TO_PDF_MAX_TOTAL_MB = 200;
/** Images other than JPEG are decoded on the server, which takes CPU time in
 *  proportion to their pixels, so one PDF may decode this many megapixels.
 *  A HEIC megapixel counts half. JPEGs are embedded as they are and don't
 *  count. The server enforces it; browsers can't read every format's size. */
export const IMAGE_TO_PDF_MAX_MEGAPIXELS = 750;
export const IMAGE_TO_PDF_MAX_HEIC_MEGAPIXELS = 1_500;

const count = `One PDF takes up to ${IMAGE_TO_PDF_MAX_FILES} images`;

/** The limits one tool's page states, by the tool's slug. */
export function imageToPdfLimits(slug: string): string {
    if (slug === "jpg-to-pdf") return `${count}, ${IMAGE_TO_PDF_MAX_TOTAL_MB} MB in total.`;
    if (slug === "heic-to-pdf") {
        return `${count}, ${IMAGE_TO_PDF_MAX_TOTAL_MB} MB and ${IMAGE_TO_PDF_MAX_HEIC_MEGAPIXELS.toLocaleString("en-US")} megapixels in total.`;
    }
    if (slug === "image-to-pdf") {
        return `${count}, ${IMAGE_TO_PDF_MAX_TOTAL_MB} MB in total. Images other than JPEG can add up to ${IMAGE_TO_PDF_MAX_MEGAPIXELS} megapixels, with HEIC photos counting half.`;
    }
    return `${count}, ${IMAGE_TO_PDF_MAX_TOTAL_MB} MB and ${IMAGE_TO_PDF_MAX_MEGAPIXELS} megapixels in total.`;
}
