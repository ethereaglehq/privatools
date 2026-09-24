/** Limits of POST /image-to-pdf (backend/app/routes/image_to_pdf.py), which
 *  Image, JPG, PNG, HEIC, WebP, TIFF, BMP, GIF and SVG to PDF share.
 *  backend/tests/test_image_to_pdf_route.py checks them against the route. */
export const IMAGE_TO_PDF_MAX_FILES = 100;
export const IMAGE_TO_PDF_MAX_TOTAL_MB = 200;
