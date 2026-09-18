"""
Structured HowTo steps and FAQ entries for each tool.

Used for:
- Server-side rendering (visible to crawlers)
- JSON-LD HowTo and FAQPage schema markup
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# HowTo steps  –  tool slug → list of {name, text}
# ---------------------------------------------------------------------------
TOOL_HOWTO: dict[str, list[dict[str, str]]] = {
    # ── PDF manipulation ──────────────────────────────────────────────
    "merge-pdf": [
        {"name": "Add the PDFs", "text": "Drop or select two or more PDF files, up to 500 MB each and up to 100 files at a time. The whole upload also has to fit within the same overall request limit, so several very large files may need to be merged in stages."},
        {"name": "Put them in order", "text": "Drag the file cards into the order the files should appear in the merged PDF."},
        {"name": "Choose the pages from each file", "text": "Select thumbnails, or type ranges for each file in the merge settings. Leave a file's field blank to include every page; 1-3,5 or 2-end includes just those pages, in the order you type them."},
        {"name": "Merge and download", "text": "Click merge. The server joins the files in the order shown and returns a single PDF."},
    ],
    "split-pdf": [
        {"name": "Add the PDF", "text": "Drop or select the PDF you want to divide, up to 500 MB."},
        {"name": "Choose how to split", "text": "By page ranges (the default) pulls the pages you list into one new PDF. Every page gives each page its own file. Every N pages cuts the document into equal chunks of the size you set."},
        {"name": "Enter pages or a chunk size", "text": "For page ranges, type something like 1-3, 5, 7-end. For every N pages, enter the number of pages per part; the last part holds whatever remains."},
        {"name": "Split and download", "text": "Run the split. Page ranges return a single PDF; the other two modes return a ZIP with one PDF per part."},
    ],
    "split-by-size": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB that is too large for an email, a portal or an upload form."},
        {"name": "Set the maximum part size", "text": "Enter the largest size each part may be, in megabytes, from 1 to 1024. The default is 10, which suits many email attachment limits."},
        {"name": "Split and download", "text": "Run it. The document is divided at page boundaries so each part stays under your limit, and the parts arrive in a ZIP."},
    ],
    "compress-pdf": [
        {"name": "Add your PDFs", "text": "Drop or select one or more PDFs, up to 500 MB each; each file is uploaded and compressed separately. Documents full of photos or scans shrink the most."},
        {"name": "Pick a compression level", "text": "Light keeps images closest to the original, Recommended (the default) balances size and quality, and Extreme gives the smallest file. Presets for Email and Print are there too."},
        {"name": "Or set it yourself", "text": "Custom lets you choose the JPEG quality and the maximum image dimension directly, when none of the presets fits."},
        {"name": "Compress and download", "text": "Run it and compare the new size with the original. One file downloads directly; several come back together."},
    ],
    "edit-pdf": [
        {"name": "Open the PDF", "text": "Drop or select a PDF up to 500 MB. Each page is shown in the editor, ready for you to add to it."},
        {"name": "Choose a tool", "text": "Pick text, highlight, freehand pen, rectangle, circle, line, arrow, whiteout or image from the toolbar."},
        {"name": "Add your changes", "text": "Click to place text, drag to draw shapes, or cover an area with whiteout. Adjust or remove items before you save."},
        {"name": "Save the edited PDF", "text": "Save and download. Your additions are drawn onto the pages, so they look the same in every PDF reader."},
    ],
    "sign-pdf": [
        {"name": "Add the PDF", "text": "Drop or select the document you need to sign, up to 500 MB."},
        {"name": "Create your signature", "text": "Draw it with a mouse, trackpad or finger, or upload an image of your handwritten signature."},
        {"name": "Place it on the page", "text": "Choose the page and set the position and size. The fields give exact values, so a signature can line up precisely with a signature line."},
        {"name": "Apply and download", "text": "Apply the signature and save the signed PDF. The signature image becomes part of the page."},
    ],
    "protect-pdf": [
        {"name": "Drop your PDF", "text": "Select a PDF up to 500 MB that you want to password-protect. The file is uploaded over HTTPS and processed in isolated temporary per-request storage."},
        {"name": "Choose your password", "text": "Enter a strong password (12+ characters, mixed case, numbers, symbols recommended). Save it in a password manager — there is no recovery."},
        {"name": "Set permission restrictions", "text": "Optionally change the three switches: Print (on by default), Extract for copying text and images (off by default), and Modify for editing, comments, form filling and page assembly (off by default)."},
        {"name": "Download the encrypted PDF", "text": "Click Protect. The output uses AES-256 encryption and requires your password to open in any PDF reader."},
    ],
    "unlock-pdf": [
        {"name": "Add the locked PDFs", "text": "Drop or select one or more password-protected PDFs, up to 100 at a time and 500 MB each."},
        {"name": "Enter the password", "text": "Type the existing password. It must be correct: this tool removes protection you already have the key to, it does not guess or crack passwords."},
        {"name": "Unlock and download", "text": "Run it. The result opens without a password, and restrictions such as no-print or no-copy are removed as well."},
    ],
    "rotate-pdf": [
        {"name": "Drop your PDF", "text": "Select one or more PDFs, up to 500 MB each. The same rotation is applied to each file."},
        {"name": "Select pages to rotate", "text": "Keep All pages, or choose Specific pages and type them, such as 1,3,5-8. One run applies one angle; to turn different pages by different amounts, run it again on the result."},
        {"name": "Choose the rotation angle", "text": "Pick 90° clockwise, 180° (upside-down), or 270° clockwise (equivalent to 90° counter-clockwise). PDF only allows 90° increments."},
        {"name": "Apply and download", "text": "Click Rotate. The server applies the rotation permanently (not just a viewer toggle) and returns the updated PDF — orientation sticks in every reader."},
    ],
    "watermark": [
        {"name": "Add the PDF", "text": "Drop or select the PDF you want to mark, up to 500 MB."},
        {"name": "Choose text or an image", "text": "Type a word such as CONFIDENTIAL or DRAFT, or upload an image such as a logo."},
        {"name": "Set the look", "text": "Adjust the opacity and the font size for text, or the scale for an image. A lighter watermark keeps the document readable."},
        {"name": "Pick a position", "text": "Place it in the centre, at the top or bottom, in any corner, diagonally across the page, or tiled across the whole page."},
        {"name": "Apply and download", "text": "Apply the watermark and save the marked PDF. It is added to every page."},
    ],
    "ocr-pdf": [
        {"name": "Upload a scanned PDF or image-based PDF", "text": "Select a PDF containing scanned pages. Files up to 500 MB are supported."},
        {"name": "Select the document language", "text": "Pick the document's main language from the list so Tesseract uses the right language data. The server engine has 17 language packs; languages marked as not installed can be read with the In this browser engine instead."},
        {"name": "Run OCR and download", "text": "Choose an output (Show text, Download .txt or Searchable PDF) and click Run OCR. For a searchable PDF, Tesseract adds an invisible text layer to each page image so the PDF can be searched and copied."},
    ],
    "redact-pdf": [
        {"name": "Upload the PDF", "text": "Select the document containing sensitive information you need to permanently remove."},
        {"name": "Mark areas to redact", "text": "Draw rectangles over text, images, or regions on the page preview, or add a box and type its position. Pick the box colour (black by default) and, if you need them, an exemption code set whose code is printed inside each box. To find every occurrence of a word automatically, use Smart Redact."},
        {"name": "Preview the redactions", "text": "The page preview shows every box in place; step through the pages to check them before committing."},
        {"name": "Apply redactions and download", "text": "Click Redact. The underlying content is permanently destroyed — it cannot be recovered, even by removing the black boxes."},
    ],
    "flatten-pdf": [
        {"name": "Upload the PDF", "text": "Select one or more filled PDF forms, up to 500 MB each. A PDF that contains comments, highlights or other annotations currently fails with an error."},
        {"name": "Let it lock the fields", "text": "There are no options. Every form field is set to read-only; the fields and their values stay in the file, and links and layers are left as they are."},
        {"name": "Download the flattened PDF", "text": "Click Flatten and download. The values show as before, but a PDF reader will not let anyone edit the fields; because the fields are still in the file, a PDF editor can clear the read-only setting."},
    ],
    "bookmarks": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB. Existing bookmarks are not loaded, and saving replaces them, so include any you want to keep."},
        {"name": "Edit the bookmark tree", "text": "Add, rename, or delete rows, giving each bookmark a title and a target page. Or switch to the JSON view and paste an array of entries with a title and a page. Bookmarks are saved in list order, all on one level."},
        {"name": "Save and download", "text": "Click Save. The bookmarks are written into the PDF as its outline for easy navigation in any reader; a page number past the end points to the last page."},
    ],
    "form-creator": [
        {"name": "Upload a PDF", "text": "Upload the PDF you want to add form fields to. The fields are placed on top of its existing pages, and its bookmarks, links and comments are kept."},
        {"name": "Add form fields", "text": "Click Draw a field and drag a box on the page preview, or click Add and type the page, X, Y, width and height in points from the top-left corner. Give each field a name and choose its type: text, checkbox, dropdown, list or signature."},
        {"name": "Configure form properties", "text": "Set default values, mark fields as required, allow several lines in a text field, pre-tick checkboxes, and type the options for dropdowns and lists, separated by commas."},
        {"name": "Export the fillable PDF", "text": "Click Generate fillable PDF. The download contains standard AcroForm fields, the interactive form format PDF readers use; test it in the reader your recipients use."},
    ],
    "extract-tables": [
        {"name": "Upload the PDF", "text": "Select a PDF that contains one or more tables you need to extract as structured data."},
        {"name": "Extract the tables", "text": "Click Extract Tables. Every page is checked with PyMuPDF table detection, which finds tables drawn with ruled lines; there is no page selection on this page."},
        {"name": "Check the CSV", "text": "All detected tables go into one CSV file in page order, with a blank row between tables. Cells that start with =, +, - or @ get a leading apostrophe so spreadsheet apps do not run them as formulas; this includes negative numbers."},
        {"name": "Download the extracted data", "text": "For one PDF, the CSV downloads automatically, named after your PDF. For several PDFs, download each CSV or all of them as one ZIP."},
    ],
    "pdf-to-pdfa": [
        {"name": "Upload the PDF", "text": "Select the PDF you want to prepare for archiving. You can queue up to 25 files; each one is processed separately."},
        {"name": "Convert", "text": "Click Convert to PDF/A. There is no conformance level to choose: every file is marked PDF/A-2b."},
        {"name": "Download and check", "text": "Download the result. The tool re-saves the file and adds PDF/A-2b identification metadata, but it does not embed fonts, convert colours or validate compliance, so check it with a dedicated PDF/A validator if an archive requires strict PDF/A."},
    ],

    # ── PDF conversion ────────────────────────────────────────────────
    "image-to-pdf": [
        {"name": "Upload images", "text": "Select one or more images (JPG, PNG, WebP, BMP, TIFF, GIF, HEIC, or SVG). One PDF can take up to 50 images with a combined size of up to 200 MB."},
        {"name": "Arrange and configure", "text": "Reorder images by dragging thumbnails or with the arrow buttons. Choose Auto (the default), which makes each page the size of its image, or A4 or Letter, which fit each image on a portrait page with a half-inch margin."},
        {"name": "Convert to PDF", "text": "Click Convert. Each image becomes a full page in the resulting PDF, maintaining original resolution."},
    ],
    "txt-to-pdf": [
        {"name": "Upload a text file", "text": "Select one or more .txt files, up to 500 MB each; each file becomes its own PDF. Save the text as UTF-8 so accented characters come through."},
        {"name": "Know the fixed layout", "text": "There are no formatting options: text is set in 11 pt Courier on A4 pages with 1-inch margins, and long lines wrap at spaces. Runs of spaces and tabs collapse to a single space, so indentation and space-aligned columns are not kept, and a single word longer than a line runs off the page."},
        {"name": "Generate the PDF", "text": "Click Convert. The text is wrapped and paginated automatically into a PDF for you to download."},
    ],
    "office-to-pdf": [
        {"name": "Upload an Office document", "text": "Select a Word (.docx), Excel (.xlsx), or PowerPoint (.pptx) file up to 500 MB."},
        {"name": "Convert via LibreOffice", "text": "The server converts the file with LibreOffice in headless mode, keeping tables, charts, and layout. Fonts the server does not have are replaced with similar ones, which can shift line and page breaks."},
        {"name": "Download the PDF", "text": "Click Convert. Each file becomes its own PDF; queue up to 25 files and they are converted one after another, with an option to download them all as a ZIP."},
    ],
    "word-to-pdf": [
        {"name": "Add the Word document", "text": "Drop or select a .docx file up to 500 MB. Older .doc files are not accepted here; Office to PDF handles a wider range of formats."},
        {"name": "Convert to PDF", "text": "Run the conversion. The text of each paragraph is set in Helvetica on A4 pages with 1-inch margins, and headings become larger bold text. Images, tables, headers, footers and links are left out."},
        {"name": "Download and check the PDF", "text": "Open the PDF and check it: everything is set in one typeface, and any text that was in tables, text boxes, headers or footers is missing."},
    ],
    "epub-to-pdf": [
        {"name": "Upload an EPUB file", "text": "Select an .epub e-book file up to 500 MB."},
        {"name": "Know what is kept", "text": "There are no layout options: the text of each chapter is set in 11 pt Helvetica on A4 pages as one running paragraph. Images, headings, bold and italic, and paragraph breaks are not kept, and characters outside Western European scripts print as black boxes."},
        {"name": "Convert and download", "text": "Click Convert. Chapters follow the order of their file names inside the EPUB, which is not always the reading order, so check the result."},
    ],
    "html-to-pdf": [
        {"name": "Enter a URL or paste HTML", "text": "Type a public URL to render, or paste raw HTML/CSS directly into the editor."},
        {"name": "Know what gets rendered", "text": "There are no page, margin, or background settings. Pasted HTML is laid out on A4 pages unless its CSS sets a page size, and stylesheets and images linked by full http(s) addresses are fetched. A web address is fetched as HTML only and laid out on A4 pages without its external stylesheets or images. JavaScript is not run in either mode."},
        {"name": "Generate the PDF", "text": "Click Convert to PDF. The server renders pasted HTML with WeasyPrint and a fetched page with PyMuPDF, then the PDF downloads."},
    ],
    "xml-to-pdf": [
        {"name": "Upload an XML file", "text": "Select one or more .xml files of up to 5 MB each; each file becomes its own PDF. Any well-formed UTF-8 XML works, including RSS, Atom, and XHTML."},
        {"name": "Know the fixed layout", "text": "There are no view options: the XML is re-indented with two spaces per level in 9 pt Courier on A4 pages, with lines that contain tags in blue and text-only lines in black. A line too long for the page is cut off at the right margin, and the rest of it is not printed."},
        {"name": "Convert and download", "text": "Click Convert. The XML is rendered into a readable, paginated PDF document."},
    ],
    "csv-to-pdf": [
        {"name": "Upload a CSV file", "text": "Select a comma-separated .csv file up to 500 MB. The first row always becomes the column header."},
        {"name": "Check the table width", "text": "There are no layout settings: the table is drawn on portrait A4 pages in 9 pt text with striped rows. Columns that do not fit across the page are cut off rather than wrapped or moved to another page, so trim wide files first."},
        {"name": "Convert to PDF", "text": "Click Convert. The data is rendered into a clean, paginated table in the output PDF."},
    ],
    "json-to-pdf": [
        {"name": "Upload a JSON file", "text": "Select one or more .json files of up to 5 MB each; each file becomes its own PDF. The JSON must be valid UTF-8 and nest no more than 25 levels deep."},
        {"name": "Know the fixed layout", "text": "There are no view options: the JSON is pretty-printed with two-space indentation in 9 pt Courier on A4 pages, with keys in bold blue and values in black. Lines are not wrapped, so very long values run off the right edge of the page."},
        {"name": "Convert and download", "text": "Click Convert. The JSON is rendered into a paginated, readable PDF with proper indentation."},
    ],
    "pdf-to-word": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB. Documents created digitally, with real text rather than scanned images, convert best."},
        {"name": "Convert to Word", "text": "Run the conversion. The text is read page by page and rebuilt as Word paragraphs, keeping font names, text colours and paragraph spacing where the PDF provides them."},
        {"name": "Download and review the .docx", "text": "Open the result in Word or another editor and check the layout, especially tables, columns and headers, before relying on it."},
    ],
    "pdf-to-excel": [
        {"name": "Drop your PDF", "text": "Select one or more PDFs up to 500 MB each that contain tables or tabular data. A scanned PDF needs OCR first via the OCR PDF tool, and even then gives its text rather than rebuilt tables."},
        {"name": "Convert", "text": "Click Convert. Every page is checked with PyMuPDF table detection, which finds tables drawn with ruled lines. There is no page selection or detection setting."},
        {"name": "Check each sheet", "text": "The workbook has one sheet per page, named Page 1, Page 2 and so on. A page with tables gets only its table rows, with a blank row between tables; a page without a table gets its text, one line per row in column A."},
        {"name": "Download the workbook", "text": "The .xlsx file downloads automatically, with the rows and columns of each detected table kept. Several PDFs download together as a ZIP. Cell values arrive as text, so convert number columns before doing sums."},
    ],
    "pdf-to-text": [
        {"name": "Upload the PDF", "text": "Select one or more text-based PDFs up to 500 MB each."},
        {"name": "Extract the text", "text": "Click Extract text. The text is read from the PDF text layer; there is no OCR here, so a scanned page comes back empty with a suggestion to run OCR PDF first."},
        {"name": "Download the text", "text": "For one PDF, the text appears with word, character and line counts; copy it or download it as a .txt file. Several PDFs download as a ZIP with one .txt per PDF. Pages are separated by a blank line."},
    ],
    "pdf-to-image": [
        {"name": "Upload the PDF", "text": "Select one or more PDFs up to 500 MB each. The queue lists each file with its size."},
        {"name": "Configure output settings", "text": "Choose the image format (JPG, the default, or PNG) and the resolution: 72, 150 (the default) or 300 DPI. Every page is converted; there is no page selection."},
        {"name": "Convert and download", "text": "Click Convert. Each page becomes a separate image file: a multi-page PDF downloads as a ZIP of images and a one-page PDF as a single image. Several PDFs arrive together in one ZIP."},
    ],

    # ── Image tools ───────────────────────────────────────────────────
    "heic-to-jpg": [
        {"name": "Add your HEIC photos", "text": "Drop or select .heic or .heif files, the format iPhones save by default, up to 500 MB each. You can add several at once; they are processed a few at a time and a batch comes back as one ZIP."},
        {"name": "Choose the quality", "text": "Pick High (95) for the most detail, Standard (85, the default) for a good balance, or Compressed (70) for noticeably smaller files."},
        {"name": "Convert and download", "text": "Run the conversion. A single photo downloads on its own; a batch is offered as one ZIP, and the JPGs open in any application, including older software that refuses HEIC."},
    ],
    "remove-exif": [
        {"name": "Add the images to clean", "text": "Drop or select up to 100 pictures at once. JPG, PNG, WebP, BMP and TIFF are all handled, and each keeps its original format."},
        {"name": "Strip the metadata", "text": "Run it. The EXIF block is cleared and the image is written out again, which removes camera model, capture time and any GPS coordinates recorded by the device."},
        {"name": "Download the cleaned images", "text": "One image comes back on its own, named with clean_ in front of the original name; several arrive as a ZIP that keeps each original filename."},
    ],
    "image-compressor": [
        {"name": "Add the images to shrink", "text": "Drop or select your pictures, up to 500 MB each. You can add several at once; they are processed a few at a time and a batch comes back as one ZIP."},
        {"name": "Set the quality", "text": "Choose a quality value between 1 and 95; the default is 82. It applies to JPG and WebP, where lower values give smaller files with more visible artefacts. PNGs ignore it and are re-saved with lossless optimisation instead."},
        {"name": "Compress and compare", "text": "Run the compression and check the reported size against the original before you commit to the result. If it looks over-compressed, raise the quality and run it again."},
        {"name": "Download the smaller files", "text": "One image downloads on its own; a batch is offered as a single ZIP built in your browser."},
    ],
    "remove-background": [
        {"name": "Add the images", "text": "Drop or select JPG, PNG or WebP pictures. Photos with a clear subject and a reasonably distinct background give the best results. You can add several at once; they are processed a few at a time and a batch comes back as one ZIP."},
        {"name": "Choose where the model runs", "text": "The server engine is the default: it runs a compact U-2-Net model on the PrivaTools server with nothing to download. The in-browser engine downloads the same small model once, around four and a half megabytes plus its runtime, and then works on your device."},
        {"name": "Cut out the subject", "text": "Run it. The model estimates which pixels belong to the subject and makes the rest transparent."},
        {"name": "Check the edges", "text": "Look closely at hair, fur, thin objects and anything semi-transparent, which are the hardest cases for any automatic cut-out. A busy or low-contrast background is where mistakes appear."},
        {"name": "Download the PNG", "text": "Save the result. It is a PNG, because the transparency that replaces the background needs a format that can store it."},
    ],

    # ── Video/media tools ─────────────────────────────────────────────
    "video-to-gif": [
        {"name": "Add a short video", "text": "Drop or select a video up to 200 MB — this tool's limit is lower than the site-wide one. Trim long footage first with Trim Media; GIFs are only practical for a few seconds."},
        {"name": "Set the frame rate", "text": "Choose how many frames per second the GIF keeps; the default is 10. Higher rates are smoother but make the file much larger."},
        {"name": "Set the width", "text": "Choose the width in pixels, from 120 up to 1920; the default is 480. The height follows automatically so the picture keeps its proportions."},
        {"name": "Convert and download", "text": "Create the GIF and save it. It loops, and it has no sound."},
    ],
    "compress-video": [
        {"name": "Upload a video", "text": "Select an MP4, WebM, MOV, or AVI file up to 500 MB."},
        {"name": "Choose compression preset", "text": "Pick Keep detail, Balanced (the default) or Small file, or set the compression level (CRF) anywhere from 18 to 40. Higher numbers make smaller files but lower the visual quality."},
        {"name": "Compress and download", "text": "Run it. The server re-encodes each video as H.264 in an MP4 using FFmpeg, and each result shows its new file size."},
    ],
    "trim-media": [
        {"name": "Upload an audio or video file", "text": "Select an MP4, MP3, WAV, WebM, or other media file up to 200 MB."},
        {"name": "Set the trim range", "text": "Play or scrub the preview, then set the start and end with the sliders or the playhead buttons, or type timestamps in HH:MM:SS form (e.g. 00:00:30 to 00:02:15)."},
        {"name": "Trim and download", "text": "Run the trim. Audio files are cut without re-encoding (FLAC is rewritten losslessly); video is re-encoded, sound included, so the cut starts on the exact frame you chose."},
    ],

    # ── Developer tools ───────────────────────────────────────────────
    "base64": [
        {"name": "Choose encode or decode mode", "text": "Select whether you want to encode data to Base64 or decode a Base64 string back to its original form."},
        {"name": "Enter input", "text": "Paste text into the editor; any language works, because text is encoded as UTF-8. For decoding, paste the Base64 string."},
        {"name": "Get the result", "text": "The output appears instantly. Copy it to your clipboard, or use Swap sides to run it back the other way."},
    ],
    "text-diff": [
        {"name": "Enter the two texts", "text": "Paste the original text on the left and the modified text on the right."},
        {"name": "View the diff", "text": "Added lines are marked + and removed lines −, each in its own colour; a changed line shows as one removal and one addition."},
        {"name": "Choose diff mode", "text": "Switch between side-by-side and unified views. Line numbers help locate changes in large documents."},
        {"name": "Swap or start again", "text": "Swap A and B to compare in the other direction, or clear the diff and paste new text."},
    ],
    "image-upscaler": [
        {"name": "Add the image to enlarge", "text": "Drop or select pictures up to 500 MB each. Small, reasonably sharp images give the best results; a heavily compressed thumbnail simply becomes a larger heavily compressed thumbnail."},
        {"name": "Choose 2x or 4x", "text": "Pick how much to enlarge. Those are the only two options, and 4x on an already large photo can exceed the server's pixel limit, in which case the request is rejected and 2x is the way forward."},
        {"name": "Upscale and download", "text": "Run it and save the result. The output has two or four times the width and height of your original."},
    ],
    "audio-converter": [
        {"name": "Add the audio file", "text": "Drop or select an audio file up to 200 MB."},
        {"name": "Choose the output format", "text": "Pick MP3, AAC, OGG, FLAC or WAV. MP3 is the most widely compatible; FLAC and WAV are lossless."},
        {"name": "Choose a bitrate", "text": "For MP3, AAC and OGG choose from 64 to 320 kbps; the default is 192. Higher bitrates keep more detail and make bigger files. WAV and FLAC are lossless, so the bitrate does not apply."},
        {"name": "Convert and download", "text": "Run the conversion and save the new file."},
    ],

    # ── v1.1.0 + v1.2.0 additions ─────────────────────────────────────────
    "highlight-pdf": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB containing the text you want to highlight."},
        {"name": "Enter your search phrase", "text": "Type the word or phrase to highlight. Matching ignores capitalisation, so invoice also finds Invoice and INVOICE; the Case sensitive switch does not change this at present."},
        {"name": "Pick a highlight color", "text": "Choose yellow, green, pink, blue, or orange. Highlights are added as real PDF annotations."},
        {"name": "Download the highlighted PDF", "text": "Click Highlight. The tool finds every occurrence on every page and writes a new PDF with a highlight annotation over each match."},
    ],
    "transcribe-audio": [
        {"name": "Add a recording", "text": "Select an audio file up to 500 MB, such as a voice memo, a meeting recording or an interview."},
        {"name": "Choose where it runs", "text": "On this device uses Whisper in your browser: Tiny, about 41 MB, is faster, and Base, about 74 MB, is more accurate. The model downloads once and is cached. With your own API key, the audio goes to your chosen provider instead."},
        {"name": "Transcribe", "text": "Start the transcription. On-device speed depends on your computer, so a long recording can take a while."},
        {"name": "Export the text", "text": "Copy the transcript, download it as a .txt file, or download timed subtitles as .srt."},
    ],
    "chat-with-pdf": [
        {"name": "Open your PDF", "text": "Select a text-based PDF. Its text is extracted in your browser; a scanned PDF needs OCR PDF first, because there is no text to read."},
        {"name": "Connect your AI provider", "text": "Choose a provider and paste your API key once. Supported options include Anthropic, OpenAI, Google Gemini, OpenRouter, Groq, Together AI, Mistral, DeepSeek, or a local or self-hosted OpenAI-compatible server."},
        {"name": "Ask your question", "text": "Type a question about the document. The question and the document's text go from your browser directly to the provider you chose."},
        {"name": "Read and follow up", "text": "Read the answer and ask follow-ups. Check anything important against the document itself."},
    ],
    "summarize-pdf": [
        {"name": "Choose your PDF", "text": "Select a text-based PDF. The text is read page by page in your browser with pdf.js; a scanned PDF has no text layer, so run OCR PDF on it first."},
        {"name": "Decide where the model runs", "text": "'On this device' (the default) downloads a DistilBART model of about 250 MB once, caches it in this browser and then works offline. 'My own API key' sends the extracted text from your browser straight to the AI provider you configured, billed to your account."},
        {"name": "Pick a summary length", "text": "Choose Short, Medium or Long (Medium is the default). On this device the setting controls how much is written for each chunk of the document, so a long PDF still produces a longer summary than a short one; with your own API key it sets the length of the whole summary."},
        {"name": "Run the summary", "text": "Start the run and watch the progress readout. On this device the text is split into chunks of roughly 600 words at sentence boundaries and summarized chunk by chunk; longer documents get a second pass that condenses the partial summaries."},
        {"name": "Copy or download the summary", "text": "The summary appears on the page. Copy it to the clipboard or download it as a .txt file named after your PDF."},
    ],
    "smart-redact": [
        {"name": "Choose a text-based PDF", "text": "Select a PDF up to 500 MB. The text is extracted in your browser; a scanned PDF needs OCR PDF first because there is no text to scan."},
        {"name": "Pick the detection engine", "text": "'On this device' (the default) downloads a BERT NER model of about 110 MB once and finds names, organisations and locations locally. 'My own API key' sends the extracted text to the AI provider you configured instead, with anything the pattern pass already found masked first."},
        {"name": "Let the scan finish", "text": "Pattern matching finds emails, phone numbers, SSN-style numbers, card-length digit runs and dates in your browser, then the chosen engine adds people, organisations and locations."},
        {"name": "Review every suggestion", "text": "Detections are grouped by type. Untick anything that should stay visible; only the strings you leave selected are redacted."},
        {"name": "Apply and download", "text": "Click the Redact button. The PDF and your approved strings are uploaded to the PrivaTools server, which removes the matching text with PyMuPDF redactions and returns the redacted PDF."},
    ],
    "split-in-half": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB, typically a scan where two book or magazine pages were captured on each sheet."},
        {"name": "Choose the cut direction", "text": "Vertical cut (the default) turns each page into its left half followed by its right half. Horizontal cut turns each page into its top half followed by its bottom half."},
        {"name": "Split and download", "text": "Run it and save the new PDF, which has twice as many pages as the original."},
    ],
    "pdf-to-svg": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB. Best results come from vector PDFs."},
        {"name": "Convert and download", "text": "Click Convert. Each page is converted to SVG with PyMuPDF. A multi-page PDF comes back as a ZIP with one SVG per page; a one-page PDF as a single SVG, which currently downloads with a .zip name, so rename it to .svg."},
    ],
    "pdf-to-html": [
        {"name": "Upload the PDF", "text": "Select one or more PDFs up to 500 MB each. Each page is exported with PyMuPDF's HTML exporter, which keeps the text, images and font styles."},
        {"name": "Download the HTML", "text": "Click Convert. The result is a single self-contained HTML file with inline styles — open it in any browser without needing the PDF."},
    ],
    "pdf-to-rtf": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB."},
        {"name": "Download the RTF", "text": "Click Convert. The RTF file opens in WordPad, Microsoft Word, Pages, LibreOffice, and any other RTF-aware editor. Unicode is preserved via RTF escape sequences."},
    ],
    "web-optimize-pdf": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB that you serve over the web or via a CDN."},
        {"name": "Linearize and download", "text": "Click Optimize. qpdf reorganizes the file structure so the first page renders before the whole document downloads — perfect for inline embeds and CDN-hosted PDFs."},
    ],
    "split-by-text": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB that has a text layer, such as a batch of invoices or statements exported from software."},
        {"name": "Enter the text that starts each part", "text": "Type a word or phrase that appears on the first page of every section, for example Invoice Number or Statement Date."},
        {"name": "Choose case matching", "text": "Matching ignores capitalisation by default. Turn on case-sensitive matching when the phrase also appears in lower case elsewhere and you want only the exact form."},
        {"name": "Split and download", "text": "Run it. A new part begins at each page where the text is found, and the parts arrive in a ZIP."},
    ],
    "view-exif": [
        {"name": "Add the photo", "text": "Drop or select an image up to 500 MB. Photos straight from a camera or phone carry the most metadata; anything already processed by a social platform has usually had it stripped."},
        {"name": "Read what it carries", "text": "The metadata is listed for you: camera and lens, exposure settings, the capture timestamp and, where the device recorded it, GPS coordinates."},
        {"name": "Decide what to do next", "text": "If the image is going to be published and the metadata should not, run Remove EXIF on the original to write a clean copy."},
    ],
    "jwt-decoder": [
        {"name": "Paste the token", "text": "Paste a JSON Web Token: three base64url parts separated by dots, header.payload.signature."},
        {"name": "Read the header and claims", "text": "The header and payload are decoded to readable JSON, and time claims such as exp and iat are shown as dates, with a clear indication when the token has expired."},
        {"name": "Copy what you need", "text": "Copy the decoded parts for a bug report or a test. The decoding happens on this page; the token is not uploaded to PrivaTools."},
    ],
    "regex-tester": [
        {"name": "Enter your regex pattern", "text": "Type the pattern. JavaScript RegExp syntax (same as in MDN docs)."},
        {"name": "Set flags", "text": "Combine g (global), i (case-insensitive), m (multiline), s (dotall), u (unicode), y (sticky)."},
        {"name": "Paste test text", "text": "Drop the text to match against. Matches highlight in real time as you edit either field."},
        {"name": "Read match details", "text": "Each match is listed with its offset, captured groups, and matched substring."},
    ],
    "timestamp-converter": [
        {"name": "Paste a timestamp", "text": "Enter a Unix epoch (seconds or milliseconds — auto-detected) or an ISO 8601 date string. Click Now to insert the current time."},
        {"name": "Read all formats side-by-side", "text": "The tool displays Unix seconds, Unix milliseconds, ISO 8601 (UTC), UTC string, local timezone, and a relative phrase ('in 3 hours', '2 days ago')."},
        {"name": "Copy what you need", "text": "Click Copy on any row. Useful for filling Cron entries, debugging API timestamps, or formatting logs."},
    ],
    "batch-compress-pdf": [
        {"name": "Upload multiple PDFs", "text": "Drag 2 to 50 PDF files. They go up in one request, so together they can be up to 500 MB."},
        {"name": "Know what it does", "text": "There is no level to pick. Each PDF is rewritten without unused objects and with its streams compressed. Images are not downsampled or re-encoded, so photo-heavy files shrink little; use Compress PDF for image compression levels."},
        {"name": "Compress and download as ZIP", "text": "Click Compress. Files are processed in parallel, up to four at a time, and the results come back in one ZIP, in upload order."},
    ],
    "pdf-page-counter": [
        {"name": "Upload up to 100 PDFs", "text": "Drag up to 100 PDF files, 500 MB in total. They are uploaded together, and the server reads each file's page count without rendering any pages, so the counts come back quickly once the upload finishes."},
        {"name": "Read the per-file count", "text": "Each filename appears with its page count, and the total across all files appears above the list — ideal for print quotes. Files that cannot be read are marked invalid and left out of the total."},
    ],
    "webp-to-jpg": [
        {"name": "Add your WebP images", "text": "Drop or select .webp files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to JPG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to JPG, so the conversion starts straight away."},
        {"name": "Download the JPG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new JPG rather than a renamed copy."},
    ],
    "webp-to-png": [
        {"name": "Add your WebP images", "text": "Drop or select .webp files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to PNG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to PNG, so the conversion starts straight away."},
        {"name": "Download the PNG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new PNG rather than a renamed copy."},
    ],
    "heic-to-png": [
        {"name": "Add your HEIC photos", "text": "Drop or select .heic or .heif files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to PNG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to PNG, so the conversion starts straight away."},
        {"name": "Download the PNG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new PNG rather than a renamed copy."},
    ],

    # ── v1.4.0 — additional format converter aliases ─────────────────────
    "jpg-to-png": [
        {"name": "Add your JPG images", "text": "Drop or select .jpg or .jpeg files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to PNG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to PNG, so the conversion starts straight away."},
        {"name": "Download the PNG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new PNG rather than a renamed copy."},
    ],
    "png-to-jpg": [
        {"name": "Add your PNG images", "text": "Drop or select .png files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to JPG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to JPG, so the conversion starts straight away."},
        {"name": "Download the JPG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new JPG rather than a renamed copy."},
    ],
    "jpg-to-webp": [
        {"name": "Add your JPG images", "text": "Drop or select .jpg or .jpeg files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to WebP", "text": "Click the convert button. There are no settings to choose: the output format is fixed to WebP, so the conversion starts straight away."},
        {"name": "Download the WebP", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new WebP rather than a renamed copy."},
    ],
    "png-to-webp": [
        {"name": "Add your PNG images", "text": "Drop or select .png files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to WebP", "text": "Click the convert button. There are no settings to choose: the output format is fixed to WebP, so the conversion starts straight away."},
        {"name": "Download the WebP", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new WebP rather than a renamed copy."},
    ],
    "tiff-to-jpg": [
        {"name": "Add your TIFF images", "text": "Drop or select .tif or .tiff files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to JPG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to JPG, so the conversion starts straight away."},
        {"name": "Download the JPG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new JPG rather than a renamed copy."},
    ],
    "tiff-to-png": [
        {"name": "Add your TIFF images", "text": "Drop or select .tif or .tiff files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to PNG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to PNG, so the conversion starts straight away."},
        {"name": "Download the PNG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new PNG rather than a renamed copy."},
    ],
    "bmp-to-jpg": [
        {"name": "Add your BMP images", "text": "Drop or select .bmp files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to JPG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to JPG, so the conversion starts straight away."},
        {"name": "Download the JPG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new JPG rather than a renamed copy."},
    ],
    "bmp-to-png": [
        {"name": "Add your BMP images", "text": "Drop or select .bmp files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to PNG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to PNG, so the conversion starts straight away."},
        {"name": "Download the PNG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new PNG rather than a renamed copy."},
    ],
    "gif-to-jpg": [
        {"name": "Add your GIF images", "text": "Drop or select .gif files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to JPG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to JPG, so the conversion starts straight away."},
        {"name": "Download the JPG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new JPG rather than a renamed copy."},
    ],
    "gif-to-png": [
        {"name": "Add your GIF images", "text": "Drop or select .gif files up to 500 MB each. You can queue several images: each one is sent as its own request and you can download them individually or all together as a ZIP the page builds for you."},
        {"name": "Convert to PNG", "text": "Click the convert button. There are no settings to choose: the output format is fixed to PNG, so the conversion starts straight away."},
        {"name": "Download the PNG", "text": "A single image downloads on its own; several arrive as a ZIP. The pixels are re-encoded on the server, so the file you get back is a new PNG rather than a renamed copy."},
    ],
    "m4a-to-mp3": [
        {"name": "Upload an M4A audio file", "text": "Drop a .m4a file (iTunes purchases, GarageBand exports, iPhone voice memos)."},
        {"name": "Convert and download", "text": "Run the conversion. FFmpeg re-encodes the AAC audio inside the M4A container as a 192 kbps MP3, which almost every player supports."},
    ],
    "mp4-to-mp3": [
        {"name": "Upload an MP4 video", "text": "Drop an MP4 file up to 200 MB — music videos, lecture recordings, podcasts, anything with audio."},
        {"name": "Extract audio and download", "text": "Run the conversion. PrivaTools extracts the audio track and re-encodes it as MP3, perfect for offline listening on any device."},
    ],
    "mov-to-mp4": [
        {"name": "Upload a MOV", "text": "Drop a QuickTime .mov file, the format iPhone cameras and Mac screen recordings use."},
        {"name": "Convert and download", "text": "Run the conversion. FFmpeg re-encodes the video as H.264 and the audio as AAC in an MP4 — widely playable."},
    ],
    "avi-to-mp4": [
        {"name": "Upload an AVI", "text": "Drop an .avi video — typical for older Windows captures."},
        {"name": "Convert and download", "text": "Run the conversion. The result is an MP4 with H.264 video and AAC audio, ready for streaming on phones, browsers, and modern TVs."},
    ],
    "webm-to-mp4": [
        {"name": "Upload a WebM video", "text": "Drop a WebM file (VP8 or VP9). Browser screen recorders and many web exports use WebM by default."},
        {"name": "Convert and download", "text": "Run the conversion. The video is re-encoded as H.264 MP4 for compatibility with iOS, older Android, and most editing software."},
    ],
    "mp4-to-webm": [
        {"name": "Upload an MP4 video", "text": "Drop an .mp4 file (H.264 or H.265)."},
        {"name": "Convert and download", "text": "Run the conversion. The video is re-encoded as VP9 at about 1 Mbit/s with Opus audio, which suits HTML5 video on the open web."},
    ],
    "yaml-to-json": [
        {"name": "Paste YAML", "text": "Drop a YAML document into the left textarea — a Kubernetes manifest, GitHub Actions workflow, Docker Compose file, or other configuration that uses mappings, lists and plain values."},
        {"name": "Read JSON instantly", "text": "Equivalent JSON appears on the right, pretty-printed and validated. Click Copy to grab it. 100% in your browser — your config never touches our servers."},
    ],
    "json-to-yaml": [
        {"name": "Paste JSON", "text": "Drop valid JSON into the left textarea."},
        {"name": "Read YAML instantly", "text": "Clean YAML with proper indentation appears on the right, ready to paste into a Kubernetes, GitHub Actions, or Compose file. Click Copy to grab it. Pure-browser conversion."},
    ],
    "case-converter": [
        {"name": "Paste your text", "text": "Drop any string — a variable name, sentence, or paragraph — into the input box."},
        {"name": "Copy any case format", "text": "All 12 case variants (camelCase, snake_case, kebab-case, PascalCase, CONSTANT_CASE, Title Case, sentence case, dot.case, path/case, and more) appear instantly. Click Copy on the one you want."},
    ],
    "cron-parser": [
        {"name": "Paste a cron expression", "text": "Enter a standard 5-field cron schedule: minute, hour, day of month, month, and weekday."},
        {"name": "Read the explanation", "text": "The tool validates each field and explains the schedule in plain language."},
        {"name": "Preview upcoming runs", "text": "Next run times are calculated locally in your browser timezone so you can verify the schedule before shipping it."},
    ],
    "sql-formatter": [
        {"name": "Paste SQL", "text": "Drop a compact SELECT, INSERT, UPDATE, DELETE, or JOIN-heavy query into the editor."},
        {"name": "Review formatted SQL", "text": "Keywords, clauses, commas, and boolean operators are line-broken into a readable layout."},
        {"name": "Copy the result", "text": "Use the formatted SQL in reviews, docs, migrations, dashboards, or database consoles."},
    ],
    "graphql-formatter": [
        {"name": "Paste GraphQL", "text": "Enter a query, mutation, fragment, or selection set in compact form."},
        {"name": "Format the operation", "text": "Braces, arguments, arrays, and comma-separated fields are indented in a readable shape."},
        {"name": "Copy the formatted query", "text": "Paste the result into your app, GraphiQL, Apollo Studio, or pull request."},
    ],
    "yaml-toml-converter": [
        {"name": "Choose a direction", "text": "Switch between YAML to TOML and TOML to YAML depending on the config format you need."},
        {"name": "Paste config", "text": "Common nested maps, strings, numbers, booleans, and arrays are parsed directly in your browser."},
        {"name": "Copy converted output", "text": "Use the converted config in pyproject.toml, Cargo.toml, app config, or deployment files."},
    ],
    "gitignore-generator": [
        {"name": "Pick stack templates", "text": "Choose templates such as Node, Python, Vite, Docker, Terraform, Go, Rust, macOS, or Windows."},
        {"name": "Review the generated file", "text": "The selected templates are combined into one readable .gitignore with section comments."},
        {"name": "Copy or download", "text": "Copy the text or download it directly as .gitignore for your repository root."},
    ],
    "semver-bumper": [
        {"name": "Enter the current version", "text": "Use a SemVer value such as 1.2.3 or v1.2.3-beta.1."},
        {"name": "Compare bump types", "text": "Patch, minor, major, and prerelease candidates are calculated side-by-side."},
        {"name": "Copy the release version", "text": "Use the chosen value in package manifests, tags, changelogs, and release notes."},
    ],
    "env-validator": [
        {"name": "Paste a .env file", "text": "Drop environment variable lines into the browser-only editor."},
        {"name": "Review warnings", "text": "The validator catches missing equals signs, invalid names, duplicate keys, empty values, unquoted spaces, and short-looking secrets."},
        {"name": "Fix and copy", "text": "Update your .env file until the report is clean, then copy the corrected content back to your project."},
    ],
    "json-to-csv-schema": [
        {"name": "Paste JSON", "text": "Enter a JSON object or array of objects. Nested objects are flattened to dot-notation columns."},
        {"name": "Inspect the inferred schema", "text": "Each column shows its inferred type and how many rows contain a value."},
        {"name": "Copy or download CSV", "text": "Export the flattened CSV for spreadsheets, BI tools, QA fixtures, or one-off data migrations."},
    ],
    # ── Phase 7 — competitor-gap tools (v1.5.0) ──────────────────────────
    "mute-video": [
        {"name": "Upload your video", "text": "Drag-and-drop MP4, MOV, WebM, MKV, AVI, or M4V — up to 200 MB."},
        {"name": "Click Mute Video", "text": "PrivaTools stream-copies the video and strips the audio track. Nothing is re-encoded, so it is lossless and quick."},
    ],
    "reverse-video": [
        {"name": "Upload a video", "text": "Drop an MP4/MOV/WebM/MKV/AVI file up to 200 MB. Best with short clips: every frame is held in memory while the clip is reversed, and a run longer than three minutes is stopped."},
        {"name": "Click Reverse", "text": "Both video and audio are reversed in sync. Output is MP4 (H.264 + AAC), which almost every device plays."},
    ],
    "video-speed": [
        {"name": "Upload a video", "text": "Drop an MP4/MOV/WebM/MKV/AVI file up to 200 MB. It needs an audio track: a video with no sound fails to process."},
        {"name": "Pick a speed", "text": "Drag the slider or pick a preset. Speeds from 0.3× (slow-mo) to 3.95× (hyperlapse) work; the 0.25× end of the slider and the 4× preset are rejected. 1× is original speed."},
        {"name": "Change the speed and download", "text": "FFmpeg's setpts filter handles the video and atempo filter handles audio pitch-correction so it doesn't sound like a chipmunk."},
    ],
    "audio-trim": [
        {"name": "Upload an audio file", "text": "Drop MP3, WAV, AAC, FLAC, OGG, or M4A — up to 200 MB."},
        {"name": "Set start and end", "text": "Type the start and end timestamps in HH:MM:SS format (e.g. 00:01:30 to 00:02:45)."},
        {"name": "Click Trim audio", "text": "Stream-copy preserves the original quality — no re-encoding, except that FLAC is rewritten losslessly."},
    ],
    "image-palette": [
        {"name": "Upload an image", "text": "Drop a JPG, PNG, WebP, BMP, TIFF, or GIF — up to 50 MB."},
        {"name": "Set the color count", "text": "Drag the slider from 2 to 24 colors. 6 is a good default for most brand/UI work."},
        {"name": "Copy any color", "text": "The dominant colors appear as swatches with HEX, RGB, and coverage percentage. Click a color to copy its HEX code, or copy them all at once."},
    ],
    "pixelate-image": [
        {"name": "Upload an image", "text": "Drop a JPG, PNG, WebP, or BMP file with sensitive content you want to obscure."},
        {"name": "Choose effect + strength", "text": "Pick Pixelate (mosaic, still readable as 'something censored') or Blur (Gaussian, smoother). Strength slider 1-100."},
        {"name": "Download the result", "text": "The processed image downloads once the effect has been applied. Response cleanup then removes the uploaded original and the result from the server's temporary storage."},
    ],
    "rotate-image": [
        {"name": "Upload an image", "text": "Drop a JPG, PNG, WEBP, BMP, GIF, or TIFF — up to 50 MB."},
        {"name": "Pick a rotation angle", "text": "Click 90° (left/right), 180°, 270°, or enter any custom angle (e.g. 13° to straighten a tilted scan). The canvas auto-expands so nothing is cropped off."},
        {"name": "Rotate and download", "text": "JPG, PNG and WEBP files download in the same format; BMP, GIF and TIFF come back as PNG. Transparency is preserved for PNG and WEBP."},
    ],
    "flip-image": [
        {"name": "Upload an image", "text": "Drop a JPG, PNG, WEBP, BMP, GIF, or TIFF up to 50 MB."},
        {"name": "Pick horizontal or vertical", "text": "Horizontal flips left↔right (mirror). Vertical flips top↔bottom, like a reflection in water."},
        {"name": "Flip and download", "text": "The mirrored copy downloads as soon as it is ready. Transparency is preserved; PNG stays lossless, while JPG and WEBP are re-saved at quality 92. BMP, GIF and TIFF come back as PNG."},
    ],

    # ── Auto-generated content for v1.3.1 SEO coverage push ──────────────
    "add-attachment": [
        {"name": "Upload the host PDF", "text": "Drop the PDF you want to embed a file inside (up to 500 MB)."},
        {"name": "Add the file to attach", "text": "Drop any file up to 50 MB — image, spreadsheet, .zip, even another PDF. PrivaTools embeds it without altering the visible content."},
        {"name": "Download the result", "text": "Click Attach. The output PDF has your file embedded as an attachment; readers like Acrobat show it in the Attachments panel."},
    ],
    "add-hyperlinks": [
        {"name": "Upload your PDF", "text": "Select one or more PDFs, up to 500 MB each. The PDF needs real text: a scanned page has no words to search."},
        {"name": "Let it find the addresses", "text": "There is nothing to draw or type. PrivaTools reads the text of every page and picks out each web address that starts with http:// or https://. Addresses without that prefix, such as www.example.com, and email addresses stay plain text."},
        {"name": "Download the linked PDF", "text": "Click Add hyperlinks. Each address found gets a clickable link over its text that opens the address when clicked in a PDF reader."},
    ],
    "add-shapes": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB."},
        {"name": "Define shapes", "text": "For each shape, choose the type (rectangle, circle, line or arrow), page number, coordinates, stroke color, optional fill color, and stroke width. A circle takes the smaller of its width and height as its diameter."},
        {"name": "Apply and download", "text": "Click Add Shapes. The shapes are drawn directly onto the page content; they survive copy-paste, printing, and PDF/A conversion."},
    ],
    "alternate-mix": [
        {"name": "Upload two PDFs", "text": "Select two PDFs to interleave. They don't need the same page count."},
        {"name": "Choose mode", "text": "Alternate: page 1A, 1B, 2A, 2B… Reverse-alternate: same, but the second PDF is reversed first (useful for double-sided scans where the back side scans bottom-to-top)."},
        {"name": "Download the mixed PDF", "text": "Click Mix. The output is a single PDF with pages interleaved from both inputs."},
    ],
    "annotate-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Add annotations", "text": "Draw a box on the page preview, or add an annotation from the list, then set its type (highlight, underline, strikethrough or sticky note), page, position and colour. A sticky note also takes a line of text."},
        {"name": "Save and download", "text": "Click Save. Annotations are added as standard PDF annotation objects — they appear in every PDF reader and can be edited later."},
    ],
    "auto-crop": [
        {"name": "Upload the PDF", "text": "Drop one or more PDFs, up to 500 MB each. It works on pages with real text: a scanned page is one full-page image, so it is left as it is."},
        {"name": "Let auto-detection scan", "text": "PrivaTools finds the area covered by the text and images on each page using PyMuPDF. Everything counts, including a page number in the margin, while vector drawings such as lines and boxes are not detected and can be trimmed away."},
        {"name": "Download the cropped PDF", "text": "Click Auto Crop. Each page's visible area (its CropBox) is set to that box plus a 20-point margin; the rest of the page stays in the file, hidden."},
    ],
    "bates-numbering": [
        {"name": "Upload the PDF (or batch)", "text": "Drop one PDF, or up to 100 PDFs that make up one production. Several files are numbered as one continuous run, file after file, and come back as a ZIP with a bates-manifest.json listing each file's range. The whole upload can be up to 500 MB."},
        {"name": "Configure the Bates format", "text": "Set the prefix (e.g. BATES), starting number, padding digits (e.g. 0001), and position on the page (top/bottom × left/center/right)."},
        {"name": "Download with stamps", "text": "Click Apply. PrivaTools stamps each page with the next Bates number — e.g. BATES0001, BATES0002, etc."},
    ],
    "bmp-to-pdf": [
        {"name": "Upload BMP images", "text": "Drop one or many .bmp files. BMP is the legacy Windows bitmap format — uncompressed and lossless."},
        {"name": "Choose page size", "text": "Auto (the default) makes each page the size of its image. Letter (8.5 × 11 in) or A4 (210 × 297 mm) scale each BMP to fit the page while preserving aspect ratio."},
        {"name": "Download the PDF", "text": "Click Convert. All input images are combined into a single PDF, one image per page in upload order."},
    ],
    "booklet-pdf": [
        {"name": "Add the PDF", "text": "Drop or select the document you want to print as a folded booklet, up to 500 MB."},
        {"name": "Create the booklet order", "text": "Run it. The pages are rearranged into saddle-stitch order, and blank pages are added at the end if needed so the total is a multiple of four."},
        {"name": "Print two per sheet, double-sided", "text": "Print the result with two pages per sheet, on both sides, flipping on the short edge. Fold the stack in half and it reads in order."},
    ],
    "compare-pdf": [
        {"name": "Upload two PDFs", "text": "The first is the baseline; the second is the revised version."},
        {"name": "Choose comparison mode", "text": "Visual (the default) renders both versions and paints the areas that differ in a highlight colour you can pick. Text compares the extracted text line by line."},
        {"name": "Download or view the diff", "text": "Visual mode downloads a PDF of page images, the original pages with the changed areas painted in the highlight colour, covering up to the first 50 pages. Text mode shows the diff on the page, with added lines in green and removed lines in red, plus the page count of each file."},
    ],
    "crop-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Set crop margins", "text": "Draw the area to keep on the page preview, or type the top / bottom / left / right margins to remove, in PDF points (1 pt = 1/72 inch). The same margins apply to every page."},
        {"name": "Download the cropped PDF", "text": "Click Crop. Each page's CropBox, the area a reader shows, is set inside those margins; the MediaBox is left unchanged."},
    ],
    "delete-annotations": [
        {"name": "Upload the PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Strip annotations", "text": "Click Delete. PrivaTools removes every annotation except form fields: highlights, comments, sticky notes, drawings, stamps and links."},
        {"name": "Download the cleaned PDF", "text": "The visible page content is unchanged; comments, markup and links are gone, while form fields stay fillable."},
    ],
    "delete-pages": [
        {"name": "Add the PDF", "text": "Drop or select the PDF you want to trim, up to 500 MB."},
        {"name": "List the pages to remove", "text": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page."},
        {"name": "Delete and download", "text": "Run it and save the new PDF, which contains every page you did not list, in the original order."},
    ],
    "deskew-pdf": [
        {"name": "Upload a scanned PDF", "text": "Drop a scanned PDF up to 500 MB. Works best on documents where text lines are visible."},
        {"name": "PrivaTools detects skew per page", "text": "The algorithm tries rotations of up to about 6° either way, in half-degree steps, on a low-resolution copy of each page and picks the angle at which the lines of text run straightest."},
        {"name": "Download the deskewed PDF", "text": "Each tilted page is rotated by its detected angle and saved as an image, at 200 DPI in a file of one or two pages and 100 DPI otherwise; the rotated picture is scaled to fit the original page size, with white in the corners. Pages that are already straight, within 0.3°, are kept exactly as they were."},
    ],
    "esign-pdf": [
        {"name": "Add the PDF", "text": "Drop or select the document to sign, up to 500 MB."},
        {"name": "Make your signature", "text": "Draw it, type your name and pick one of the script styles — Classic italic, Flowing script, Formal cursive or Handwritten — or upload an image of your signature."},
        {"name": "Position it", "text": "Choose the page and set the position, width and height so the signature sits on the signing line."},
        {"name": "Sign and download", "text": "Apply it and save the signed PDF, with the signature drawn onto the page."},
    ],
    "excel-to-pdf": [
        {"name": "Upload an .xlsx file", "text": "Drop an Excel workbook up to 500 MB."},
        {"name": "PrivaTools converts each sheet to a PDF page", "text": "Each sheet, hidden ones included, is drawn as a plain table on landscape A4 pages in 8 pt Helvetica, over one or more pages. Only cell values come across: number and date formats, colours, fonts, and column widths are not kept, the columns share the page width equally, and text too long for its column is cut short."},
        {"name": "Download the PDF", "text": "Click Convert. The output PDF has one section per worksheet."},
    ],
    "extract-images": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "PrivaTools pulls out the images", "text": "Each embedded raster image is saved at the pixel size stored in the PDF. JPEG and JPEG 2000 images keep their format; others are saved as PNG. Vector drawings are not images and are not extracted, and images stored inline in the page content are skipped."},
        {"name": "Download as ZIP", "text": "All extracted images are bundled into a ZIP archive, named by page and order."},
    ],
    "extract-pages": [
        {"name": "Add the PDF", "text": "Drop or select the PDF that contains the pages you need, up to 500 MB."},
        {"name": "List the pages to keep", "text": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page."},
        {"name": "Extract and download", "text": "Run it. The pages you listed are copied into one new PDF; the original is left untouched."},
    ],
    "fill-form": [
        {"name": "Upload a fillable PDF form", "text": "Drop a PDF with AcroForm fields up to 500 MB. The tool detects form fields automatically."},
        {"name": "Fill in the values", "text": "Click Detect form fields. Each field is listed with its name and type: type into text fields, tick checkboxes and choose dropdown options from their list. Signature fields cannot be filled here; use E-Sign PDF for a visible signature."},
        {"name": "Download the filled form", "text": "Click Fill. The PDF is returned with values populated. Field structure is preserved so the form can be filled again later."},
    ],
    "gif-to-pdf": [
        {"name": "Upload GIF images", "text": "Drop one or many .gif files. Animated GIFs use only the first frame."},
        {"name": "Choose page size", "text": "Auto (the default) makes each page the size of its GIF; Letter or A4 scale each GIF to fit while preserving aspect ratio."},
        {"name": "Download the PDF", "text": "All GIFs are combined into one PDF, one image per page in upload order."},
    ],
    "grayscale-pdf": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Convert all content to grayscale", "text": "PrivaTools converts every embedded image to grayscale, re-saved as JPEG. If any text or vector drawing is still in color after that, every page of the document is re-rendered as a 200 DPI grayscale image. Either way, everything ends up greyscale."},
        {"name": "Download the grayscale PDF", "text": "The size change depends on the file: in tests, a PDF of black text and a photo shrank by about a third, while a text PDF with one red heading grew many times over once its pages became images."},
    ],
    "header-footer": [
        {"name": "Upload your PDF", "text": "Drop one or more PDFs, up to 500 MB each. The same header and footer go on all of them."},
        {"name": "Enter header and footer text", "text": "Type a header, a footer, or both, and set the font size (6-32 pt on the slider, 10 pt by default). The text is printed exactly as typed on every page; placeholders such as {page} or {date} are not filled in, so use Page Numbers for numbering."},
        {"name": "Apply and download", "text": "Click Apply. The text is stamped at the top and bottom of every page in the chosen font size."},
    ],
    "heic-to-pdf": [
        {"name": "Upload HEIC images", "text": "Drop one or many .heic / .heif files (e.g. from iPhone photos)."},
        {"name": "Choose page size", "text": "Auto (the default) makes each page the size of its photo; A4 or Letter scale each photo to fit a standard page. Each HEIC is decoded with libheif."},
        {"name": "Download the PDF", "text": "All images become one PDF, one photo per page. Camera EXIF metadata, including GPS location, is not copied into the PDF."},
    ],
    "invert-colors": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose DPI for rendering", "text": "Higher DPI gives sharper output but larger file size. Choose Fast (72 DPI), Balanced (150 DPI, the default) or Sharp (200 DPI)."},
        {"name": "Download the inverted PDF", "text": "Each page is rendered, inverted (white↔black, colors mapped to complements), and re-embedded."},
    ],
    "jpg-to-pdf": [
        {"name": "Add your images", "text": "Drop or select JPG images; each one becomes a page, in the order shown."},
        {"name": "Arrange the pages", "text": "Put the images in the order you want the pages to appear before converting."},
        {"name": "Choose a page size", "text": "Auto (the default) makes every page exactly the size of its image. A4 and Letter place each image on a standard page instead, which prints predictably."},
        {"name": "Create the PDF", "text": "Convert and download a single PDF containing all the images, one per page."},
    ],
    "markdown-to-pdf": [
        {"name": "Upload a Markdown file", "text": "Drop a .md file up to 500 MB."},
        {"name": "PrivaTools renders to HTML, then PDF", "text": "Standard Markdown syntax is converted: headings, lists, links, code blocks, blockquotes, and GitHub-style tables and footnotes. Task-list checkboxes and bare web addresses stay plain text, and only images embedded as data: URIs are drawn."},
        {"name": "Download the styled PDF", "text": "The output is an A4 PDF with a clean typographic style, proper headings, and monospace code. Link text is shown in colour but is not clickable, and the link address itself is not printed."},
    ],
    "metadata": [
        {"name": "Upload the PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "View the metadata", "text": "PrivaTools displays the document's Title, Author, Subject, Keywords, Producer, Creator, Creation Date and Modified Date, as stored in its Info dictionary, plus the page count."},
        {"name": "Decide what to do next", "text": "To change the Title, Author, Subject or Keywords, switch to Edit in this tool; clearing a field removes it. To remove all metadata, use Strip Metadata."},
    ],
    "nup": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose pages-per-sheet", "text": "2, 4, 6, 9, or 16, and for 2-up either side-by-side or stacked. Every sheet is A4 landscape; each input page is shrunk to fit its cell, and cells are filled left-to-right, top-to-bottom."},
        {"name": "Download the n-up PDF", "text": "Use this to save paper when printing or to create thumbnail-style overviews."},
    ],
    "odt-to-pdf": [
        {"name": "Upload an .odt file", "text": "Drop an OpenDocument Text file (LibreOffice / OpenOffice) up to 500 MB."},
        {"name": "PrivaTools renders via LibreOffice headless", "text": "Styles, embedded images, tables, footnotes, and bibliography are kept; fonts the server does not have are replaced with similar ones, which can shift line and page breaks."},
        {"name": "Download the PDF", "text": "Click Convert. The output PDF matches the on-screen rendering closely."},
    ],
    "organize-pages": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB. A thumbnail of every page is generated so you can see what you are rearranging."},
        {"name": "Reorder the pages", "text": "Drag thumbnails into a new position, or use the move left and move right buttons for precise single steps."},
        {"name": "Remove pages you do not need", "text": "Use the remove button on any thumbnail to leave that page out of the result."},
        {"name": "Save the new PDF", "text": "Apply the changes and download the PDF with the pages in the order you arranged."},
    ],
    "overlay": [
        {"name": "Upload the base PDF", "text": "The main document (A). The output keeps its pages, bookmarks, links and form fields."},
        {"name": "Upload the overlay PDF", "text": "The PDF (B) whose pages are layered onto the base, on top of it or behind it depending on the mode."},
        {"name": "Choose mode and download", "text": "Overlay puts B on top of A; Stamp puts B behind A as a background. Output: the base PDF with an overlay page drawn onto each of its pages."},
    ],
    "page-numbers": [
        {"name": "Upload your PDF", "text": "Drop one or more PDFs, up to 500 MB each. The same settings apply to all of them."},
        {"name": "Choose position and starting number", "text": "Position: top-left/top-center/top-right/bottom-left/bottom-center/bottom-right. Starting number: defaults to 1, but use any whole number from 1 upward to continue a multi-document sequence. Font size: 12 pt by default, 6-48 pt on the slider."},
        {"name": "Apply and download", "text": "PrivaTools stamps each page with its number in the chosen position and font size."},
    ],
    "pdf-to-bmp": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Convert", "text": "Click Convert. Every page is rendered at 150 DPI, a good size for screens; there is no resolution setting on this page."},
        {"name": "Download a ZIP of BMPs", "text": "Each page becomes one 24-bit BMP file, and a multi-page PDF downloads as a ZIP. BMP is uncompressed so files are LARGE — about 6.5 MB for each A4 page."},
    ],
    "pdf-to-epub": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB. Works best on simple, text-heavy PDFs."},
        {"name": "PrivaTools copies the text and images", "text": "Each page is exported with PyMuPDF: every line of text keeps its font size, bold, italics and color, and images are embedded. All pages go into a single section; headings, lists and chapters are not detected."},
        {"name": "Download the EPUB", "text": "Each page keeps the width of the PDF page instead of reflowing to the screen, and the file lacks the navigation document the EPUB 3 standard requires, so check it in your e-book app before relying on it."},
    ],
    "pdf-to-gif": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Convert", "text": "Click Convert. Every page is rendered at 150 DPI; GIF is limited to 256 colors so detail loss is acceptable for previews."},
        {"name": "Download a ZIP of GIFs", "text": "Each page becomes one GIF file, and a multi-page PDF downloads as a ZIP. Useful for embedding PDF previews in legacy systems."},
    ],
    "pdf-to-jpg": [
        {"name": "Drop your PDF", "text": "Upload a PDF up to 500 MB. It is processed in isolated temporary per-request storage for the conversion, and response cleanup removes the job's temporary files after your download is sent."},
        {"name": "Check the output settings", "text": "Every page is rendered at 150 DPI, good for on-screen viewing and sharing, and saved at JPEG quality 75. There is no resolution or quality setting here; for 72 or 300 DPI, use PDF to Image."},
        {"name": "Add more PDFs (optional)", "text": "Queue up to 25 PDFs. Each one is converted separately and gets its own download, and Download all bundles the results into one ZIP."},
        {"name": "Need only some pages?", "text": "Every page is converted. To convert only some, pull them into a smaller PDF with Extract Pages first."},
        {"name": "Convert and download", "text": "Click Convert. Each page becomes one JPG. Multi-page PDFs return as a ZIP; single-page PDFs return as a single JPG file."},
    ],
    "pdf-to-markdown": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB. Text-heavy PDFs convert best."},
        {"name": "PrivaTools extracts and structures text", "text": "Headings are detected by font size and bold text is marked with double asterisks. Each line of the PDF becomes its own paragraph and pages are separated by a horizontal rule; images, lists, tables and code blocks are not detected."},
        {"name": "Download the .md file", "text": "Open in any Markdown editor for editing or further conversion to HTML / EPUB / DOCX."},
    ],
    "pdf-to-png": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Convert", "text": "Click Convert. Every page is rendered at 150 DPI; there is no resolution setting on this page. For 72 or 300 DPI, use PDF to Image instead."},
        {"name": "Download a ZIP of PNGs", "text": "Each page becomes one PNG file with lossless compression, and a multi-page PDF downloads as a ZIP. Pages are rendered onto a white background, so the PNGs have no transparency."},
    ],
    "pdf-to-pptx": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "PrivaTools creates one slide per page", "text": "Each page is rendered at 200 DPI and placed as one picture, centered and scaled to fit a 4:3 slide (10 x 7.5 in). No text boxes are created, so the text is part of the picture."},
        {"name": "Download the .pptx file", "text": "Open in PowerPoint / Keynote / Google Slides to present it, or to add your own titles, notes and slides around the page pictures."},
    ],
    "pdf-to-tiff": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Convert", "text": "Click Convert. Every page is rendered in color at 200 DPI; there is no resolution setting on this page."},
        {"name": "Download the TIFF", "text": "PrivaTools produces a single multi-page TIFF with one image per PDF page, compressed losslessly with Deflate."},
    ],
    "pdfa-validator": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB to check it for basic PDF/A indicators."},
        {"name": "PrivaTools runs a conformance check", "text": "It looks for a PDF/A identifier in the XMP metadata, checks that a title and an author are set, and flags encryption. Fonts, colour profiles, JavaScript and external references are not examined."},
        {"name": "Read the validation report", "text": "It shows whether a PDF/A label was found and lists any warnings. A pass means those basic checks passed, not that the file conforms to PDF/A."},
    ],
    "png-to-pdf": [
        {"name": "Upload PNG images", "text": "Drop one or many .png files, up to 50 images and 200 MB in total."},
        {"name": "Choose page size", "text": "Auto (the default) makes each page the size of its image; A4 or Letter fit each image on a standard page. Transparency is not kept: transparent areas show the colour stored underneath, which is often black."},
        {"name": "Download the PDF", "text": "All images become a single PDF, one per page. Lossless — PNG pixels map directly to PDF image objects."},
    ],
    "pptx-to-pdf-convert": [
        {"name": "Upload a .pptx file", "text": "Drop a PowerPoint presentation up to 500 MB."},
        {"name": "Each slide becomes one PDF page", "text": "The text of each text box and placeholder is drawn at its position in Helvetica, using the first run's size (capped at 36 pt) and bold setting. Pictures, tables, charts, SmartArt, backgrounds, colours, and speaker notes are left out; for a visual copy of the slides, use Office to PDF."},
        {"name": "Download the PDF", "text": "The output preserves slide aspect ratio (16:9 or 4:3 as designed)."},
    ],
    "qr-code": [
        {"name": "Enter the data to encode", "text": "Type or paste a URL or plain text, or a contact card (vCard) or WiFi login already written in its standard text format; there is no form that builds them for you. Ordinary text can run to about 2,200 characters."},
        {"name": "Choose size and format", "text": "Set the size from 100 to 1,200 pixels (300 by default) and download as a PNG image or a one-page PDF containing the same image. You can also change the code and background colours and add a small centre logo."},
        {"name": "Download the QR", "text": "Click Generate QR code and download the result; PNG codes also show a preview. Codes use error correction level M, which tolerates about 15% damage, or level H, about 30%, when you add a centre logo."},
    ],
    "remove-blank-pages": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB. Scanned documents from a duplex scanner, which often contain empty reverse sides, are the typical case."},
        {"name": "Set the sensitivity", "text": "The slider runs from 50 to 100 and starts at 85. Higher values only remove pages that are almost perfectly white; lower values also remove scanned blank pages that carry specks, show-through or scanner noise."},
        {"name": "Remove and download", "text": "Run it and check the result. Every page judged blank is dropped and the rest keep their order."},
    ],
    "repair-pdf": [
        {"name": "Upload the corrupt PDF", "text": "Drop a PDF up to 500 MB that won't open or shows errors in your viewer."},
        {"name": "PrivaTools rebuilds the file structure", "text": "Uses pikepdf to parse the PDF tolerantly, recover damaged cross-reference tables, and rewrite the file with a clean structure; if that fails, it retries with MuPDF."},
        {"name": "Download the repaired PDF", "text": "Structural damage such as a broken cross-reference table or a missing trailer is usually fixable. Damaged data inside a page's content is copied as it is, and a file cut off too early may not be recoverable at all."},
    ],
    "resize-pdf": [
        {"name": "Upload your PDF", "text": "Drop one or more PDFs, up to 500 MB each."},
        {"name": "Choose target page size", "text": "A4, Letter, A3, Legal, or Custom, where you enter the width and height in points (72 points = 1 inch), from 72 to 14400."},
        {"name": "Download the resized PDF", "text": "PrivaTools sets each page's size (its MediaBox) to the target and removes any crop box. The content is not scaled or moved: it stays anchored to the bottom-left corner."},
    ],
    "reverse-pdf": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB."},
        {"name": "Reverse the order", "text": "Run it. There are no options: the last page becomes the first and the first becomes the last."},
        {"name": "Download the result", "text": "Save the reversed PDF. The pages themselves are copied unchanged."},
    ],
    "rtf-to-pdf": [
        {"name": "Upload an .rtf file", "text": "Drop a Rich Text Format file (Word, WordPad, TextEdit, Pages all save in RTF)."},
        {"name": "PrivaTools extracts the text", "text": "The RTF codes are stripped and the remaining text is set in 11 pt Helvetica on A4 pages. Bold, italic, underline, fonts, tables, and images are not kept, paragraphs can run together, and some leftover codes or font names may appear as text."},
        {"name": "Download the PDF", "text": "Click Convert. Open in any PDF viewer."},
    ],
    "sanitize-pdf": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB containing potentially risky elements."},
        {"name": "PrivaTools clears what it can", "text": "It empties the document information fields (title, author, dates, producer) and deletes Movie and RichMedia annotations, the containers for old video and Flash (SWF) content. JavaScript, embedded files, links, layers, form fields, screen annotations and XMP metadata are left in the file."},
        {"name": "Download the sanitized PDF", "text": "Visible content is preserved, and the file is rewritten without unused objects."},
    ],
    "set-permissions": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Set an owner password and permissions", "text": "Choose which operations are allowed for users without the owner password: print, copy text, modify, annotate. If you leave the owner password blank, a random one is used, so nobody can later use it to change the permissions."},
        {"name": "Download the protected PDF", "text": "Anyone without the owner password is limited to the allowed operations. The PDF itself still opens without a password (use Protect PDF if you want a user password too)."},
    ],
    "split-by-bookmarks": [
        {"name": "Add a PDF with bookmarks", "text": "Drop or select a PDF up to 500 MB that has a bookmark outline, such as a report or book exported with chapter bookmarks."},
        {"name": "Split at each chapter", "text": "Run it. A new part starts at every top-level bookmark, so each chapter or section becomes its own PDF."},
        {"name": "Download the ZIP", "text": "The parts arrive together in a ZIP. Check it against the bookmark panel in your PDF reader to confirm the sections are what you expected."},
    ],
    "stamp-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose a stamp", "text": "Preset: APPROVED, CONFIDENTIAL, COPY, DRAFT, FINAL, NOT APPROVED, SAMPLE, VOID. Or custom: your own text."},
        {"name": "Set opacity and position", "text": "Opacity runs from 5 to 100 % (30 % by default) and fades the stamp's colour; the letters stay solid. Position: centre, top or bottom (Diagonal currently places it level across the centre as well). Pages: all, or page numbers separated by commas. Click Apply."},
    ],
    "strip-metadata": [
        {"name": "Upload PDF(s)", "text": "Drop one or many PDFs up to 500 MB each. Multi-file batches are supported."},
        {"name": "PrivaTools removes all metadata", "text": "Title, Author, Subject, Keywords, Producer, Creator, Creation Date, Modified Date, all XMP fields, and any custom-defined metadata. The cleaned XMP keeps just two entries that the PDF library writes itself: a pikepdf producer tag and the time of processing."},
        {"name": "Download the clean PDF (or ZIP)", "text": "Single file → single PDF; multiple files → ZIP. Visible content is unchanged."},
    ],
    "svg-to-pdf": [
        {"name": "Upload SVG images", "text": "Drop one or many .svg files, up to 50 files and 200 MB in total. Images embedded as data: URIs are fine, but an SVG that loads an image from another file or a web address is rejected."},
        {"name": "Choose page size", "text": "Auto (the default) sizes the page to the rendered image, which is 2400 points wide, so choose A4 or Letter for a printable page; each SVG is then scaled to fit while preserving its aspect ratio."},
        {"name": "Download the PDF", "text": "All SVGs become one PDF, one per page. Each drawing is rasterized into an image first, so the PDF contains pictures rather than vector paths or selectable text."},
    ],
    "tiff-to-pdf": [
        {"name": "Upload TIFF images", "text": "Drop one or more .tif / .tiff files, up to 50 files and 200 MB in total. Only the first page of a multi-page TIFF is converted."},
        {"name": "Choose page size", "text": "Auto (the default) makes each page the size of its image; A4 or Letter scale each image to fit a standard page."},
        {"name": "Download the PDF", "text": "All TIFFs become one PDF. Whatever compression the TIFF used (LZW, Deflate, or JPEG), the pixels are decoded and stored with lossless Flate compression, so JPEG-compressed TIFFs can give a larger PDF."},
    ],
    "transparent-background": [
        {"name": "Upload a PDF", "text": "Drop one or more PDFs, up to 500 MB each. PrivaTools renders each page as an image at the DPI you choose, 144 by default (72-300)."},
        {"name": "Set threshold", "text": "Set how close to pure white a pixel must be to count as background, from 180 to 255 (245 by default). A pixel whose red, green and blue values are all at or above the threshold becomes transparent."},
        {"name": "Download with transparency", "text": "The output has white/off-white pixels converted to alpha=0. Useful for overlaying scans on dark backgrounds. Each page becomes a single image, so its text can no longer be selected or searched."},
    ],
    "verify-signature": [
        {"name": "Upload a signed PDF", "text": "Drop a PDF with one or more digital signatures."},
        {"name": "PrivaTools looks for signature fields", "text": "It scans each page's form fields for signature fields. It does not check certificates, trust chains or whether the content changed since signing, and at present it misses signature fields, so a signed PDF comes back with none found."},
        {"name": "Read the result", "text": "Any fields found are listed with the status detected, beside a note that cryptographic verification is not supported. For a real check, open the file in a PDF reader that validates signatures."},
    ],
    "webp-to-pdf": [
        {"name": "Upload WebP images", "text": "Drop one or many .webp files, up to 50 images and 200 MB in total."},
        {"name": "Choose page size", "text": "Auto (the default) makes each page the size of its image; A4 or Letter fit each image on a standard page. Transparency is not kept: transparent areas show the colour stored underneath, which is often black."},
        {"name": "Download the PDF", "text": "All images become one PDF in upload order. The PDF is usually much larger than the WebP files, because the pixels are stored with lossless compression."},
    ],
    "whiteout-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Draw white-out rectangles", "text": "Drag on the page preview to draw a box, or add one and set its page, position and size. Each box is filled with white; what is underneath is hidden from view but stays in the file."},
        {"name": "Download the cleaned PDF", "text": "Apply the boxes and download the PDF. The regions are covered with white wherever the file is opened."},
    ],
    "add-subtitles": [
        {"name": "Upload a video", "text": "Drop an MP4/MOV/MKV file up to 500 MB."},
        {"name": "Upload an SRT subtitle file", "text": "Standard SubRip Text format with timestamps and dialogue."},
        {"name": "Add the subtitles and download", "text": "The subtitles are burned into the video pixels, so they show in every player and cannot be switched off. The result is an MP4 with H.264 video."},
    ],
    "audio-merge": [
        {"name": "Upload audio files", "text": "Drop 2 or more audio files (MP3, WAV, OGG, FLAC, AAC), up to 50; the whole upload has to fit within the 500 MB request limit."},
        {"name": "Reorder if needed", "text": "Use the up and down arrows to set the order the files play in."},
        {"name": "Download the merged audio", "text": "FFmpeg joins the files in that order into one MP3, whatever the input formats were."},
    ],
    "color-converter": [
        {"name": "Enter a HEX color", "text": "Type a HEX code (#FF5733, or the short #F53 form), or click the swatch to pick a color."},
        {"name": "PrivaTools shows the same color in every format", "text": "Live conversion: HEX, RGB, RGBA, HSL, a Tailwind class and a CSS variable, plus a contrast rating against white or black text."},
        {"name": "Copy the value you need", "text": "Use the Copy button on any row. Runs entirely in your browser — no network roundtrip."},
    ],
    "create-zip": [
        {"name": "Upload files", "text": "Drop multiple files of any type, up to 500 MB in total."},
        {"name": "Choose compression level", "text": "Slide from 0 (Store, no compression) through Fast and Balanced (the default, level 6) to Smallest size at 9."},
        {"name": "Download the ZIP", "text": "All files are bundled into a single .zip with their original filenames and extensions."},
    ],
    "csv-json": [
        {"name": "Paste your CSV or JSON", "text": "Choose CSV to JSON or JSON to CSV, then paste your data. The CSV delimiter (comma, semicolon, tab or pipe) is detected for you."},
        {"name": "Click Convert", "text": "CSV → JSON: each row becomes an object using the first row as keys. JSON → CSV: array of objects → rows; keys → header."},
        {"name": "Copy or download the result", "text": "Runs entirely in your browser. Your data never leaves your device."},
    ],
    "extract-archive": [
        {"name": "Upload an archive", "text": "Drop a .zip, .tar, .tar.gz, .tar.bz2, or .tar.xz archive up to 500 MB."},
        {"name": "PrivaTools extracts and returns each file", "text": "All files inside are extracted and bundled into a folder-style download."},
        {"name": "Download the extracted folder as a ZIP", "text": "The result lists each file's name and size, then everything downloads together as one ZIP."},
    ],
    "extract-audio": [
        {"name": "Upload a video file", "text": "Drop an MP4/MOV/MKV/WebM file up to 200 MB."},
        {"name": "Choose output format", "text": "MP3 (universal), WAV (uncompressed), OGG (open), FLAC (lossless), AAC (high quality)."},
        {"name": "Download the audio track", "text": "FFmpeg extracts the audio stream and re-encodes it to the chosen format, even when the video already carries that format."},
    ],
    "generate-barcode": [
        {"name": "Enter the data to encode", "text": "The string or number you want to encode, up to 200 characters. Format limits vary (e.g. EAN-13 takes 12 digits and the check digit is added for you)."},
        {"name": "Choose barcode type", "text": "Code 128 (most flexible), Code 39, EAN-13 (retail), EAN-8 (small packs), UPC-A (US retail), ISBN-13 (books) or QR code (also available via the QR tool)."},
        {"name": "Download as PNG", "text": "The image comes out at a fixed size, ready for printing on labels or embedding in documents; there is no size setting."},
    ],
    "generate-favicon": [
        {"name": "Upload a square image", "text": "PNG, JPG, WebP or BMP. PrivaTools resizes it to favicon dimensions automatically; a rectangular image is centred on a transparent square instead of being stretched."},
        {"name": "PrivaTools generates the favicon", "text": "One .ico file that holds three sizes: 16×16, 32×32 and 48×48 pixels. Transparency in the source image is kept."},
        {"name": "Download the icon", "text": "Rename the downloaded file to favicon.ico and put it at the root of your website, where browsers look for it by default, or point to it with an icon link in the head section of your pages."},
    ],
    "gif-to-mp4": [
        {"name": "Upload an animated GIF", "text": "Drop a .gif file up to 500 MB."},
        {"name": "PrivaTools converts via FFmpeg", "text": "GIF frames become MP4 frames at the source frame rate. H.264 codec for universal compatibility."},
        {"name": "Download the MP4", "text": "Typically 5-10x smaller than the source GIF, with smoother playback."},
    ],
    "hash-generator": [
        {"name": "Type or paste your input", "text": "Or choose a file. It is read in your browser, not uploaded."},
        {"name": "Calculate the hashes", "text": "One click gives SHA-1, SHA-256 and SHA-512 side by side. SHA-256 is the modern recommendation."},
        {"name": "Copy the hex digest", "text": "Runs entirely in your browser using the Web Crypto API. Input never leaves your machine."},
    ],
    "image-converter": [
        {"name": "Add your images", "text": "Drop or select the pictures you want to convert, up to 500 MB each. You can add several at once; they are processed a few at a time and a batch comes back as one ZIP."},
        {"name": "Choose the output format", "text": "Pick the target: JPG, PNG, WebP, BMP or TIFF. That choice is the only setting — everything else uses the imaging library's defaults, so there is no quality slider to tune."},
        {"name": "Convert and download", "text": "Start the conversion. A single image downloads on its own; several are offered as one ZIP."},
    ],
    "image-ocr": [
        {"name": "Upload an image", "text": "JPG, PNG, TIFF, WebP up to 500 MB."},
        {"name": "Choose the engine", "text": "On our server (the default) runs Tesseract on the PrivaTools server. My own AI key sends the image straight to a vision model at the provider you choose. In this browser runs tesseract.js on your device and downloads the language data when it is first needed."},
        {"name": "Select OCR language", "text": "Pick one of 13 languages: English, French, German, Spanish, Italian, Portuguese, Chinese (Simplified), Chinese (Traditional), Japanese, Korean, Arabic, Hindi and Russian. A vision model detects the language itself, so the picker is hidden for that engine."},
        {"name": "Copy or download the text", "text": "The recognized text appears in a box you can copy from, or save as a .txt file."},
    ],
    "image-watermark": [
        {"name": "Add the images", "text": "Drop or select JPG, PNG, WebP or BMP pictures up to 500 MB each. You can add several at once; they are processed a few at a time and a batch comes back as one ZIP."},
        {"name": "Type the watermark text", "text": "Enter the words to stamp on the image. The starting text is WATERMARK; a name, a website or a word such as DRAFT or SAMPLE is more useful in practice."},
        {"name": "Set opacity and size", "text": "Opacity starts a little above half-strength, and the font size starts at 40. Lower opacity is less intrusive but also easier to overlook."},
        {"name": "Choose where it sits", "text": "Pick one of the four corners, the centre (the default), or Tile to repeat the text across the whole picture. A corner keeps the subject clear; Tile is the hardest to crop away."},
        {"name": "Apply and download", "text": "Run it and save the marked copy. The text is drawn into the pixels, so it is part of the image rather than a layer that can be switched off."},
    ],
    "json-xml-formatter": [
        {"name": "Paste JSON or XML", "text": "Choose JSON or XML, then paste your text or load the example."},
        {"name": "Format, minify or validate", "text": "Format adds indentation and line breaks, Minify removes the extra whitespace, and Validate only checks the syntax. Keys keep their original order."},
        {"name": "Copy or download the result", "text": "Runs entirely in your browser."},
    ],
    "lorem-ipsum": [
        {"name": "Choose paragraphs, sentences, or words", "text": "Specify how much placeholder text you need."},
        {"name": "Generate or reroll", "text": "Text appears as you change the options; Reroll shuffles it. The classic variant draws on Lorem Ipsum (Cicero's De Finibus, scrambled), the publishing industry's standard placeholder."},
        {"name": "Copy and use in your mockups", "text": "Runs entirely in your browser."},
    ],
    "make-collage": [
        {"name": "Add your images", "text": "Drop or select the pictures for the collage. They fill the grid left to right, top to bottom."},
        {"name": "Arrange the tiles", "text": "Drag the thumbnails to change their order. What you see in the preview is the order the finished collage uses."},
        {"name": "Choose the grid", "text": "By default the tool finds a balanced, roughly square grid for the number of images, up to six columns. Switch that off to set the columns yourself, anywhere from 1 to 6."},
        {"name": "Adjust spacing and background", "text": "Spacing between the tiles runs from 0 to 100 pixels and starts at 10. The background colour shows through that gap and around the edges, and starts as white."},
        {"name": "Build and download", "text": "Create the collage and save the single combined image."},
    ],
    "markdown-html": [
        {"name": "Write or open Markdown", "text": "Type, paste or open a .md file (up to 2 MB). The conversion runs one way: Markdown to HTML."},
        {"name": "Watch the preview", "text": "The HTML and the preview update as you type. It covers headings, paragraphs, bold, italic, inline code, fenced code, links, lists, blockquotes and horizontal rules."},
        {"name": "Copy the result", "text": "Runs entirely in your browser."},
    ],
    "merge-images": [
        {"name": "Upload 2+ images", "text": "JPG, PNG, WebP — at least 2 files."},
        {"name": "Choose direction", "text": "Vertical: top-to-bottom (good for screenshots in sequence). Horizontal: side-by-side (good for before/after). A grid places them in equal cells, with the number of columns picked for you."},
        {"name": "Download the merged image", "text": "Each input is scaled to a common dimension and joined into one PNG, which keeps any transparency. The grid option returns a JPG instead."},
    ],
    "password-generator": [
        {"name": "Choose length and character classes", "text": "Length 4-64 (20 by default). Include uppercase / lowercase / digits / symbols / exclude ambiguous (1lI0O)."},
        {"name": "Generate", "text": "A password appears straight away and changes with the options; Regenerate makes a new one and Batch x5 makes five. It uses the Web Crypto API's getRandomValues — cryptographically strong random."},
        {"name": "Copy the password", "text": "Copy the password into your password manager or the form that needs it. It is generated in JavaScript on this page and is not sent to PrivaTools."},
    ],
    "qr-reader": [
        {"name": "Upload an image with a QR code", "text": "JPG, PNG, WebP, or BMP. The QR code should be reasonably in-focus."},
        {"name": "PrivaTools decodes via pyzbar", "text": "Detects the QR code anywhere in the image and at any angle. A damaged or partly covered code can still read when the damage stays within the code's built-in error correction, which tops out at about 30%."},
        {"name": "Read the decoded data", "text": "Plain text, URL, vCard, WiFi credentials, or whatever the QR encoded."},
    ],
    "resize-crop-image": [
        {"name": "Add your image", "text": "Drop or select one picture up to 500 MB. This tool works on a single image at a time."},
        {"name": "Choose resize or crop", "text": "Resize stretches the whole image to exactly the width and height you give. Crop fills that same size without distorting anything: it scales the picture to cover the box and trims the overflow evenly from the centre."},
        {"name": "Set the width and height", "text": "Enter the target size in pixels. Both values accept anything from 1 up to 8000, and the starting point is 800 by 600."},
        {"name": "Process and download", "text": "Run it and save the result, which keeps the format of your original. Check the edges when cropping, since anything outside the centred box is removed."},
    ],
    "subtitle-converter": [
        {"name": "Upload an SRT / VTT / ASS subtitle file", "text": "The format is detected from the file's content."},
        {"name": "Choose target format", "text": "SRT (universal) or VTT (web video). ASS files can be read but not written."},
        {"name": "Download the converted subtitles", "text": "Runs entirely in your browser."},
    ],
    "svg-to-png": [
        {"name": "Add the SVG", "text": "Drop or select .svg files up to 500 MB each. Vector artwork, icons and exported logos are the usual input. You can add several at once; they are processed a few at a time and a batch comes back as one ZIP."},
        {"name": "Choose the scale", "text": "Pick 1×, 2× (the default), 3× or 4× the SVG's own dimensions; the output size in pixels is shown before you convert. 2× gives a crisp result on high-resolution screens."},
        {"name": "Render and download", "text": "Convert and save the PNG. Because SVG is vector artwork, rendering at a larger scale produces genuinely sharper output rather than an enlarged blur."},
    ],
    "url-encoder": [
        {"name": "Paste a string, URL, or JWT", "text": "Pick the mode yourself: URL encode, URL decode or JWT decode."},
        {"name": "Choose encode or decode", "text": "URL encode: spaces → %20, etc. URL decode: %20 → spaces. JWT decode: header.payload.signature → parsed JSON."},
        {"name": "Copy the result", "text": "Runs entirely in your browser."},
    ],
    "url-to-pdf": [
        {"name": "Enter the URL to convert", "text": "Any public web page — no file upload needed for this one."},
        {"name": "PrivaTools fetches and renders", "text": "WeasyPrint loads the page (with CSS, images, fonts) and renders it as a print-quality PDF."},
        {"name": "Download the PDF", "text": "Click Convert. Pagination follows print CSS rules; links remain clickable."},
    ],
    "uuid-generator": [
        {"name": "Choose UUID version", "text": "v4 (random — most common) or v7-like (time-sortable random — modern recommendation)."},
        {"name": "Choose bulk count", "text": "1 to 500 UUIDs at once."},
        {"name": "Copy the list", "text": "One UUID per line, copied with one click. Runs entirely in your browser using Web Crypto API."},
    ],
    "video-converter": [
        {"name": "Upload a video", "text": "MP4, WebM, MOV, AVI, MKV — up to 500 MB."},
        {"name": "Choose target format", "text": "MP4 (universal), WebM (open, smaller), MOV (Apple), AVI (legacy), MKV (open container)."},
        {"name": "Download the converted video", "text": "FFmpeg transcodes via the appropriate codec (H.264 for MP4, VP9/Opus for WebM, etc.)."},
    ],
    "video-merge": [
        {"name": "Upload 2+ videos", "text": "MP4 / MOV / MKV / WebM / AVI, up to 20 clips; the whole upload has to fit within the 500 MB request limit."},
        {"name": "Reorder if needed", "text": "Use the up and down arrows to set the order the clips play in."},
        {"name": "Download the merged video", "text": "FFmpeg joins the clips in that order and re-encodes the result as one MP4 with H.264 video and AAC audio."},
    ],
    "video-resizer": [
        {"name": "Upload a video", "text": "MP4 / MOV / MKV / WebM up to 500 MB."},
        {"name": "Choose preset", "text": "240p, 360p, 480p (SD), 720p (HD, the default), 1080p (Full HD) or 1440p (QHD)."},
        {"name": "Download the resized video", "text": "FFmpeg scales the video to the target height while preserving aspect ratio."},
    ],
    "video-thumbnail": [
        {"name": "Upload a video", "text": "MP4 / MOV / MKV / WebM up to 500 MB."},
        {"name": "Choose timestamp", "text": "Drag the slider or type the time in seconds (e.g. 5.5 = 5.5 seconds in); the preview shows that frame. It starts at 1 second."},
        {"name": "Download the frame as JPG", "text": "FFmpeg extracts the frame at that timestamp and saves it as a JPG."},
    ],
    "video-to-pdf": [
        {"name": "Upload a video", "text": "MP4 / MOV / MKV / WebM up to 500 MB."},
        {"name": "Choose number of frames", "text": "Anywhere from 1 to 60 (12 by default). PrivaTools samples frames at even intervals across the video."},
        {"name": "Download the PDF", "text": "Each frame becomes one PDF page. Useful for storyboards, content review, or accessibility."},
    ],
    "word-counter": [
        {"name": "Paste your text", "text": "Or type directly. Counter updates as you type."},
        {"name": "Read live stats", "text": "Word count, character count (with/without spaces), sentence count, paragraph count, line count, reading time at 220 wpm."},
        {"name": "Optional metrics", "text": "Average word length, longest sentence and an approximate passive-voice count."},
    ],

    # ── filled in 2026-09-02: these tools shipped without How-To steps, which
    # made them the thinnest pages on the site. ──────────────────────
    "aac-to-mp3": [
        {"name": 'Upload an AAC file', "text": 'Drop an .aac file up to 200 MB. For .m4a files, use M4A to MP3.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'AAC is decoded and re-encoded as MP3 at 192 kbps. Both are lossy, so a little more detail is lost.'},
        {"name": 'Convert and download', "text": 'Run the conversion. AAC and MP3 are both lossy, so this is a transcode rather than a lossless change; the MP3 is encoded at 192 kbps. MP3 is the safer choice for car stereos, gym equipment and older players that never learned AAC.'},
    ],
    "flac-to-mp3": [
        {"name": 'Upload a FLAC file', "text": 'Drop a .flac file. FLAC is lossless, so the source is the best possible input for an encode.'},
        {"name": 'PrivaTools encodes via FFmpeg', "text": 'FLAC is lossless, so the encoder is working from the best possible source. The MP3 is encoded at 192 kbps, roughly 3–6x smaller than a CD-quality FLAC.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Expect roughly a 3–6x size reduction. This step is one-way: the detail MP3 discards cannot be recovered, so keep the FLAC if it is your master copy.'},
    ],
    "mp3-to-aac": [
        {"name": 'Upload an MP3', "text": 'Drop an .mp3 file up to 200 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'AAC is more efficient than MP3 at the same bitrate, but re-encoding one lossy format as another loses a little more each time.'},
        {"name": 'Convert and download', "text": 'Run the conversion. AAC is more efficient than MP3 at the same bitrate, but re-encoding one lossy format as another always loses a little more. The result is a raw .aac file at 192 kbps, not an .m4a. It is worth doing for Apple devices and for streaming, not for archiving.'},
    ],
    "mp3-to-flac": [
        {"name": 'Upload an MP3', "text": 'Drop an .mp3 file up to 200 MB.'},
        {"name": 'PrivaTools converts via FFmpeg', "text": 'The decoded audio is stored losslessly. Nothing further is lost, and nothing is restored: the output sounds identical to the MP3 and is larger.'},
        {"name": 'Convert and download', "text": 'Run the conversion. FLAC stores the decoded audio losslessly, so nothing further is lost — but nothing is restored either. The output is larger than the MP3 and sounds identical to it. Use this when a workflow demands FLAC input, not to improve quality.'},
    ],
    "mp3-to-ogg": [
        {"name": 'Upload an MP3', "text": 'Drop an .mp3 file up to 200 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'Ogg Vorbis is royalty-free and well supported by browsers, game engines and Linux desktops.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Ogg Vorbis is royalty-free and well supported by browsers, game engines and Linux desktops. As a lossy-to-lossy transcode, it loses a little more detail; the Ogg is encoded with a 192 kbps target.'},
    ],
    "mp3-to-wav": [
        {"name": 'Upload an MP3', "text": 'Drop an .mp3 file up to 200 MB.'},
        {"name": 'PrivaTools decodes via FFmpeg', "text": 'The MP3 is decoded to uncompressed PCM, which is what editors, samplers and DAWs want to work from.'},
        {"name": 'Convert and download', "text": 'Run the conversion. The MP3 is decoded to uncompressed PCM, which is what most editors, samplers and DAWs want to work from. Files grow roughly tenfold — a 5 MB MP3 lands near 50 MB.'},
    ],
    "ogg-to-mp3": [
        {"name": 'Upload an Ogg file', "text": 'Drop an .ogg or .oga file.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'One more lossy generation, in exchange for a format that plays essentially everywhere.'},
        {"name": 'Convert and download', "text": 'Run the conversion. MP3 plays essentially everywhere, which Ogg still does not, at the cost of one more lossy generation. The MP3 is encoded at 192 kbps.'},
    ],
    "wav-to-flac": [
        {"name": 'Upload a WAV file', "text": 'Drop a .wav file up to 200 MB.'},
        {"name": 'PrivaTools compresses via FFmpeg', "text": 'FLAC is lossless: the audio is bit-for-bit identical to the WAV, typically 40-60% smaller.'},
        {"name": 'Convert and download', "text": 'Run the conversion. FLAC is lossless: the audio is bit-for-bit identical to the WAV and typically 40–60% smaller. This is the one audio conversion here that costs you nothing in quality.'},
    ],
    "wav-to-mp3": [
        {"name": 'Upload a WAV file', "text": 'Drop a .wav file. Uncompressed audio is the ideal source for an encode.'},
        {"name": 'PrivaTools encodes via FFmpeg', "text": 'Uncompressed source gives the encoder the best possible input. At 192 kbps, expect roughly a 7:1 reduction from CD-quality WAV.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Expect roughly a 7:1 reduction. Keep the WAV if it is your master — MP3 is a delivery format, not an archive one.'},
    ],
    "wav-to-ogg": [
        {"name": 'Upload a WAV file', "text": 'Drop a .wav file up to 200 MB.'},
        {"name": 'PrivaTools encodes via FFmpeg', "text": 'Encoded straight from uncompressed source with a 192 kbps target, so quality is as good as that bitrate allows.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Ogg Vorbis is patent-free and a good fit for games and web audio, encoded here straight from uncompressed source so quality is as good as the bitrate allows.'},
    ],
    "avi-to-webm": [
        {"name": 'Upload an AVI file', "text": 'Drop an .avi file up to 500 MB. AVI is a legacy container, often carrying DivX or Xvid video.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The legacy stream, often DivX or Xvid, is re-encoded as VP9.'},
        {"name": 'Convert and download', "text": 'Run the conversion. The video is re-encoded as VP9 WebM at about 1 Mbit/s, which plays natively in modern browsers; a high-bitrate AVI shrinks a lot.'},
    ],
    "mkv-to-mp4": [
        {"name": 'Upload an MKV file', "text": 'Drop an .mkv file. Matroska commonly holds H.264 or H.265 video.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The video is re-encoded as H.264 and the audio as AAC, even when the MKV already holds H.264.'},
        {"name": 'Convert and download', "text": 'Run the conversion. MP4 is the container Safari, iOS, Windows and most TVs expect. Because the video is re-encoded, expect a small quality loss and a different file size.'},
    ],
    "mkv-to-webm": [
        {"name": 'Upload an MKV file', "text": 'Drop an .mkv file up to 500 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The video is re-encoded as VP9, which browsers play natively and MKV never could.'},
        {"name": 'Convert and download', "text": 'Run the conversion. The result is VP9 WebM — open, royalty-free and suited to HTML5 video where MKV has no browser support at all.'},
    ],
    "mov-to-gif": [
        {"name": 'Upload a MOV clip', "text": 'Drop a .mov file. Short clips work best; GIF has no audio, and its compression is far weaker than a video codec\'s.'},
        {"name": 'PrivaTools samples frames via FFmpeg', "text": 'Frames are sampled at 10 per second, scaled to 480 pixels wide and mapped to a 256-colour palette.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Frames are sampled and mapped to a 256-colour palette. Expect the GIF to be considerably larger than the video — use MP4 or WebM if you can, and GIF only where autoplay everywhere matters more than size.'},
    ],
    "mov-to-mkv": [
        {"name": 'Upload a MOV file', "text": 'Drop a .mov file from QuickTime, an iPhone or a camera.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The video is re-encoded as H.264 (CRF 23) and the audio as AAC, then stored in Matroska.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Matroska can hold multiple audio and subtitle tracks, though this conversion keeps just one audio track.'},
    ],
    "mov-to-webm": [
        {"name": 'Upload a MOV file', "text": 'Drop a .mov file up to 500 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The video is re-encoded as VP9 at about 1 Mbit/s with Opus audio, well below the bitrate of a typical phone or camera MOV, and it plays without QuickTime.'},
        {"name": 'Convert and download', "text": 'Run the conversion. VP9 WebM is the right output for the open web: usually much smaller than a camera MOV, and playable without QuickTime.'},
    ],
    "mp4-to-avi": [
        {"name": 'Upload an MP4', "text": 'Drop an .mp4 file up to 500 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The video is re-encoded as MPEG-4 Part 2 with MP3 audio. That codec is less efficient than H.264, so the file will usually grow rather than shrink.'},
        {"name": 'Convert and download', "text": 'Run the conversion. AVI is only worth choosing for genuinely old software or hardware that refuses MP4; its older codec is less efficient and the file will usually grow.'},
    ],
    "mp4-to-mov": [
        {"name": 'Upload an MP4', "text": 'Drop an .mp4 file up to 500 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'The video is re-encoded as H.264 (CRF 23) and the audio as AAC, even when the MP4 already holds H.264.'},
        {"name": 'Convert and download', "text": 'Run the conversion. MOV is what QuickTime, Final Cut Pro and much of the macOS video world prefer.'},
    ],
    "webm-to-gif": [
        {"name": 'Upload a WebM clip', "text": 'Drop a .webm file. Keep it short — every GIF frame is stored as its own image.'},
        {"name": 'PrivaTools samples frames via FFmpeg', "text": 'Every GIF frame is stored as its own image, which is why short clips work and long ones do not.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Frames are reduced to a 256-colour palette. GIF trades size and colour depth for the ability to autoplay in email and old chat clients.'},
    ],
    "webm-to-mov": [
        {"name": 'Upload a WebM file', "text": 'Drop a .webm file up to 500 MB.'},
        {"name": 'PrivaTools re-encodes via FFmpeg', "text": 'VP9 is re-encoded into a stream QuickTime and Final Cut will actually open.'},
        {"name": 'Convert and download', "text": 'Run the conversion. The clip is re-encoded into a MOV that QuickTime and Final Cut will open, which they will not do for VP9 WebM.'},
    ],
    "jpg-to-bmp": [
        {"name": 'Upload a JPG', "text": 'Drop a .jpg or .jpeg file.'},
        {"name": 'PrivaTools converts via Pillow', "text": 'Every pixel is written uncompressed, which is why the output dwarfs the JPG.'},
        {"name": 'Convert and download', "text": 'Run the conversion. BMP stores every pixel uncompressed, so the file will be many times larger than the JPG. It exists for legacy Windows software and imaging hardware that reads nothing else.'},
    ],
    "jpg-to-tiff": [
        {"name": 'Upload a JPG', "text": 'Drop a .jpg or .jpeg file up to 500 MB.'},
        {"name": 'PrivaTools converts via Pillow', "text": 'The existing pixels are rewritten into TIFF without a further lossy generation.'},
        {"name": 'Convert and download', "text": 'Run the conversion. TIFF is the format archives, print shops and scanning workflows ask for. It cannot restore detail the JPG already discarded — it preserves exactly what is there, without adding another lossy generation.'},
    ],
    "png-to-bmp": [
        {"name": 'Upload a PNG', "text": 'Drop a .png file up to 500 MB.'},
        {"name": 'PrivaTools converts via Pillow', "text": 'BMP has no practical transparency support, so the alpha channel is dropped and transparent areas usually come out black.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Transparent areas are not filled with white; they usually come out black, so place the image on a background first if you need one. Keep the PNG if transparency matters.'},
    ],
    "png-to-tiff": [
        {"name": 'Upload a PNG', "text": 'Drop a .png file up to 500 MB.'},
        {"name": 'PrivaTools converts via Pillow', "text": 'Both formats are lossless, so the conversion is faithful and the alpha channel survives.'},
        {"name": 'Convert and download', "text": 'Run the conversion. Both formats are lossless, so this is a faithful conversion, and TIFF keeps the alpha channel — the right choice for archival and print pipelines that will not take PNG.'},
    ],
    "webp-to-bmp": [
        {"name": 'Upload a WebP image', "text": 'Drop a .webp file up to 500 MB.'},
        {"name": 'PrivaTools converts via Pillow', "text": 'Uncompressed output; the alpha channel is dropped, so transparent areas usually come out black.'},
        {"name": 'Convert and download', "text": 'Run the conversion. BMP is uncompressed and drops transparency, which usually leaves those areas black; it is worth using only when some older tool insists on it.'},
    ],
    "webp-to-tiff": [
        {"name": 'Upload a WebP image', "text": 'Drop a .webp file up to 500 MB.'},
        {"name": 'PrivaTools converts via Pillow', "text": 'TIFF keeps the alpha channel and is read by archival software that has never heard of WebP.'},
        {"name": 'Convert and download', "text": 'Run the conversion. TIFF preserves transparency and is accepted by archival and prepress software that has no idea what WebP is.'},
    ],
    "pdf-to-long-image": [
        {"name": 'Upload the PDF', "text": 'Select a PDF up to 500 MB. Every page is rendered, so long documents make very tall images.'},
        {"name": 'Pick a format', "text": 'PNG is lossless and best for text and line art; JPG is saved at quality 90 and produces a much smaller file for scanned or photographic pages.'},
        {"name": 'Download the stitched image', "text": 'Pages are rendered at the resolution you pick (100 DPI by default, 36 to 200 DPI) and joined top to bottom on a white canvas, with a thin gap between pages. Pages narrower than the widest one are centred, so a mixed-size document stays aligned.'},
    ],
    "bates-remove": [
        {"name": 'Upload the stamped PDF', "text": 'Select a PDF that carries Bates numbering applied by PrivaTools or another tool.'},
        {"name": 'Describe the stamp', "text": 'Give the prefix and any suffix used when the numbers were applied, so the tool matches those stamps and leaves real page content alone. The digit count matters only when both are blank: then anything in the top or bottom inch that looks like letters followed by at least that many digits is removed.'},
        {"name": "Download the clean PDF", "text": "The matching stamps are removed and the rest of the page is untouched. You download a new PDF; the original on your device is not changed."},
    ],
    "accessibility-check": [
        {"name": 'Upload the PDF', "text": 'Select the PDF you need to audit. Tagged, untagged, scanned and born-digital files are all accepted.'},
        {"name": 'Run the audit', "text": 'The document is checked against PDF/UA and WCAG expectations: tag structure, document language, title metadata, and alternative text on images.'},
        {"name": 'Read the report', "text": 'Each finding names the requirement it relates to, so you can fix the document at source. The report is advice, not a legal certification.'},
    ],
    "remove-watermark": [
        {"name": 'Upload the watermarked PDF', "text": 'Select a PDF that carries a visible watermark.'},
        {"name": 'Review the candidates', "text": 'The tool scans the pages for text that repeats across them and is see-through or set at an angle, as watermarks usually are, and lists what it found. Image watermarks such as logos are not detected.'},
        {"name": 'Remove and download', "text": 'Confirm which candidates to strip. Only those objects are removed, so the rest of the page survives intact. A watermark burned into a scanned image is part of the picture and cannot be lifted this way — use Remove Image Watermark for that.'},
    ],
    "remove-image-watermark": [
        {"name": 'Upload the image', "text": 'Drop a JPG, PNG or WebP that carries a watermark.'},
        {"name": 'Mark the watermark', "text": 'Select the area covering it. The tool reconstructs that region from the pixels around it.'},
        {"name": 'Download the result', "text": 'Works best on watermarks over flat or gently textured backgrounds. Over busy detail the repair will be visible — and only remove watermarks from images you have the right to alter.'},
    ],
    "translate-pdf": [
        {"name": "Choose the PDF", "text": "Select a text-based PDF. The text is extracted in your browser, so the file itself is not uploaded; a scanned PDF needs OCR PDF first."},
        {"name": "Pick a translator and languages", "text": "'On this device' (the default) translates English to or from the listed languages with an OPUS-MT model of about 107 MB per language pair, downloaded once and cached. 'My own API key' sends the text to the AI provider you configured and offers more target languages."},
        {"name": "Translate and review", "text": "Run the translation and read the result page by page. The on-device models translate text, not layout, so check names, numbers and long sentences."},
        {"name": "Save the result", "text": "Download the translation as a .txt file, which stays on your device. 'Save as PDF' is optional and sends the translated text, not your original PDF, to the PrivaTools server to be typeset in a basic Latin font; letters outside Western European alphabets, such as Cyrillic, Chinese, Arabic or Hindi, come out as boxes, so keep the .txt for those languages."},
    ],
}


# ---------------------------------------------------------------------------
# FAQ  –  tool slug → list of {q, a}
# ---------------------------------------------------------------------------
TOOL_FAQ: dict[str, list[dict[str, str]]] = {
    "merge-pdf": [
        {"q": "How many PDFs can I merge at once?", "a": "Up to 100 files in one merge, each up to 500 MB. The combined upload is also capped at roughly 500 MB, so a handful of very large files may need to be merged in two passes — merge some, then merge that result with the rest."},
        {"q": "Can I change the order after adding files?", "a": "Yes. Drag the cards into the order you want before merging; the output follows it exactly. To reorder pages within a file, type them in the order you want in that file's page field, or use Organize Pages on the merged result."},
        {"q": "Can I merge only some pages from each file?", "a": "Yes. Each file has its own page field in the merge settings: leave it blank to include every page, or enter ranges such as 1-3,5 or 2-end. Pages are added in the order you type them, so you can also reorder pages within a file."},
        {"q": "Are bookmarks kept?", "a": "No. The merged PDF does not carry over the bookmarks (outline) of the individual files. Page content is copied unchanged, so the document reads the same, but if navigation matters, add a new outline afterwards with the Bookmarks tool."},
        {"q": "Can I merge password-protected PDFs?", "a": "A file that needs a password to open has to be unlocked first, because the merge has to read its pages. Use Unlock PDF with the password you already have, then merge the unlocked copy."},
        {"q": "What happens to my files after I upload them?", "a": "It is uploaded over HTTPS and merged on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDFs and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "split-pdf": [
        {"q": "Which split mode should I use?", "a": "Use page ranges to pull a specific set of pages into one file, Every page to break a document into single pages, and Every N pages to cut a long file into equal parts, for example separating a batch of two-page forms scanned together."},
        {"q": "How do I write page ranges?", "a": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page. Page 0, pages beyond the end, and ranges written backwards are rejected with a message rather than guessed at."},
        {"q": "Why did I get one PDF instead of several?", "a": "Because page ranges collects everything you list into a single document. To get separate files, choose Every page or Every N pages, which return a ZIP."},
        {"q": "Is the original PDF changed?", "a": "No. The split writes new files from a copy, and the PDF on your device stays exactly as it was."},
        {"q": "Can I split by bookmarks, file size or a word?", "a": "Yes, with the dedicated tools: Split by Bookmarks cuts at each chapter, Split by Size keeps every part under a size you choose, and Split by Text starts a new part wherever a phrase appears."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and split on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "split-by-size": [
        {"q": "Where does it cut the document?", "a": "Between pages. A page is never split in half; the tool fills each part with as many whole pages as fit under your limit, then starts the next part."},
        {"q": "What if a single page is bigger than my limit?", "a": "A page cannot be divided, so it ends up in a part of its own that is larger than the target. Compress PDF can shrink image-heavy pages before splitting."},
        {"q": "What size should I choose for email?", "a": "Stay comfortably below the attachment limit of the service you are sending through, because email encoding makes attachments larger in transit. The default of 10 MB is a reasonable starting point."},
        {"q": "Should I compress instead?", "a": "Try compressing first when the goal is a smaller file: Compress PDF may bring it under the limit in one piece. Split by size when the document is genuinely too big even after compression."},
        {"q": "Does splitting reduce quality?", "a": "No. Pages are copied as they are; only the division into files changes."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and split on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "compress-pdf": [
        {"q": "What does compression actually change?", "a": "Mainly the images. Each embedded picture is downsampled to a maximum dimension and re-encoded as JPEG at a quality that depends on the level, and the file structure is rewritten more compactly. Text and vector graphics are not rasterised, so they stay sharp and selectable."},
        {"q": "Which level should I use?", "a": "Recommended suits most documents. Light is for files where image detail matters, such as photos you may print. Extreme is for getting under a strict size limit when some image softness is acceptable. Email aims at a typical attachment limit; Print keeps images at a print-friendly resolution."},
        {"q": "Why did my PDF barely shrink?", "a": "Because there was little to compress. A PDF made mostly of text and vector graphics is already small, and one whose images were compressed hard before has little left to give. The biggest savings come from scans and photo-heavy documents."},
        {"q": "Will text stay searchable?", "a": "Yes. Compression works on images and file structure; the text layer is left in place, so you can still search, select and copy text."},
        {"q": "Can I compress many PDFs at once?", "a": "Yes. The page sends each file as its own request, three at a time, and each can be up to 500 MB. Compression is one of the heavier jobs, so fair-use rate limits apply and very large batches are best split into smaller runs."},
        {"q": "The result is still too big. What next?", "a": "Try Extreme, Target size, or Custom with a lower quality and a smaller maximum image dimension. If it still will not fit, Split by Size divides the document into parts under a size you choose."},
        {"q": "What happens to my PDFs after I upload them?", "a": "It is uploaded over HTTPS and compressed on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDFs and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "edit-pdf": [
        {"q": "Can I change the existing text in the PDF?", "a": "Not directly. The editor adds content on top of the page. To replace a word, cover it with whiteout and type the new text over it."},
        {"q": "Is whiteout the same as redaction?", "a": "No. Whiteout hides what is underneath visually, but the original text remains in the file and can still be selected or extracted. Use Redact PDF to actually remove sensitive content."},
        {"q": "Can someone remove my edits afterwards?", "a": "They cannot be switched off like comments, because they are drawn into the page content. Someone with a full PDF editor could still delete them, as with any PDF content."},
        {"q": "Can I add an image or logo?", "a": "Yes. The image tool places a picture on the page, which is useful for a logo, a stamp or a scanned signature."},
        {"q": "Can I fill in a PDF form with this?", "a": "You can type text on top of any page, but it will not fill real form fields. For a PDF with interactive fields, Fill Form enters values into the fields themselves, which is what forms software expects."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and edited on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "sign-pdf": [
        {"q": "Is this a legally binding digital signature?", "a": "It is an electronic signature in the everyday sense — an image of your signature placed on the document — not a certificate-based digital signature. Many routine agreements accept that; documents that require a qualified or certificate signature need a service that issues one."},
        {"q": "Can someone tell if the document was changed after I signed?", "a": "No. Because this is a visible signature rather than a cryptographic one, nothing in the file detects later edits. Keep your own copy of exactly what you signed."},
        {"q": "Draw or upload — which is better?", "a": "Drawing is quick and fine for most uses. Uploading a scan or photo of your real signature, ideally on a clean white background, looks more natural on formal documents."},
        {"q": "Can I add initials or sign several pages?", "a": "Each run places one signature on the page you choose. Run it again on the output to add initials or sign additional pages."},
        {"q": "What is the difference between Sign PDF and eSign PDF?", "a": "Both place a visible signature. eSign PDF adds the option to type your name in a choice of script styles; Sign PDF is the direct draw-or-upload route."},
        {"q": "What happens to my document after I upload it?", "a": "It is uploaded over HTTPS and signed on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the document and signature image and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "protect-pdf": [
        {"q": "What encryption does PrivaTools use?", "a": "PDFs are encrypted with AES-256, the strongest method the PDF standard defines. There is no choice of algorithm: AES-128 and the broken RC4 are not offered."},
        {"q": "Can I allow printing but block copying text?", "a": "Yes. Leave Print on and Extract off: readers that honour the permissions will print but not let text be copied. There are three switches, Print, Extract (copying text and images) and Modify (editing, comments, form filling and page assembly); access for screen readers is always left allowed."},
        {"q": "What happens if I forget the password?", "a": "PrivaTools does not store your password. If you lose it, there is no way to recover it — AES-256 has no backdoor. Save your password in a password manager like 1Password, Bitwarden, or your browser's built-in store before you encrypt."},
        {"q": "What happens to my PDF and password after I upload them?", "a": "Both are sent over HTTPS and used for that one request. The PDF is processed in isolated temporary per-request storage; response cleanup removes the job's temporary files after the encrypted copy is sent, and a background sweep clears anything left behind by an interrupted request. The password is not saved, which is also why nobody can recover it for you."},
        {"q": "What's the file size limit?", "a": "Up to 500 MB per file on the hosted site. Resource and fair-use rate limits also apply, as they do on every tool, so an unusually large or complex PDF can time out."},
        {"q": "Can I batch-protect multiple PDFs?", "a": "Yes — upload multiple files and they will each be encrypted with the same password, then bundled into a ZIP. Use different passwords for different files by running the tool separately."},
        {"q": "Does a password stop someone from copying or printing the PDF?", "a": "An open password encrypts the file, so it cannot be read without the password. Restrictions such as no-print or no-copy work differently: PDF readers honour them voluntarily, and anyone who can open the file can strip them with other software. Set an open password when the content itself has to stay private."},
    ],
    "unlock-pdf": [
        {"q": "Can it open a PDF if I have forgotten the password?", "a": "No. You need the correct password; the tool does not attempt to guess or break encryption. If the password is lost, the original creator of the document is the only route back."},
        {"q": "What does unlocking remove?", "a": "The password needed to open the file and the permission restrictions attached to it, such as limits on printing, copying text or editing. The content itself is unchanged."},
        {"q": "I entered the password and it says it did not match.", "a": "Check capitalisation, keyboard layout and any trailing spaces; PDF passwords are case-sensitive. If the document was protected by someone else, confirm with them which password opens it."},
        {"q": "Can I unlock several PDFs at once?", "a": "Yes, up to 100 files in one request, provided they all use the same password."},
        {"q": "How is my password handled?", "a": "It is sent over HTTPS together with the file and used only for that request to decrypt the PDF. It is not saved to an account or kept for later use."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and decrypted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "rotate-pdf": [
        {"q": "Can I rotate individual pages instead of the entire PDF?", "a": "Yes. Choose Specific pages and type the page numbers or ranges, such as 1,3,5-8; the other pages are left untouched. Each run uses one angle, so rotate page 3 by 90° in one run and page 7 by 180° in the next."},
        {"q": "Does rotation affect text searchability?", "a": "No. The text layer is preserved exactly. Rotation only changes the visual display orientation of each page; the underlying text glyphs, search index, and bookmark positions are kept intact."},
        {"q": "What rotation angles are supported?", "a": "90° clockwise, 180° (upside-down), and 270° clockwise (equivalent to 90° counter-clockwise). PDF only allows rotations in 90° increments per the spec — arbitrary angles aren't supported."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and rotated in isolated temporary per-request storage on the PrivaTools server. Response cleanup removes the job's temporary files after the result is sent, and a background sweep clears anything left behind by an interrupted request. Nothing is added to an account or file library."},
        {"q": "What's the file size limit?", "a": "Up to 500 MB per file on the hosted site. Resource and fair-use rate limits apply, as they do on every tool."},
        {"q": "Does rotation preserve bookmarks, hyperlinks, and form fields?", "a": "Yes. All structural metadata — bookmarks, internal hyperlinks, external hyperlinks, form fields, and annotations — is preserved through rotation. Only the display orientation of the page content changes."},
        {"q": "Is the rotation saved in the file or only in my viewer?", "a": "It is saved in the file. The new orientation is written into the PDF you download, so the pages stay rotated in every reader, including phone apps, instead of only in the viewer you happened to use."},
    ],
    "watermark": [
        {"q": "Can the watermark be removed?", "a": "It is drawn into the page content rather than added as a comment, so it cannot be hidden with a viewer setting. Someone with a full PDF editor and enough effort can still remove it — treat a watermark as a clear marking, not as protection."},
        {"q": "Text or image — which should I use?", "a": "Text for status markings such as DRAFT or CONFIDENTIAL. An image for branding, such as a company logo. A logo with a transparent background looks cleanest."},
        {"q": "Which position is hardest to remove?", "a": "Tile and Diagonal, because they cover the page rather than one area and cannot be cropped away. A corner mark is the least intrusive but also the easiest to cut off."},
        {"q": "What opacity should I use?", "a": "Low enough that the underlying text remains easy to read. The default is fairly light; raise it for proofs you want clearly marked."},
        {"q": "Does it watermark every page?", "a": "Yes. Every page of the document receives the same mark."},
        {"q": "Will the text in my PDF stay searchable?", "a": "Yes. The watermark is added on top of each page; the existing text layer is not changed."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and watermarked on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "ocr-pdf": [
        {"q": "What languages does the OCR support?", "a": "The server engine has 17 language packs: English, French, German, Spanish, Italian, Portuguese, Dutch, Russian, Polish, Turkish, Japanese, Korean, Chinese (Simplified and Traditional), Arabic, Hindi and Vietnamese. The list offers 45 languages; the rest, such as Hebrew, Thai and Ukrainian, are marked as not installed on the server but work with the In this browser engine, which downloads that language's data once and returns text only. There is no auto-detect, so pick the document's language."},
        {"q": "Will OCR change how my scanned PDF looks?", "a": "It can. The server engine renders each page to an image at the DPI you pick (200 by default), has Tesseract rebuild the page from that image with an invisible text layer, and joins the pages into a new PDF. The pages are therefore new images rather than your original scan data, digital text and drawings become part of the image, and links, bookmarks, form fields and comments are not carried over. Choose Precise (300 DPI) if fine detail matters."},
        {"q": "How accurate is the OCR?", "a": "It depends on the scan. Clean, straight pages of printed text read well, while blurry, skewed or low-contrast pages produce more mistakes, so check important passages against the page. For best results, run Deskew PDF before OCR if pages are tilted, choose Precise (300 DPI) for small or faint print, and scan at a higher resolution if you control the scan."},
        {"q": "Can I get the extracted text as a separate file?", "a": "Yes. Show text, the default output, displays the recognised text on the page ready to copy; Download .txt saves it as one text file with a marker before each page; Searchable PDF returns the PDF with its text layer. The in-browser and own-key engines give text only, which you can copy or download as .txt."},
        {"q": "Where is my document processed?", "a": "That depends on the engine you pick. 'On our server' (the default) uploads the PDF over HTTPS and runs Tesseract in isolated temporary per-request storage; response cleanup removes the job's temporary files after the result is sent, and a background sweep clears anything left behind by an interrupted request. 'In this browser' runs OCR on your device after a one-time engine download, and with your own AI key the page images go from your browser straight to that provider."},
        {"q": "Can I OCR a scanned PDF in a language I don't have the keyboard for?", "a": "Yes. OCR needs the right language to be available to the engine, not a keyboard. Once the text is recognised you can copy it, or use Translate PDF to translate the searchable result."},
    ],
    "redact-pdf": [
        {"q": "Is redaction permanent and truly irreversible?", "a": "Yes for what is under the boxes. The text glyphs and image pixels under each redaction rectangle are removed before the new PDF is written, and the file is rewritten without the old objects, so there is nothing under the box to recover. The same words elsewhere in the file are not touched: a bookmark title, a comment or the document metadata that repeats them survives, so check those too."},
        {"q": "Can I search and redact every occurrence of a name or number?", "a": "Not in Redact PDF, which works with the boxes you draw. Smart Redact finds candidates such as emails, phone numbers and names across the whole document, and removes every match you approve in one batch."},
        {"q": "What's the difference between redacting and drawing a black box?", "a": "Drawing a black annotation rectangle, as a comment or markup tool does, covers the text visually but leaves it in the file underneath — anyone can move or delete the annotation and recover the secret. True redaction removes the text and image data and rewrites the file. PrivaTools uses true redaction, not annotation."},
        {"q": "Will the redacted PDF still be searchable for non-redacted text?", "a": "Yes. Only the content under the redaction rectangles is destroyed. Text outside the rectangles, along with bookmarks, hyperlinks, and the text-search layer, are preserved intact."},
        {"q": "Is metadata also redacted?", "a": "By default the rectangles destroy on-page text and images. Author name, title, software, and other XMP/Info metadata are NOT automatically stripped — use the Strip Metadata tool afterward. Smart Redact leaves metadata alone too."},
        {"q": "What happens to the original, unredacted PDF I upload?", "a": "It is uploaded over HTTPS and held in isolated temporary per-request storage while the redactions are applied. Response cleanup removes both the original and the redacted output after the result is sent, and a background sweep clears anything left behind by an interrupted request. The redaction code is open source under the MIT licence, so it can be reviewed, or self-hosted if the original must not leave your network."},
    ],
    "flatten-pdf": [
        {"q": "What does flattening a PDF mean?", "a": "Flattening usually means turning form fields and annotations into ordinary page content. This tool currently does part of that: it makes form fields read-only rather than merging them into the page, and it does not flatten comments, highlights or layers."},
        {"q": "When should I flatten a PDF?", "a": "Before sending a filled form, so the recipient's reader will not let them change the answers."},
        {"q": "Does flattening reduce file size?", "a": "Sometimes, slightly: the file is rewritten with unused objects removed and its streams compressed. The form fields themselves stay in the file."},
    ],
    "bookmarks": [
        {"q": "Can I create a multi-level bookmark tree?", "a": "No. Every bookmark is saved at the top level, in the order listed; nested entries are not supported."},
        {"q": "Do bookmarks work in all PDF readers?", "a": "Yes. The bookmarks use the standard PDF outline format supported by Adobe Reader, Preview, Chrome, Firefox, and all major PDF viewers."},
        {"q": "Can I import a bookmark structure from a text file?", "a": "There is no file import, but the JSON view accepts a pasted array of entries, each with a title and a page, so a list prepared elsewhere goes in at once."},
    ],
    "form-creator": [
        {"q": "What field types can I add?", "a": "Single-line and multi-line text fields, checkboxes, dropdowns, list boxes, and empty signature fields. There are no date pickers, and the Radio type in the list currently fails with an error."},
        {"q": "Will the form work in Adobe Reader?", "a": "It should. The fields are standard AcroForm fields, the form format that Adobe Reader and other common PDF viewers support, and the file asks viewers to draw the fields' appearance themselves. Open the finished form in the reader your recipients use before sending it."},
        {"q": "Can I set fields as required?", "a": "Yes. Tick Required on a field to set the PDF required flag; how it is enforced depends on the PDF reader and on how the form is submitted. Validation rules such as numeric-only or email format are not available."},
    ],
    "extract-tables": [
        {"q": "What output formats are supported?", "a": "CSV only. All detected tables go into one CSV file, with a blank row between tables. For an Excel workbook, use PDF to Excel, which puts each page on its own sheet."},
        {"q": "Can it extract tables from scanned PDFs?", "a": "Usually not. Detection looks for ruled lines drawn in the PDF itself, and a scanned page is a picture, so no table is found even after the OCR tool adds a text layer. The tool works on digitally created PDFs whose tables have ruled borders."},
        {"q": "How does the tool detect table boundaries?", "a": "It uses PyMuPDF table detection, which looks for the ruled lines drawn around and between cells. Tables laid out with spacing alone, without visible borders, are usually not detected, and when no table is found you get an error instead of a CSV."},
    ],
    "pdf-to-pdfa": [
        {"q": "What is PDF/A and why would I need it?", "a": "PDF/A is an ISO-standardized archival format that ensures documents remain viewable long-term. Government agencies, courts, and archives often require PDF/A submissions."},
        {"q": "What changes does the conversion make?", "a": "It re-saves the file with unused objects removed and streams compressed, sets the producer to PrivaTools PDF/A Converter, and writes PDF/A-2b identification into the XMP metadata. It also drops the author, subject, keywords, creating application and creation and modification dates from the document properties, keeping only the title. It does not embed fonts, add an output colour profile, convert colours or remove JavaScript, so the result is labelled PDF/A-2b without being checked against the standard."},
        {"q": "Will the document look different after conversion?", "a": "No. Pages are not re-rendered, and text, images, links, bookmarks, form fields and annotations stay as they were. Because fonts are not embedded, text in a font that was not already embedded still depends on the fonts of the computer that opens the file."},
    ],
    "image-to-pdf": [
        {"q": "What image formats are supported?", "a": "JPG, PNG, WebP, BMP, TIFF, GIF, HEIC/HEIF, and SVG, up to 50 images and 200 MB in total per PDF. Animated GIF and WebP files and multi-page TIFFs contribute only their first frame, SVGs are converted to images, and transparent areas are not kept."},
        {"q": "Can I control the page size?", "a": "Yes. Auto (the default) makes each page match its image, one point per pixel. A4 and Letter place each image on a portrait page, scaled to fit inside a half-inch margin. There is no separate orientation setting."},
        {"q": "Are multiple images combined into one PDF?", "a": "Yes. All uploaded images become pages in a single PDF. Drag to reorder them before converting."},
    ],
    "txt-to-pdf": [
        {"q": "Can I change the font and page size?", "a": "No. Every PDF uses 11 pt Courier, a monospace font, on A4 pages with 1-inch margins; there are no font, size, page, or margin settings."},
        {"q": "Does the tool handle Unicode text?", "a": "Only partly. The file must be UTF-8, and only Western European characters print, such as accented letters, curly quotes, and the euro sign. Other scripts, including Chinese, Arabic, Cyrillic, and Devanagari, come out as black boxes."},
        {"q": "Is there a character or line limit?", "a": "There is no separate character or line limit, but the conversion has to finish within the two-minute request limit, so text files of tens of megabytes can time out. Split very large files first."},
    ],
    "office-to-pdf": [
        {"q": "Which Office formats are supported?", "a": "Word (.doc, .docx), Excel (.xls, .xlsx), PowerPoint (.ppt, .pptx), and OpenDocument formats (.odt, .ods, .odp)."},
        {"q": "Are charts and images preserved?", "a": "Yes. The conversion uses LibreOffice, which preserves charts, images, tables, headers, footers, and most formatting accurately."},
        {"q": "How long does conversion take?", "a": "It depends on the size and complexity of the document. Each conversion starts LibreOffice with a fresh profile, and a conversion still running after two minutes is stopped with a timeout error, so split very large documents first."},
    ],
    "word-to-pdf": [
        {"q": "Will the PDF look exactly like my Word document?", "a": "No. Only the text of the body paragraphs is carried over, in Helvetica on A4 pages; headings are enlarged and bold, and a paragraph with any bold or italic text is set that way throughout. Fonts, alignment, spacing, images, tables, headers, footers and links are not kept. For a close copy of the layout, use Office to PDF, which converts with LibreOffice."},
        {"q": "Why do the fonts look different?", "a": "Because every paragraph is set in Helvetica, whatever fonts the document uses, and characters outside Western European scripts, such as Cyrillic or Chinese, do not print correctly. Office to PDF keeps the document's fonts where the server has them."},
        {"q": "Which file types can I convert?", "a": "This page takes .docx. For .doc, .odt, .rtf, spreadsheets or presentations, use Office to PDF, which accepts a wider set of formats."},
        {"q": "Are comments and tracked changes included?", "a": "Accept or reject tracked changes and remove comments before converting if you do not want them to appear. Converting exactly the version you intend to share avoids surprises."},
        {"q": "Do links and headings carry over?", "a": "Headings do, as larger bold text: Heading 1 and 2 get their own sizes, and lower levels share a third. Links do not: their text is kept but is not clickable, and a table of contents comes across as plain text."},
        {"q": "What happens to my document after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the document and the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "epub-to-pdf": [
        {"q": "Are images and formatting preserved?", "a": "No. Only the text is extracted: images, headings, bold and italic, and the book's styling are dropped, and each chapter becomes one continuous block of text. The chapter's page title and any style rules written inside it can also appear as text at the start of the chapter."},
        {"q": "Can I convert DRM-protected EPUBs?", "a": "No. DRM-protected e-books cannot be converted. The tool only works with DRM-free EPUB files."},
        {"q": "What page size options are available?", "a": "Only A4, with 1-inch margins. There is no Letter or custom size, and the text is wrapped to fit that page."},
    ],
    "html-to-pdf": [
        {"q": "Can I convert a live website URL to PDF?", "a": "Yes, for public http and https addresses; local and private network addresses are refused, and the address must start with http:// or https://. The server fetches the page's HTML, up to 5 MB, and lays it out on A4 pages, but it does not load the page's external stylesheets or images or run its JavaScript, so many sites come out plainer than in a browser."},
        {"q": "Is JavaScript rendered?", "a": "No. Neither mode runs JavaScript, so content that a page builds with scripts after it loads does not appear in the PDF. If you can copy the finished HTML, for example from your browser's developer tools, paste that instead."},
        {"q": "Are external stylesheets and images included?", "a": "Only for pasted HTML. There, stylesheets and images referenced by full http(s) addresses are fetched, up to 25 MB each, while relative paths such as images/logo.png cannot be resolved and are skipped. For a web address, only styles written inside the page itself are applied; its external stylesheets and images are not loaded."},
    ],
    "xml-to-pdf": [
        {"q": "What XML schemas are supported?", "a": "Any well-formed XML file is supported. The tool prints the XML itself as indented text; it does not draw a tree or table and does not apply XSL transforms."},
        {"q": "Is syntax highlighting included?", "a": "Only simple colouring: every line that contains a tag is printed in blue and text-only lines in black. Element names, attributes, and values are not coloured separately."},
        {"q": "Can I convert large XML files?", "a": "Up to 5 MB per file; larger files are refused. Each nesting level is indented further, and long lines are cut off at the right margin, so very wide or deeply nested documents lose text."},
    ],
    "csv-to-pdf": [
        {"q": "Does the tool auto-detect delimiters?", "a": "No. Only commas separate columns, and quoted values may contain commas. Semicolon-, tab-, or pipe-separated files come out as a single column, so save them as comma-separated CSV first."},
        {"q": "How are wide tables handled?", "a": "Pages are always portrait A4, and columns that do not fit across the page are cut off at the right edge rather than wrapped or split across pages. For example, a file with 30 short columns shows only its first nine, so remove or split columns before converting."},
        {"q": "Is the first row treated as a header?", "a": "Yes, always. The first row is drawn in bold white text on a dark background, and there is no option to turn this off, so add a header row if your data has none. The header appears once, at the top of the first page."},
    ],
    "json-to-pdf": [
        {"q": "Is JSON validated before conversion?", "a": "Yes. The file is parsed first and invalid JSON is not converted, but the error is a general conversion failure without a line number. Check the syntax in JSON / XML Formatter to find the problem."},
        {"q": "How are nested objects displayed?", "a": "Nested objects and arrays are indented two spaces per level, with every key in bold blue. Everything is printed fully expanded; there is no preview or collapsing."},
        {"q": "Can I convert JSON arrays into tables?", "a": "No. Arrays of objects are printed as indented JSON like the rest of the file, not as a table. For a table, convert the array to CSV with the CSV ↔ JSON Converter and then use CSV to PDF."},
    ],
    "pdf-to-word": [
        {"q": "Will the Word file look exactly like the PDF?", "a": "Close for straightforward documents, not identical for complex ones. A PDF describes where text sits on a page, not how it flows, so the converter has to reconstruct paragraphs. Multi-column layouts, text boxes and intricate tables usually need some tidying afterwards."},
        {"q": "Why is my converted document empty or full of images?", "a": "The PDF is probably a scan: a picture of text with no text layer to read. Run OCR PDF first to add recognisable text, then convert that version."},
        {"q": "What is preserved?", "a": "The text itself, with font names, colours and paragraph spacing where the PDF records them. Embedded images are included too, placed at a standard width rather than their original position. Treat the result as an editable starting point rather than a pixel-perfect copy."},
        {"q": "Why did my large PDF fail?", "a": "Conversion has a time budget, and very long or complex documents can exceed it. Split the PDF into smaller parts with Split PDF, convert each, and combine the text in Word."},
        {"q": "Can I convert a password-protected PDF?", "a": "Not while it is locked. Use Unlock PDF with the password you have, then convert the unlocked copy."},
        {"q": "How often can I use it?", "a": "Conversion is one of the heavier jobs on the server, so it has a fair-use rate limit per visitor. Space out a large batch rather than submitting many files in quick succession."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the generated .docx and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "pdf-to-excel": [
        {"q": "Does it convert the entire PDF or just tables?", "a": "It works page by page, with one sheet per page. On a page where a table is found, only the table rows are kept and the rest of that page's text is left out. A page without a table has its text copied, one line per row. For the full text, use PDF to Word or PDF to Text."},
        {"q": "Can I choose which tables to extract?", "a": "No. Every page is processed and every detected table is kept. To convert only some pages, pull them into a smaller PDF with Extract Pages first, then convert that."},
        {"q": "What if my PDF has no visible table borders?", "a": "Then the table is usually not detected. Detection looks for the ruled lines drawn around and between cells, so a table laid out with spacing alone comes through as plain text, often one value per row in column A, and needs rearranging in the spreadsheet."},
        {"q": "What happens to a confidential financial PDF after I upload it?", "a": "The PDF is uploaded over HTTPS and converted in isolated temporary per-request storage on the PrivaTools server, using local libraries rather than a third-party API. Response cleanup removes the PDF and the generated .xlsx after the result is sent, and a background sweep clears anything left behind by an interrupted request."},
        {"q": "What's the file size limit?", "a": "Up to 500 MB per file on the hosted site. Table extraction is one of the heavier jobs, so fair-use rate limits apply and a very long PDF can hit the request timeout; splitting the document first avoids that."},
        {"q": "Does it work on scanned PDFs?", "a": "Only partly. A scan has no text, so on its own it gives an error. Run the OCR PDF tool first (you can pick the language) and the recognized text comes through, but tables are not rebuilt: the detector needs ruled lines drawn in the PDF, and a scan is a picture, so expect one value per row in column A."},
        {"q": "Can I batch-convert multiple PDFs to Excel?", "a": "Yes — upload multiple PDFs and each is converted independently, then bundled into a ZIP of .xlsx files. Useful for processing a folder of monthly statements or invoices."},
        {"q": "Which tables convert most reliably?", "a": "Tables with clear ruled lines and one value per cell. Borderless tables are usually not detected at all, and merged cells or a table that breaks across pages (each page lands on its own sheet) usually need tidying in the spreadsheet afterwards."},
    ],
    "pdf-to-text": [
        {"q": "Is formatting preserved in the text output?", "a": "The tool extracts raw text only. Bold, italic, font sizes, and layout are not preserved — you get clean plain text."},
        {"q": "Can I extract text from a specific page range?", "a": "Not in this tool; it extracts every page. Pull the pages you need into a smaller PDF with Extract Pages first, then extract the text from that."},
        {"q": "How does it handle multi-column layouts?", "a": "It does not analyze the layout; text comes out in the order it is stored in the PDF. When a two-column document stores each column in turn, the columns come out one after the other; when it stores the page line by line, lines from the two columns are interleaved."},
    ],
    "pdf-to-image": [
        {"q": "What DPI should I use?", "a": "150 DPI (the default) is good for on-screen viewing. Use 300 DPI for printing, or 72 DPI for small, quick previews. Higher DPI means larger files."},
        {"q": "Which image formats are available?", "a": "JPG (the default: lossy, with much smaller files for photos and photographic scans) and PNG (lossless, best for text-heavy pages). Both are rendered on a white background, so neither keeps transparency."},
        {"q": "Can I convert just specific pages?", "a": "Not in this tool; every page is converted. Pull the pages you need into a smaller PDF with Extract Pages first, then convert that."},
    ],
    "heic-to-jpg": [
        {"q": "Why will nothing open my HEIC files?", "a": "HEIC is Apple's high-efficiency photo format. It halves the storage a photo needs, but support outside Apple's ecosystem is patchy, so Windows applications, older editors and many web upload forms simply reject the file. A JPG copy sidesteps all of that."},
        {"q": "How much quality is lost?", "a": "Very little at Standard or High. Compressed trades some fine detail for a smaller file. The conversion is lossy and one-way — the JPEG is re-encoded from the decoded photo — so keep the HEIC originals if they are your only copy."},
        {"q": "Why is the JPG bigger than the HEIC?", "a": "Because HEIC compresses far more efficiently than JPEG. Roughly doubling in size when you convert is normal and is the price of the compatibility you are buying."},
        {"q": "Are the GPS coordinates and camera details kept?", "a": "No. The JPEG is written without copying the EXIF block across, so location, camera model and capture time do not travel with the converted file. That is helpful before publishing a photo; run View EXIF on the original first if you need to read that data."},
        {"q": "Can I convert a whole camera roll?", "a": "Yes. Add the photos together; they are converted a few at a time and the batch comes back as a single ZIP. Each photo is still its own upload, so the 500 MB limit applies per file."},
        {"q": "What about Live Photos or depth effects?", "a": "Only the still image is converted. The motion attached to a Live Photo and the depth map behind a portrait-mode shot are not part of a JPEG and are not carried over."},
        {"q": "What happens to my photos after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "remove-exif": [
        {"q": "Why does image metadata matter?", "a": "A photo from a phone commonly records where and when it was taken and which device took it. Publish it unchanged and you publish that too. Stripping EXIF before something goes online is a small habit that prevents an avoidable disclosure."},
        {"q": "What exactly is removed?", "a": "The EXIF block, which is where the camera, timestamp and GPS coordinates live. The colour profile is preserved where the output format supports it, so the picture does not shift in appearance after cleaning."},
        {"q": "Are the pixels affected?", "a": "The image is written out again rather than edited in place, so a JPG passes through the encoder once more at the library's default quality. For most photos the difference is hard to see, but it is a new file, not a byte-for-byte copy — keep the original if it is your master."},
        {"q": "Can I clean a whole folder at once?", "a": "Yes, up to 100 images in a single request. More than one image comes back as a ZIP with the original filenames intact."},
        {"q": "How do I check what my photo is carrying?", "a": "Run View EXIF first. It reads the metadata and shows it, including GPS coordinates, so you can see what would have been published before you strip it."},
        {"q": "Does this remove a watermark or hidden text in the picture?", "a": "No. Anything drawn into the pixels is part of the image, not metadata. This tool only clears the data the camera and editing software attach alongside it."},
        {"q": "What happens to my images after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "image-compressor": [
        {"q": "How much smaller will my images get?", "a": "It depends on the picture, its format and the quality you choose. Photographs straight from a camera or phone usually shrink a great deal, because they are often saved at a higher quality than anyone needs. An image that has already been compressed hard has much less left to give."},
        {"q": "Why did my PNG barely shrink?", "a": "Because PNGs are only optimised losslessly here: the file is re-saved more efficiently, but no detail is thrown away and the quality setting has no effect. That saving is usually modest. If a photo was saved as PNG, converting it to JPG or WebP with Image Converter shrinks it far more."},
        {"q": "Which formats come back in which format?", "a": "PNG stays PNG and WebP stays WebP. Everything else — JPG, and formats such as BMP or TIFF — comes back as a JPG. Transparency is kept in PNG and WebP but discarded when the output is JPG."},
        {"q": "What quality setting should I use?", "a": "The default of 82 is a sensible starting point for photographs. Drop towards the sixties when size matters more than fine detail, and go higher when the image will be printed or edited further. Compare the result against the original rather than trusting the number alone."},
        {"q": "Is the compression reversible?", "a": "No. Detail removed during compression cannot be restored by raising the quality afterwards, so always keep your original file until you are happy with the result."},
        {"q": "Does it change the image dimensions?", "a": "No. Compression changes how the pixels are stored, not how many there are. To reduce the actual width and height — often the biggest single saving for a web image — use Resize and Crop Image first."},
        {"q": "Is metadata kept?", "a": "The compressed file is written fresh, so EXIF details such as camera model, timestamp and GPS position do not carry over. Use Remove EXIF when stripping metadata is the actual goal."},
        {"q": "What happens to my images after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "remove-background": [
        {"q": "How good is the cut-out?", "a": "Good on a clear subject against a distinct background, and noticeably weaker on fine detail. Hair, fur, foliage, glass and motion blur are where automatic cut-outs struggle, because the model has to decide a single yes or no for pixels that are genuinely part subject and part background."},
        {"q": "What is the difference between the two engines?", "a": "The in-browser engine downloads a compact model once and then runs on your own hardware, so the image is not uploaded for that path. The server engine needs no download and does not depend on your device's speed, but the picture is uploaded to be processed."},
        {"q": "Why is the result always a PNG?", "a": "Because the background is replaced with transparency, and JPG cannot store transparency. Saving the result as JPG afterwards would fill the cut-out area with a solid colour and undo the point of the exercise."},
        {"q": "Which formats can I upload?", "a": "JPG, PNG and WebP work with both engines, and the server engine rejects anything else. Convert a HEIC, TIFF or other format with Image Converter first."},
        {"q": "Can I put a new background behind the subject?", "a": "Not here — this tool produces the cut-out. Drop the resulting PNG onto a background in any editor, or use it directly in a document or presentation, where the transparency behaves as you would expect."},
        {"q": "The edges are not quite right. What can I do?", "a": "Crop tightly around the subject first so there is less background to judge, and prefer a source image where subject and background differ clearly in colour or focus. For a critical cut-out, expect to tidy the edges by hand afterwards."},
        {"q": "What happens to my image if I use the server engine?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "video-to-gif": [
        {"q": "Why is my GIF so large?", "a": "GIF stores every frame as a separate image and compresses poorly, so a few seconds of video can produce a file far bigger than the video itself. Lower the frame rate, reduce the width or shorten the clip."},
        {"q": "Can I choose which part of the video to use?", "a": "There are no start and end controls here; the whole clip is converted. Cut the section you want with Trim Media first, then convert the trimmed clip."},
        {"q": "Why do the colours look banded?", "a": "GIF allows at most 256 colours per frame, so gradients and skin tones show steps. That is a limit of the format; for smooth colour, share a short MP4 or WebM instead."},
        {"q": "Does the GIF include sound?", "a": "No. GIF is an image format and cannot carry audio."},
        {"q": "Why did my conversion fail on a long video?", "a": "Long or high-resolution clips take a long time to turn into frames and can exceed the processing time limit. Trim the clip and lower the width, then try again."},
        {"q": "What is a good setting for chat and social posts?", "a": "Around 10 frames per second at 480 pixels wide keeps motion readable and the file manageable. Raise the width only when the detail really matters."},
        {"q": "What happens to my video after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the video and the GIF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "compress-video": [
        {"q": "How much can a video be compressed?", "a": "It depends on the source. High-bitrate recordings, such as phone and camera footage, shrink the most; a video that is already heavily compressed may barely change at the default level."},
        {"q": "Does compression change the video resolution?", "a": "No. The resolution stays the same; only the bitrate is reduced. To lower the resolution too, run the video through Video Resizer."},
        {"q": "What output format is used?", "a": "The output is MP4 with H.264 video, which almost every device and browser can play."},
    ],
    "trim-media": [
        {"q": "Can I trim audio files too?", "a": "Yes. The tool supports both audio (MP3, WAV, OGG, FLAC) and video (MP4, WebM, MOV, AVI) files."},
        {"q": "Is the trimmed file re-encoded?", "a": "Audio is not: MP3, WAV, AAC, OGG and M4A are cut without re-encoding, and FLAC is rewritten losslessly. Video always is — H.264 for MP4, MOV and MKV, VP9 for WebM, MPEG-4 for AVI — so the file keeps its format but not its exact original encoding."},
        {"q": "How precise is the trimming?", "a": "Video cuts are frame-accurate, because the video is re-encoded. An audio file is copied, so its cut lands on the nearest compressed-audio frame, within a few hundredths of a second."},
    ],
    "base64": [
        {"q": "Can I encode files (not just text)?", "a": "No. This tool encodes and decodes text only; there is no file upload, and Base64 that holds binary data such as an image cannot be decoded to text here."},
        {"q": "Is there a size limit for encoding?", "a": "There is no fixed limit; everything runs in your browser, so very long text is limited only by your device. Keep in mind that Base64 output is approximately 33% larger than the original."},
        {"q": "What character set is used?", "a": "Standard Base64 (RFC 4648) using A-Z, a-z, 0-9, +, and /. URL-safe Base64 (with - and _ in place of + and /) is not supported."},
    ],
    "text-diff": [
        {"q": "What diff algorithm is used?", "a": "A line-by-line longest-common-subsequence diff, like Unix diff: each line is marked as added, removed or unchanged. There is no word-level highlighting within a changed line."},
        {"q": "Can I compare files directly?", "a": "Not as uploads: paste the contents of each file into the two panes. Any plain text works, including .txt, .csv, .json, .xml, .html, .css, .js and .py files."},
        {"q": "Is there a size limit for comparison?", "a": "Yes: roughly 2,000 lines per side. Larger inputs are refused so the page stays responsive, so compare long documents in sections."},
        {"q": "Can I compare code files?", "a": "Yes. The diff viewer works with any plain-text format. It highlights changes line by line, making it useful for comparing code, configs, or data files."},
    ],
    "image-upscaler": [
        {"q": "Does this use AI to add detail?", "a": "No, and this is worth being clear about. The enlargement uses Lanczos resampling, a high-quality mathematical filter. It produces smooth, clean edges rather than the invented texture an AI model would generate, which also means it cannot add detail the original never contained."},
        {"q": "Will a blurry photo become sharp?", "a": "No. Enlarging makes every existing pixel bigger, including the blur. Lanczos avoids the blockiness of a naive enlargement, but a soft or out-of-focus source stays soft at a larger size."},
        {"q": "What enlargement factors can I choose?", "a": "Two or four times. Anything else falls back to 2x. A 4x enlargement multiplies the pixel count by sixteen, so it is both slow and memory-hungry on a large source."},
        {"q": "Why was my image rejected as too large?", "a": "Because the enlarged result would be larger than 100 megapixels, the limit the server enforces to protect its memory. For a 4x enlargement that means a source of roughly 2,500 × 2,500 pixels at most. Choose 2x instead, or reduce the source first with Resize and Crop Image."},
        {"q": "What is this actually good for?", "a": "Making a small logo, icon or diagram usable at a bigger size, and getting a modest photo up to a required minimum dimension. It is not a way to recover detail from a low-quality image."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "audio-converter": [
        {"q": "Which format should I choose?", "a": "MP3 when you need something that plays everywhere. AAC for Apple devices and good quality at modest sizes. OGG for games and open-source software. FLAC to archive without loss, and WAV when an editor or device asks for uncompressed audio."},
        {"q": "Will converting improve the sound?", "a": "No. Converting a lossy file such as an MP3 to FLAC or WAV preserves exactly what the MP3 contains in a bigger file; detail removed earlier cannot come back."},
        {"q": "What bitrate should I pick?", "a": "192 kbps, the default, is a good general choice. Use 256 or 320 for music you care about, and 64 or 128 for speech, podcasts and voice memos where small size matters more."},
        {"q": "Does converting between lossy formats lose quality?", "a": "Yes, a little. Each lossy encode discards more detail, so MP3 to AAC or OGG to MP3 is a trade for compatibility. Start from the highest-quality source you have."},
        {"q": "Can I take the audio out of a video?", "a": "Use Extract Audio for that; it is built for pulling the soundtrack out of a video file."},
        {"q": "What happens to my file after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the audio file and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],

    # ── v1.1.0 + v1.2.0 additions ─────────────────────────────────────────
    "highlight-pdf": [
        {"q": "Are the highlights real PDF annotations or flattened images?", "a": "Real PDF annotations. They render in every PDF viewer and can be removed later if you reopen the file in an editor. Nothing about the underlying text is changed."},
        {"q": "Can I highlight multiple phrases at once?", "a": "Run the tool once per phrase. Each run preserves previous highlights, so you can layer different colors for different keywords."},
        {"q": "Does the highlighter respect case?", "a": "No. Matches are found regardless of case, and the Case sensitive switch currently makes no difference, so check the result when capitalisation matters."},
    ],
    "transcribe-audio": [
        {"q": "Is my recording uploaded?", "a": "Not with the on-device engine: the audio is decoded and transcribed in your browser. What is downloaded is the Whisper model itself, fetched once from a public model host and cached. If you choose your own API key, the audio goes from your browser directly to that provider, not through PrivaTools."},
        {"q": "Tiny or Base — which model should I use?", "a": "Base is noticeably more accurate, particularly with accents, background noise and unusual words, at roughly twice the download and a slower run. Start with Base unless your device is slow or the recording is very clear."},
        {"q": "Can I get subtitles?", "a": "Yes. Download the .srt file, which carries the timings with each line and loads into video editors and players. Review it, since automatic timings and punctuation are rarely perfect."},
        {"q": "Which languages does it understand?", "a": "Whisper is multilingual and detects the language itself. Accuracy is best for widely spoken languages and drops for less common ones, especially with the smaller Tiny model."},
        {"q": "Why is transcription slow?", "a": "The on-device engine runs on your own processor, so speed depends on your hardware and the recording length. A long meeting on a modest laptop takes time; your own API key moves the work to the provider."},
        {"q": "How accurate is it?", "a": "Good on clear speech, weaker on crosstalk, heavy accents, poor microphones and specialist vocabulary. Treat the transcript as a draft and check names and numbers before relying on it."},
    ],
    "chat-with-pdf": [
        {"q": "What leaves my device when I ask a question?", "a": "The document's extracted text and your question are sent from your browser straight to the AI provider you selected, using your key. They do not pass through PrivaTools, but that provider's terms and retention settings apply, so check them before sending confidential material."},
        {"q": "Do I need an API key?", "a": "Yes. The answers come from your provider's model, and your provider bills your account. A local server such as one running an open model on your own machine works too, through the OpenAI-compatible option."},
        {"q": "How is my API key stored?", "a": "By default it is saved encrypted in this browser's storage, or you can keep it for the session only. It is used from your browser for provider requests and is not sent to PrivaTools. Clearing it here does not revoke it with the provider."},
        {"q": "Can I trust the answers?", "a": "Treat them as a fast guide, not a source. Language models can misread tables, miss context or state things the document does not say. Verify figures and quotations against the PDF."},
        {"q": "Why does it say my PDF has no text?", "a": "Because it is probably a scan — images of pages with no text layer. Run OCR PDF to add one, then open the result here."},
        {"q": "Does it work on very long documents?", "a": "Long documents send a lot of text with each request, which costs more and can exceed what some models accept at once. Choose a model with a large context, or extract the relevant pages first."},
    ],
    "summarize-pdf": [
        {"q": "Is my PDF uploaded to PrivaTools?", "a": "No. The text is extracted in your browser, and with the default 'On this device' engine the summary is produced there too. What does get downloaded is the model: about 250 MB, fetched once from a public model host (Hugging Face) and then cached in this browser. If you switch to 'My own API key', the extracted text goes from your browser directly to the provider you chose, not through PrivaTools."},
        {"q": "How long does it take?", "a": "It depends on your device and the length of the document, because the default engine runs on your own processor. The first run also waits for the one-time model download. The progress readout shows pages read and chunks summarized, and long documents take noticeably longer than short ones."},
        {"q": "What languages are supported?", "a": "The on-device DistilBART model was trained on English news text, so it is only dependable for English documents. For other languages, use 'My own API key' with a multilingual model from your provider."},
        {"q": "How good is the on-device summary?", "a": "Modest. DistilBART is a small model that runs in a browser tab, so it gives a serviceable gist, not a nuanced analysis, and it can miss or distort details. Check anything important against the source. 'My own API key' gives better results at your provider's prices."},
        {"q": "What leaves my device when I use my own API key?", "a": "The extracted text of the PDF and the summarization instructions go from your browser directly to the provider you selected, using your key. PrivaTools does not relay the request. That provider's terms and retention settings then apply, so check them before sending confidential material."},
        {"q": "Is there a file size or page limit?", "a": "The PDF is not uploaded, so the server's 500 MB cap does not apply; the practical limit is your browser's memory and your patience. Very long PDFs are slow on the on-device engine because every chunk is summarized in turn."},
        {"q": "Why does my scanned PDF produce no summary?", "a": "A scan is a set of page images with no text layer, so there is nothing for the tool to read. Run OCR PDF first to add real text, then summarize the result."},
    ],
    "smart-redact": [
        {"q": "What does it detect?", "a": "Pattern matching finds email addresses, phone numbers, SSN-style numbers (3-2-4 digits), runs of 13 to 19 digits that look like card numbers, and numeric dates. The entity model adds people, organisations, locations and other named entities. It does not look for postal addresses, IP addresses or custom identifiers, so check the document for those yourself."},
        {"q": "Which parts run in my browser and which on the server?", "a": "Text extraction, pattern matching and the default entity model all run in your browser, so nothing is uploaded while you scan and review. When you apply, the PDF and the strings you approved are sent over HTTPS to the PrivaTools server, which writes the redactions in isolated temporary per-request storage; response cleanup removes the job's temporary files after the result is sent."},
        {"q": "What is sent if I use my own AI key?", "a": "The extracted text of the PDF goes from your browser directly to the provider you chose, using your key, so that provider's terms apply. Values the pattern pass already found, such as emails, phone numbers, SSNs and card numbers, are masked before the text is sent. Applying the redactions still happens on the PrivaTools server."},
        {"q": "Is the redaction reversible?", "a": "No. The server applies PyMuPDF redactions, which remove the matched text from the page content instead of drawing a box over it, and the file is rewritten without the removed objects. Document metadata is separate: run Strip Metadata afterwards if the author or title fields are sensitive. Bookmark titles and comments that repeat a redacted string are not changed either."},
        {"q": "How is this different from Redact PDF?", "a": "Redact PDF has you mark each area by hand. Smart Redact proposes candidates for you to approve, which is faster on long documents but only as good as the detection: patterns are dependable for well-formed emails and numbers, while names rely on the model and should always be reviewed."},
        {"q": "Will it catch everything?", "a": "No automatic detector does. The on-device entity model is English-trained and misses unusual names and initials, the patterns only match common formats, and text inside images is invisible to it. Treat the list as a first pass, then search the redacted PDF for names and numbers you know should be gone."},
        {"q": "What's the file size limit?", "a": "The server step accepts PDFs up to 500 MB. Detection runs in your browser, so very long documents are limited by your device's memory and take longer to scan. Fair-use rate limits apply to the server step."},
    ],
    "split-in-half": [
        {"q": "What is this for?", "a": "Scans of open books and magazines, where each scanned sheet holds two pages side by side. Cutting them apart gives a document that reads one page at a time, which suits phones, e-readers and OCR."},
        {"q": "Which direction should I choose?", "a": "Vertical for a two-page spread scanned side by side, which is the usual case. Horizontal for sheets where the two halves are stacked, such as some forms or tickets printed two to a page."},
        {"q": "Does it cut exactly down the middle?", "a": "Yes, it splits each page into two equal halves. If the spread was scanned off-centre, a little of one page may appear on the other; crop the scan first if the gutter is far from the middle."},
        {"q": "What order do the new pages come in?", "a": "Left then right for a vertical cut, top then bottom for a horizontal one, for each original page in turn — so a correctly scanned book reads in order."},
        {"q": "Does it reduce image quality?", "a": "No resampling is involved in the cut itself; each half shows the same content at the same resolution as the original page."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and split on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "pdf-to-svg": [
        {"q": "What kind of PDFs convert best?", "a": "Vector PDFs (drawn in Illustrator, Inkscape, Figma, LaTeX, etc.) convert into editable vector SVGs. Scanned/raster PDFs become SVGs containing embedded images."},
        {"q": "How many SVG files come back?", "a": "One per page. A multi-page PDF comes back as a ZIP of SVGs; a one-page PDF as a single SVG file, which currently downloads with a .zip name, so rename it to .svg."},
        {"q": "Can I edit the SVGs after?", "a": "Yes. Open them in any vector editor (Illustrator, Inkscape, Figma) to edit shapes and paths. Text is converted to outlines, so it keeps its exact look but cannot be edited as text, and links are not kept."},
    ],
    "pdf-to-html": [
        {"q": "How accurate is the conversion?", "a": "Each line of text becomes a paragraph with its font, size, bold, italics and color set as inline styles, and the pages follow one another. The original positions are not applied, so lines stack one under another; drawn lines, boxes, vector charts and links are left out."},
        {"q": "Are images included?", "a": "Yes. Embedded images come through as base64-encoded inline data URLs, so the HTML is fully self-contained — no external image files needed."},
        {"q": "Why convert PDF to HTML?", "a": "Web archiving, republishing offline documents online, reading a document in any browser without a PDF viewer, or any use where you need the content as a web page."},
    ],
    "pdf-to-rtf": [
        {"q": "What's RTF good for?", "a": "Rich Text Format opens as an editable document in most word processors (Word, Pages, LibreOffice, WordPad). This export carries the same text as a .txt file, in one font with a page break after each PDF page, so it is a simple way to move PDF text into a word processor. Useful for legacy or cross-platform document exchange."},
        {"q": "Are images preserved?", "a": "No. Only the text is exported, one PDF line per paragraph, in a single font without bold or italics. To keep images, bold and italics, try PDF to Word instead."},
        {"q": "Does it handle Unicode?", "a": "Yes. Non-ASCII characters are encoded via the standard RTF \\uN escape mechanism."},
    ],
    "web-optimize-pdf": [
        {"q": "What does linearization actually do?", "a": "It reorganizes the PDF byte layout so the first page's objects come first in the file. A byte-range-aware viewer can then start rendering the first page while the rest still downloads."},
        {"q": "Does it change file size?", "a": "Expect a small change, often an increase: linearization adds hint tables for the viewer and reorders the objects. Two small test files each grew by about 9 %."},
        {"q": "Do I need this for a PDF served from my own server?", "a": "Mainly for large PDFs viewed inline in a browser, where the first page can appear before the download finishes. A small PDF downloads quickly either way."},
    ],
    "split-by-text": [
        {"q": "Where exactly does each split happen?", "a": "At every page that contains your text: that page starts a new part. Choose a phrase that appears once, on the first page of each section, so the parts line up with the documents you expect."},
        {"q": "Why does it find nothing in my scanned PDF?", "a": "A scan is a picture of text with no text layer to search. Run OCR PDF first to add one, then split the result."},
        {"q": "Is the search case-sensitive?", "a": "Not by default: Invoice, INVOICE and invoice all match. Switch on case-sensitive matching when only one form should trigger a split."},
        {"q": "My phrase appears several times on some pages.", "a": "That only starts one part per page, but a phrase that also appears in running headers or on continuation pages will create extra splits. Use a phrase unique to the start of each section."},
        {"q": "What happens to the pages before the first match?", "a": "They are kept as the first part, so nothing is lost. If your phrase appears nowhere in the document, the tool stops and tells you rather than returning a single unchanged file."},
        {"q": "What is this typically used for?", "a": "Splitting a single export that holds many documents — invoices, payslips, statements or letters — back into one file per document."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and split on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "view-exif": [
        {"q": "What can EXIF data reveal?", "a": "More than most people expect: the exact time a photo was taken, the camera or phone that took it, the exposure settings, and often the precise location. For a holiday snap that is harmless; for a photo taken at home and posted publicly, it is an address."},
        {"q": "Why does my image show almost nothing?", "a": "Most social networks and messaging apps strip metadata when you upload, so a photo saved from one of them usually arrives bare. Screenshots and images exported by editors often carry little or nothing too."},
        {"q": "Does it show GPS coordinates?", "a": "Yes, when the camera recorded them and nothing has removed them since. That is the single most sensitive field in a typical photo, and the main reason to check before publishing."},
        {"q": "Does viewing the metadata change my file?", "a": "No. This tool only reads. To actually remove anything, use Remove EXIF, which writes a cleaned copy and leaves your original alone."},
        {"q": "Can I trust the timestamp?", "a": "Treat it as a strong hint rather than proof. It comes from the device's own clock, which may be wrong or set to another time zone, and metadata can be edited after the fact."},
        {"q": "What happens to my photo after I upload it?", "a": "It is uploaded over HTTPS and read on the PrivaTools server using local imaging libraries, not a third-party service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes it once the results have been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "jwt-decoder": [
        {"q": "Does this verify the token's signature?", "a": "No, and that matters. The tool decodes and displays the contents; it does not check the signature against a key. A token that decodes cleanly may still be forged or tampered with, so never treat a decoded token as trusted."},
        {"q": "Why can anyone read my token's payload?", "a": "Because a standard signed JWT is encoded, not encrypted. Base64url is reversible by anyone, which is why a JWT should never carry secrets such as passwords."},
        {"q": "Is my token sent anywhere?", "a": "No. Decoding runs in JavaScript on this page and the token is not uploaded to PrivaTools. Even so, treat a live production token like a password and avoid pasting it into places you do not control."},
        {"q": "It says the token needs three parts.", "a": "A signed JWT is three sections separated by two dots. A missing section usually means the token was truncated when copied, or it includes a prefix such as Bearer that should be removed."},
        {"q": "How do I read exp and iat?", "a": "They are Unix timestamps in seconds: iat is when the token was issued and exp when it expires. The tool converts them to dates and highlights an expired token."},
        {"q": "Can it decode encrypted tokens?", "a": "No. An encrypted token (JWE) has five parts and cannot be read without the key. This tool handles the common signed format."},
    ],
    "regex-tester": [
        {"q": "Which regex flavor does it use?", "a": "JavaScript RegExp (ECMAScript). The same engine that powers browser pattern matching. Most patterns are portable to Python re, PCRE, or Go regexp with minor adjustments."},
        {"q": "Is my test text saved anywhere?", "a": "No. Pattern and text are kept in browser state only. Refresh the page and they're gone. No server-side storage."},
        {"q": "How many matches can it handle?", "a": "Up to 1,000 matches are found and listed; past that the result says only the first 1,000 are shown. Each check runs in a separate worker and stops after one second, so a pattern that backtracks badly shows an error instead of freezing the page."},
    ],
    "timestamp-converter": [
        {"q": "How does it know if a number is seconds or milliseconds?", "a": "By magnitude: a number of 100,000,000,000 (10^11) or more is read as milliseconds, anything smaller as seconds. The 'Interpret numbers as' setting can force seconds or milliseconds, or you can paste an ISO 8601 string."},
        {"q": "Why is the local time different from the UTC time?", "a": "Your browser's timezone offset is applied. The UTC value is what's actually stored in the timestamp; local is just for human convenience."},
        {"q": "Can I generate a future timestamp?", "a": "Yes. Type or paste any past or future ISO date and you'll get the corresponding epoch. The relative phrase will say 'in X days' for the future."},
    ],
    "batch-compress-pdf": [
        {"q": "How many PDFs can I upload?", "a": "Between 2 and 50 files per batch. They are sent in one upload, so together they must fit within 500 MB."},
        {"q": "Are they compressed in parallel?", "a": "Yes. The server compresses up to four files at once in a shared pool of worker threads, so a large batch still takes longer than a single file."},
        {"q": "How much smaller will my files get?", "a": "It depends on how much waste a file carries. Batch Compress removes unused objects and compresses streams, but it does not touch images: in a test, a PDF made of one JPEG photo shrank by less than 0.1 %. For image compression, use Compress PDF, which offers Light, Recommended and Extreme levels."},
    ],
    "pdf-page-counter": [
        {"q": "How is this faster than opening each PDF?", "a": "You drop all the files at once instead of opening them one by one, and the server reads each page count without rendering any pages, so once the upload finishes the counts come back quickly."},
        {"q": "Does it work on encrypted PDFs?", "a": "Often. Files that only restrict printing or editing are counted normally, and some files that need a password to open are counted too. When a password-protected file keeps its page list encrypted, though, it shows 0 pages, so remove the password with Unlock PDF first. Files the tool cannot read at all are marked invalid."},
        {"q": "Useful for print pricing?", "a": "Yes. Add every file in a print job to get each file's page count and the combined total in one go, which is what a per-page quote needs."},
    ],
    "webp-to-jpg": [
        {"q": "Why convert WebP to JPG?", "a": "WebP is efficient but still refused by plenty of older software, print workflows and desktop applications. JPG is the format that opens essentially everywhere, which makes it the safe choice for sending a picture to someone whose tools you do not control."},
        {"q": "Will the image lose quality?", "a": "JPEG is a lossy format, so the conversion re-encodes the picture and throws away a little detail. There is no quality slider on this page; JPEGs are written at the imaging library's default quality of 75. For a photo at normal viewing size the difference is hard to see, but repeatedly converting the same picture back and forth will visibly soften it."},
        {"q": "What happens to transparency?", "a": "JPEG has no transparency. The alpha channel is discarded rather than blended onto a white page, so anything that was see-through takes the colour stored underneath it, which is usually black. Convert to PNG, WebP or TIFF if you need transparency kept. WebP to PNG is the usual choice when the image has a cut-out background."},
        {"q": "My WebP is animated. Why did I only get one frame?", "a": "Because JPG cannot hold an animation. Only the first frame of an animated WebP is read and converted; the rest are ignored. Convert the animation to a video or GIF instead if you need the movement."},
        {"q": "Is EXIF or camera metadata carried over?", "a": "No. The converter writes a fresh image and does not copy EXIF across, so camera model, capture time and any GPS coordinates are left behind. That is useful before publishing a photo, though it also means you should keep the original if you want that data."},
        {"q": "Can I convert a folder of WebP files at once?", "a": "Yes. Add as many as you like and they are converted one after another, each as its own request. A single image downloads by itself; for several, the page offers one ZIP containing them all. Heavy conversion routes are rate limited, so a very large batch will be paced."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "webp-to-png": [
        {"q": "Why convert WebP to PNG?", "a": "PNG is lossless and keeps transparency, so it is the right target for logos, screenshots, diagrams and anything with a cut-out background that has to drop into another document cleanly. It is also accepted by far more editors and operating systems than WebP."},
        {"q": "Does the PNG lose any quality?", "a": "The conversion itself is lossless: every pixel the WebP decodes to is written into the PNG unchanged. If the source was a lossy WebP, the detail it had already discarded cannot come back, so the PNG preserves the WebP exactly as it is rather than improving it."},
        {"q": "Is transparency preserved?", "a": "Yes. PNG supports an alpha channel, so see-through areas in the WebP stay see-through in the PNG. This is the main reason to pick PNG over JPG as the target."},
        {"q": "Why is the PNG so much bigger than the WebP?", "a": "PNG compresses losslessly, while most WebP files on the web are lossy. Giving up lossy compression typically costs several times the file size for a photograph. Flat graphics and screenshots grow far less, because lossless compression suits them well."},
        {"q": "My animated WebP only produced one image.", "a": "That is expected. A plain PNG holds a single frame, so only the first frame of an animated WebP is converted and the animation itself is not carried over."},
        {"q": "Does it keep EXIF metadata?", "a": "No. The converter writes a fresh image and does not copy EXIF across, so camera model, capture time and any GPS coordinates are left behind. That is useful before publishing a photo, though it also means you should keep the original if you want that data."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "heic-to-png": [
        {"q": "What is HEIC and why convert it?", "a": "HEIC is the high-efficiency format iPhones use by default. It stores a photo in roughly half the space of a comparable JPG, but plenty of software outside Apple's ecosystem cannot open it, which is why a converted copy is often needed."},
        {"q": "Should I choose PNG or JPG?", "a": "PNG is lossless, so it is the better target if you are going to edit the photo further. For sharing or attaching a holiday photo, HEIC to JPG produces a far smaller file at a quality nobody will question."},
        {"q": "Is the conversion lossless?", "a": "The PNG stores exactly what the HEIC decodes to, so nothing further is lost. It cannot undo the compression the camera already applied, and the file will be considerably larger than the HEIC because PNG does not compress photographs efficiently."},
        {"q": "What happens to the location and camera data?", "a": "It is not carried into the PNG. The converter writes a fresh image without copying EXIF, so GPS coordinates, camera model and capture time are dropped. Use View EXIF on the original first if you want to read that information before it goes."},
        {"q": "My HEIC would not convert. What now?", "a": "HEIC support depends on the decoder available on the server, and some files, particularly Live Photos and depth-map variants, will not open. Converting the photo to JPG on the phone and working from that is the reliable fallback."},
        {"q": "What happens to my photo after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],

    # ── v1.4.0 — additional format converter aliases ─────────────────────
    "jpg-to-png": [
        {"q": "Does converting JPG to PNG improve the picture?", "a": "No, and this is the most common misunderstanding about the conversion. PNG stores the pixels the JPG decodes to without further loss, but the detail and the compression artefacts JPG already baked in stay exactly as they are. You get a larger file of the same image, not a better one."},
        {"q": "So when is it worth doing?", "a": "When something downstream needs PNG: an editor that will not open JPG, a workflow that requires lossless input, or an image you are about to edit repeatedly and do not want to re-compress at every save."},
        {"q": "Will the PNG have a transparent background?", "a": "No. A JPG has no transparency to recover, so the PNG gets a fully opaque copy of the image. Removing a background is a separate job — Remove Background does that."},
        {"q": "Why is the PNG several times larger?", "a": "Because lossless compression cannot match what JPG achieves by discarding detail. A photograph usually grows substantially. That is the expected cost of the format, not a fault in the conversion."},
        {"q": "Is the camera metadata kept?", "a": "No. The converter writes a fresh image and does not copy EXIF across, so camera model, capture time and any GPS coordinates are left behind. That is useful before publishing a photo, though it also means you should keep the original if you want that data."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "png-to-jpg": [
        {"q": "Why convert PNG to JPG?", "a": "Mostly to make a photograph smaller. PNG stores photographic detail losslessly, which is wasteful for a camera image, and some upload forms and email systems only accept JPG. For screenshots and graphics with flat colour, PNG is usually the better format to keep."},
        {"q": "Why did my transparent background turn black?", "a": "Because JPG cannot store transparency. The alpha channel is dropped rather than flattened onto white, so transparent pixels fall back to the colour recorded underneath them, which in most PNGs is black. If you need a white background, add one in an image editor before converting, or keep the PNG."},
        {"q": "How much smaller will the file be?", "a": "For a photograph, usually several times smaller. For a screenshot, a logo or a diagram the saving is much less dramatic and the sharp edges pick up visible fringing, so those are better left as PNG."},
        {"q": "Can I choose the JPEG quality?", "a": "Not on this page. JPEG is a lossy format, so the conversion re-encodes the picture and throws away a little detail. There is no quality slider on this page; JPEGs are written at the imaging library's default quality of 75. If you want to control the trade-off, use Image Compressor, which exposes a quality setting."},
        {"q": "Is any metadata carried over?", "a": "No. The converter writes a fresh image and does not copy EXIF across, so camera model, capture time and any GPS coordinates are left behind. That is useful before publishing a photo, though it also means you should keep the original if you want that data."},
        {"q": "Can I convert lots of PNGs in one go?", "a": "Yes. Add them all and each is converted in turn as its own request. One file downloads directly; several are offered as a single ZIP. Conversion routes are rate limited, so a very large batch is paced rather than run all at once."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "jpg-to-webp": [
        {"q": "Why convert JPG to WebP?", "a": "To publish a smaller file on the web. WebP generally reaches the same visual quality as JPG in fewer bytes, which is why it has become a common format for page images. Every current browser displays it."},
        {"q": "Is the WebP lossless?", "a": "No. The converter writes WebP with its default lossy settings, so the image is re-encoded. Because your JPG was already lossy, this is a second round of compression: the result is smaller, but it is not a pixel-perfect copy of the JPG."},
        {"q": "Will the file always get smaller?", "a": "Usually, but not always. An already heavily compressed JPG can come out around the same size or occasionally larger, because there is little redundancy left to exploit. Compare the two files before replacing the original."},
        {"q": "Where might a WebP not work?", "a": "Older desktop software, some print and office applications, and a few email clients still refuse WebP. Keep a JPG copy for anything you have to send to someone else."},
        {"q": "Does EXIF survive the conversion?", "a": "No. The converter writes a fresh image and does not copy EXIF across, so camera model, capture time and any GPS coordinates are left behind. That is useful before publishing a photo, though it also means you should keep the original if you want that data."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "png-to-webp": [
        {"q": "Why convert PNG to WebP?", "a": "To cut page weight. WebP usually stores the same picture in noticeably fewer bytes than PNG, which matters when the image is part of a web page rather than an archive."},
        {"q": "Is transparency preserved?", "a": "Yes. WebP supports an alpha channel, so a cut-out PNG stays cut out. This is the main reason to pick WebP rather than JPG when shrinking a graphic with a transparent background."},
        {"q": "Is the conversion lossless?", "a": "No. WebP is written with its default lossy settings here, so a PNG that was pixel-perfect becomes an approximation. For flat graphics and text that is often invisible, but if you need an exact copy, keep the PNG."},
        {"q": "Will a screenshot still look sharp?", "a": "Usually yes, though lossy compression can soften very fine text and hard edges. Check the result at full size before you replace the original, especially for a screenshot people are meant to read."},
        {"q": "Is any metadata carried across?", "a": "No. The converter writes a fresh image and does not copy EXIF across, so camera model, capture time and any GPS coordinates are left behind. That is useful before publishing a photo, though it also means you should keep the original if you want that data."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "tiff-to-jpg": [
        {"q": "Why convert TIFF to JPG?", "a": "Because TIFF files are large and awkward to share. A scan or a print-ready image can be tens of megabytes; the JPG version is small enough to email or upload and opens on any device."},
        {"q": "My TIFF has several pages. Why did I get one image?", "a": "Only the first page is converted. A multi-page TIFF, which is what many scanners produce, holds a sequence of images, and JPG holds exactly one. If you need every page, convert the TIFF to PDF first and work from there."},
        {"q": "How much quality is lost?", "a": "JPEG is a lossy format, so the conversion re-encodes the picture and throws away a little detail. There is no quality slider on this page; JPEGs are written at the imaging library's default quality of 75. Going from a lossless TIFF to JPG is a real, one-way reduction, so keep the TIFF if it is your archival master."},
        {"q": "What happens to transparency?", "a": "JPEG has no transparency. The alpha channel is discarded rather than blended onto a white page, so anything that was see-through takes the colour stored underneath it, which is usually black. Convert to PNG, WebP or TIFF if you need transparency kept."},
        {"q": "Will a CMYK print TIFF convert correctly?", "a": "Colours may shift. JPG files for general use are RGB, and a print-oriented CMYK source has to be interpreted to get there, which is not colour-managed here. For prepress work, keep the original and convert in software that handles colour profiles."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "tiff-to-png": [
        {"q": "Why convert TIFF to PNG?", "a": "PNG keeps the lossless quality a TIFF is usually kept for, while being far more portable: browsers, chat apps and web tools all display PNG, and most of them will not touch a TIFF."},
        {"q": "Is anything lost?", "a": "Not in the pixels. Both formats are lossless, so the PNG is a faithful copy of the first page. What is dropped is TIFF-specific baggage: extra pages, embedded metadata and any print-oriented colour information."},
        {"q": "Does a multi-page TIFF become several PNGs?", "a": "No, only the first page is converted. A scanner that produced a multi-page TIFF is best handled by converting to PDF instead, which keeps every page in one document."},
        {"q": "Will the PNG be smaller?", "a": "Usually, because many TIFFs are stored uncompressed while PNG always compresses losslessly. The saving depends entirely on the source; a TIFF that was already compressed may barely change."},
        {"q": "Is transparency kept?", "a": "Where the TIFF has an alpha channel, yes: PNG supports transparency and it survives the conversion. A flattened scan has no transparency to preserve in the first place."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "bmp-to-jpg": [
        {"q": "Why convert BMP to JPG?", "a": "Size. BMP stores every pixel uncompressed, so even a modest image can run to many megabytes. JPG compresses it to a fraction of that, which is what makes it practical to send or upload."},
        {"q": "How much smaller will it get?", "a": "Dramatically, in most cases: uncompressed bitmaps have a great deal of redundancy for a lossy encoder to remove. The exact ratio depends on the image, with photographs shrinking much more than flat graphics."},
        {"q": "Will it look the same?", "a": "JPEG is a lossy format, so the conversion re-encodes the picture and throws away a little detail. There is no quality slider on this page; JPEGs are written at the imaging library's default quality of 75. On a photograph it is hard to tell the two apart. On a screenshot or a diagram with sharp edges, JPG's fringing is more noticeable — BMP to PNG is the better choice for those."},
        {"q": "What about transparency?", "a": "Standard BMP has no usable transparency and JPG has none at all, so there is nothing to carry over. If your source really does have an alpha channel, convert to PNG instead."},
        {"q": "Why would anyone still have BMP files?", "a": "They are produced by older Windows software, some scanners, and industrial or embedded equipment that only writes uncompressed bitmaps. Converting is usually the first step in making that output usable anywhere else."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "bmp-to-png": [
        {"q": "Why convert BMP to PNG?", "a": "PNG gives you the same lossless pixels in a much smaller file, and it is accepted everywhere BMP is not — browsers, chat apps, document editors and web forms all handle PNG."},
        {"q": "Is any quality lost?", "a": "None. Both formats are lossless, so the PNG holds exactly the same pixels as the bitmap. The only thing that changes is how efficiently they are stored."},
        {"q": "How much smaller will the PNG be?", "a": "Substantially, for most bitmaps. PNG's lossless compression works especially well on screenshots, diagrams and anything with areas of flat colour, which is what BMP files frequently contain."},
        {"q": "Is this better than converting to JPG?", "a": "For screenshots, logos and line art, yes: PNG stays sharp where JPG introduces fringing around edges and text. For a photograph where small size matters more than perfection, BMP to JPG will produce a much smaller file."},
        {"q": "Will transparency be added?", "a": "No. The conversion copies what is in the bitmap, and a standard BMP is fully opaque. PNG supports transparency, but nothing creates it for you here."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "gif-to-jpg": [
        {"q": "My GIF was animated and I only got one picture.", "a": "That is how it works: JPG holds a single still image, so only the first frame of the animation is converted. To keep the movement, convert the GIF to a video with GIF to MP4 instead."},
        {"q": "Why convert GIF to JPG?", "a": "Usually to get a normal still photo out of a GIF, or to shrink a large one. GIF is limited to 256 colours and stores every frame as a separate image, which makes it a poor container for anything photographic."},
        {"q": "Will the colours look right?", "a": "The JPG can only contain the colours the GIF had. A photograph that was reduced to a 256-colour palette will still show banding after conversion — the conversion cannot restore shades that were not in the GIF to begin with."},
        {"q": "What happens to a transparent GIF?", "a": "JPEG has no transparency. A GIF marks one palette colour as see-through, and after conversion that colour simply shows, so transparent areas take on whatever colour the GIF assigned to them. Convert to PNG if you need the transparency kept."},
        {"q": "Is the file smaller?", "a": "For a single frame from an animation, usually much smaller, since you are discarding every other frame. For a one-frame GIF the difference depends on the picture. JPEG is a lossy format, so the conversion re-encodes the picture and throws away a little detail. There is no quality slider on this page; JPEGs are written at the imaging library's default quality of 75."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "gif-to-png": [
        {"q": "Does this keep the animation?", "a": "No. A plain PNG holds one frame, so only the first frame of an animated GIF is converted. Use GIF to MP4 if you want the animation in a modern format."},
        {"q": "Why convert GIF to PNG?", "a": "PNG handles far more colours than GIF's 256-colour limit and compresses flat graphics better, so a logo or diagram saved as a GIF is almost always better off as a PNG."},
        {"q": "Will the extra colours come back?", "a": "No. PNG can store millions of colours, but the GIF only contains the 256 it was reduced to, and the conversion copies what is there. The banding in a photographic GIF stays."},
        {"q": "Is transparency preserved?", "a": "Yes, where the GIF has it. GIF transparency is a single fully transparent colour rather than a soft alpha channel, so edges may look hard, but the see-through areas remain see-through in the PNG."},
        {"q": "Is the conversion lossless?", "a": "Yes, in the sense that every pixel the GIF decodes to is preserved exactly. Quality already given up when the image was turned into a GIF cannot be recovered."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "m4a-to-mp3": [
        {"q": "Why convert M4A to MP3?", "a": "M4A (AAC inside an MP4 container) isn't universally supported — older car stereos, some Android players, and many legacy devices won't play it. MP3 works everywhere."},
        {"q": "Will the audio quality drop?", "a": "Slightly. M4A's AAC codec is more efficient than MP3, so at the same bitrate AAC sounds better. This page always encodes at 192 kbps, which is hard to tell from the source in casual listening; for another bitrate, use Audio Converter."},
        {"q": "Does it work for iPhone voice memos?", "a": "Yes — voice memos export as M4A and convert cleanly to MP3 here."},
    ],
    "mp4-to-mp3": [
        {"q": "Does this work for any MP4?", "a": "Yes — as long as the MP4 has an audio track. Music videos, lecture recordings, podcasts, screen recordings with narration, all work."},
        {"q": "What about file size?", "a": "The MP3's size depends on the length, not on the video: it is encoded at about 128 kbps, close to 1 MB per minute of stereo audio. This page takes MP4 files up to 200 MB."},
        {"q": "Is the video kept?", "a": "No — only the audio track is extracted. If you also need the video, keep the original MP4."},
    ],
    "mov-to-mp4": [
        {"q": "Why convert MOV to MP4?", "a": "MOV is Apple's QuickTime format. While Macs play it natively, Windows, Android, and most streaming platforms prefer MP4. The codecs inside are often the same (H.264), but this tool re-encodes the video anyway rather than only changing the container."},
        {"q": "Will I lose quality?", "a": "A little. Every file is re-encoded as H.264 at CRF 23 with AAC audio instead of being copied, so the result is not bit-for-bit the original."},
        {"q": "Does it preserve audio?", "a": "Yes, re-encoded as AAC. If the file has several audio tracks, only one is kept."},
    ],
    "avi-to-mp4": [
        {"q": "Why convert AVI to MP4?", "a": "AVI is an old Microsoft container with poor support for modern codecs and metadata. MP4 is the universal standard — every modern device, browser, and editor plays it."},
        {"q": "What if my AVI uses DivX or Xvid?", "a": "FFmpeg re-encodes the video to H.264 inside the MP4 container, so any source codec is handled."},
        {"q": "Will the file get bigger or smaller?", "a": "Usually similar or smaller. Old AVIs often used inefficient codecs; modern H.264 typically achieves the same quality at a smaller size."},
    ],
    "webm-to-mp4": [
        {"q": "Why convert WebM to MP4?", "a": "WebM (VP8/VP9 codecs) isn't supported by Safari on iOS before 17.4, older Android, or many editing programs. MP4 with H.264 is universal."},
        {"q": "Does the audio survive?", "a": "Yes. WebM's Opus or Vorbis audio is re-encoded to AAC inside the MP4 container."},
        {"q": "Will I lose quality?", "a": "Re-encoding always sacrifices a little quality. The video is encoded as H.264 at CRF 23, the encoder's standard quality-based setting, rather than at a fixed bitrate."},
    ],
    "mp4-to-webm": [
        {"q": "Why convert MP4 to WebM?", "a": "WebM uses VP9, which is royalty-free and often produces smaller files than H.264 at the same quality. Ideal for hosting video on the open web."},
        {"q": "Will every browser play it?", "a": "Every modern desktop browser plays WebM. Safari on iOS plays it from iOS 17.4 onward. For maximum compatibility, MP4 is still safer."},
        {"q": "How much smaller will it be?", "a": "It depends on the source. The video is encoded at about 1 Mbit/s whatever the input, so a high-bitrate MP4 shrinks a lot while a low-bitrate one can come out larger. VP9 is also far slower to encode than H.264, so a long or high-resolution video can run into the three-minute processing limit."},
    ],
    "yaml-to-json": [
        {"q": "Is it 100% in my browser?", "a": "Yes. The conversion runs in JavaScript on this page, so the YAML you paste is not uploaded to PrivaTools."},
        {"q": "Which YAML features are supported?", "a": "Scalars, lists, nested maps, quoted strings, comments (left out of the JSON) and flow-style arrays. Inline objects work only with JSON-style quoted keys. Multi-line block strings (| and >), anchors, tags and multi-document streams are not supported and show an error instead of converting wrongly."},
        {"q": "What if my YAML has a parse error?", "a": "The error message appears in the output area with line context. Fix the YAML and the conversion updates instantly."},
    ],
    "json-to-yaml": [
        {"q": "Is it 100% in my browser?", "a": "Yes. The JSON never leaves your device — pure-browser conversion, no upload."},
        {"q": "Will it format the YAML correctly?", "a": "Yes — proper indentation (2 spaces), keys with special characters get quoted, lists get the bullet-point style by default. Output is ready to paste into a Kubernetes or GitHub Actions file."},
        {"q": "What if the JSON is invalid?", "a": "An error appears in the output area. Fix the JSON and the conversion updates live."},
    ],
    "case-converter": [
        {"q": "Which case formats are supported?", "a": "12: lowercase, UPPERCASE, Title Case, Sentence case, camelCase, PascalCase, snake_case, kebab-case, CONSTANT_CASE, dot.case, path/case, and iNVERSE."},
        {"q": "Will it handle existing camelCase or snake_case input correctly?", "a": "Yes. The tool detects word boundaries from underscores, hyphens, spaces, and lowercase→uppercase transitions, so camelCase, PascalCase, snake_case, kebab-case, CONSTANT_CASE and plain words convert cleanly. Dots and slashes are not word breaks, and an acronym such as XML in XMLHttpRequest stays joined to the next word."},
        {"q": "Does it run in my browser?", "a": "Yes — 100%. Your text never leaves the page. Useful for renaming variables, generating CSS class names, or normalizing identifiers without exposing them to a server."},
    ],
    "cron-parser": [
        {"q": "Does it support Quartz cron with seconds?", "a": "No. This tool intentionally supports standard 5-field cron because that is what Linux crontab, many schedulers, and most deployment platforms use."},
        {"q": "Which timezone is used for next runs?", "a": "Your browser's local timezone. The expression itself is not uploaded or evaluated on the server."},
        {"q": "Can it validate ranges and steps?", "a": "Yes. It catches invalid ranges, bad steps, out-of-bounds values, and expressions with the wrong number of fields."},
    ],
    "sql-formatter": [
        {"q": "Is this a full SQL parser?", "a": "No. It is a lightweight formatter for readable query cleanup. It does not execute, optimize, or validate SQL against a database schema."},
        {"q": "Will my query be uploaded?", "a": "No. Formatting happens in browser JavaScript, which is useful for production query snippets and private table names."},
        {"q": "Which SQL dialects work?", "a": "Common SELECT, JOIN, WHERE, GROUP BY, ORDER BY, INSERT, UPDATE, and DELETE syntax formats well across Postgres, MySQL, SQLite, and similar dialects."},
    ],
    "graphql-formatter": [
        {"q": "Does it need my GraphQL schema?", "a": "No. The formatter only structures the query text and does not introspect or validate against a schema."},
        {"q": "Can it format mutations and fragments?", "a": "Yes. Queries, mutations, fragments, arguments, arrays, and nested selection sets are handled."},
        {"q": "Is it private?", "a": "Yes. The GraphQL text is formatted locally in your browser."},
    ],
    "yaml-toml-converter": [
        {"q": "Are YAML anchors and custom tags supported?", "a": "No. The converter is designed for common app config: nested maps, strings, numbers, booleans, and simple arrays."},
        {"q": "Will comments be preserved?", "a": "No. Comments are omitted during conversion because TOML and YAML comments do not map cleanly through a simple object representation."},
        {"q": "Does it upload config files?", "a": "No. Conversion runs locally in your browser."},
    ],
    "gitignore-generator": [
        {"q": "Does it call the toptal/gitignore API?", "a": "No. The templates are bundled in the app so the generator works offline and does not leak your selected stack."},
        {"q": "Can I combine multiple templates?", "a": "Yes. Select any combination and the generated .gitignore groups each template under a comment header."},
        {"q": "Can I download the file directly?", "a": "Yes. You can copy the text or download a .gitignore file from the browser."},
    ],
    "semver-bumper": [
        {"q": "Does it handle prerelease versions?", "a": "Yes. Versions like 1.2.3-beta.1 are accepted, and the prerelease bump increments the trailing number when present."},
        {"q": "Does it edit package.json?", "a": "No. It only calculates version strings so you can copy the value into your release workflow."},
        {"q": "What rules does it follow?", "a": "Patch increments the third number, minor increments the second and resets patch, major increments the first and resets minor and patch. A prerelease is released instead of bumped: patch turns 1.2.3-beta.1 into 1.2.3. Build metadata is dropped."},
    ],
    "env-validator": [
        {"q": "Does this replace secret scanning?", "a": "No. It is a fast syntax and hygiene check. Use dedicated secret scanning before committing any real credentials."},
        {"q": "Will it reveal my secrets to PrivaTools?", "a": "No. The .env text stays in browser memory and is never sent to the backend."},
        {"q": "What checks are included?", "a": "Missing equals signs, invalid variable names, duplicate keys, empty values, unquoted spaces, and short-looking secret values."},
    ],
    "json-to-csv-schema": [
        {"q": "How are nested objects handled?", "a": "Nested keys are flattened with dot notation, such as user.email or billing.address.city."},
        {"q": "What schema is inferred?", "a": "The tool infers simple column types: empty, boolean, number, date, or string, plus value coverage per column."},
        {"q": "Does large JSON get uploaded?", "a": "No. Parsing, schema inference, and CSV generation all run in your browser."},
    ],
    # ── Phase 7 — competitor-gap tools (v1.5.0) ──────────────────────────
    "mute-video": [
        {"q": "Is the video quality preserved?", "a": "Yes. The video track is stream-copied without re-encoding, so its data is identical to the original; only the container is rewritten without the audio."},
        {"q": "Will the file get smaller?", "a": "Yes, by the size of the audio track, which depends on the audio's bitrate and length. The video portion is unchanged."},
        {"q": "Can I just mute the audio instead of removing it?", "a": "This tool removes the audio track entirely; it cannot put a silent track in its place. A video without an audio track simply plays silently."},
    ],
    "reverse-video": [
        {"q": "Why is reversing slow?", "a": "Reversing requires re-encoding the whole video — FFmpeg has to read every frame, store them, then write them out in reverse order. RAM usage grows with video length."},
        {"q": "Will the audio sound weird?", "a": "Yes — speech becomes gibberish but music can sound interesting. The audio is reversed with the video so they stay in sync."},
        {"q": "What's a good use case?", "a": "Reverse-loop animations, training analysis (replay a fall or trick backwards), creative edits, debugging frame-by-frame issues."},
    ],
    "video-speed": [
        {"q": "Will fast-forward make voices sound chipmunky?", "a": "No — we use FFmpeg's atempo filter which pitch-corrects audio. A 2× speedup sounds like fast speech, not a chipmunk."},
        {"q": "What's the maximum slowdown / speedup?", "a": "From 0.3× (a little under a third of normal speed) to 3.95× (almost four times faster). The slider's 0.25× end and the 4× preset are outside what the server accepts."},
        {"q": "Does it work for slow-motion footage?", "a": "Sort of — for true high-quality slow-motion you need video captured at higher FPS originally. This tool stretches the existing frames in time, so very slow speeds get a duplicated-frame look."},
    ],
    "audio-trim": [
        {"q": "How precise are the start/end times?", "a": "Times can be set to the millisecond. Because the audio is copied rather than re-encoded, a cut lands on the nearest compressed-audio frame, within a few hundredths of a second. Trim Media copies audio the same way."},
        {"q": "Will trimming reduce audio quality?", "a": "No — we use stream-copy mode which preserves the original bytes. The trimmed file is identical quality to the source."},
        {"q": "What format does it output?", "a": "Same format as input. Trim an MP3 → get an MP3. Trim a FLAC → get a FLAC, rewritten losslessly; every other format is copied without re-encoding."},
    ],
    "image-palette": [
        {"q": "How are the colors picked?", "a": "We shrink the image to fit within 400×400 for speed, then run a fast octree quantization to find the N most-dominant colors. Percentages are based on pixel coverage."},
        {"q": "Will it find the brand color from a logo?", "a": "Usually yes — logos have a few dominant colors that octree picks up well. For logos on white backgrounds, asking for 6 colors typically gives 1 white + the actual brand colors."},
        {"q": "Can I get more than 24 colors?", "a": "Not in this tool — beyond 24 the palette becomes too noisy to be useful. For full palette analysis, export the image to a design tool."},
    ],
    "pixelate-image": [
        {"q": "Pixelate vs blur — which should I use?", "a": "Pixelate reads clearly as 'censored'; blur looks softer and can pass for an out-of-focus photo. Neither is a guaranteed redaction: pixelated or blurred text can sometimes be reconstructed, especially at low strength. For content that must never be recovered, cover it with a solid box instead."},
        {"q": "Can I select a specific region?", "a": "This tool applies the effect to the whole image. For region-selective censoring, upload to an image editor first (e.g. our Edit PDF for documents) and white-out or rectangle over the area."},
        {"q": "Does the original get stored?", "a": "No. The image is uploaded over HTTPS, processed in isolated temporary per-request storage, and removed by response cleanup after the result is sent; a background sweep clears anything left behind by an interrupted request. It is not added to an account or file library."},
    ],
    "rotate-image": [
        {"q": "Will rotation lose quality?", "a": "90°, 180° and 270° rotations move pixels without resampling, so a PNG comes out lossless. JPG and WEBP files are re-saved at quality 92, which adds a little compression loss. Arbitrary angles re-sample using bicubic interpolation which is visually near-lossless but technically introduces sub-pixel smoothing."},
        {"q": "Why is my output bigger than the input?", "a": "For non-90° angles, the rotated rectangle no longer fits in the original bounding box. The canvas auto-expands so the whole rotated image is visible (corners get transparent/white padding)."},
        {"q": "Does PNG/WEBP transparency carry over?", "a": "Yes — if the image has an alpha channel, it is preserved and rotated corners are transparent. Images without transparency, including every JPG, get white corners."},
        {"q": "Is metadata preserved?", "a": "Partly. The rotated copy keeps the DPI setting and, for an RGB image such as a phone photo, the colour profile, so colours and print resolution stay the same. Other metadata is not carried over, including the EXIF data with camera details, the date taken and location. The orientation tag a phone or camera records is applied to the pixels before rotating, so the angle you pick turns the photo as your phone shows it."},
    ],
    "flip-image": [
        {"q": "Horizontal vs vertical — when do I use which?", "a": "Horizontal flip mirrors left↔right — the most common use is fixing selfies that come out mirrored. Vertical flip mirrors top↔bottom, like a reflection in water, which suits design layouts. It is not the same as turning a picture upside down: for an upside-down scan, use Rotate Image at 180°."},
        {"q": "Does flipping change the file size?", "a": "It can. Flipping is a pure pixel rearrangement, and a PNG comes out close to its original size. JPG and WEBP files are re-encoded at quality 92, so a photo that was saved at a lower quality can grow noticeably."},
        {"q": "Is metadata preserved?", "a": "Partly. The flipped copy keeps the DPI setting and, for an RGB image such as a phone photo, the colour profile, so colours and print resolution stay the same. Other metadata is not carried over, including the EXIF data with camera details, the date taken and location. The orientation tag a phone or camera records is applied to the pixels before the flip, so a photo stored sideways comes out upright."},
    ],

    # ── Auto-generated content for v1.3.1 SEO coverage push ──────────────
    "add-attachment": [
        {"q": "What's the difference between an attachment and embedding?", "a": "An attachment is a file stored inside the PDF that the reader can open separately. Embedding means inlining content (images, fonts) into the page itself. Use attachments when you want recipients to access the supporting file but keep the visible PDF clean."},
        {"q": "Can I attach more than one file?", "a": "Yes, one per run: run the tool again on the result to add the next file. Earlier attachments stay in place."},
        {"q": "How big can the embedded file be?", "a": "Up to 50 MB, and the PDF and the attachment together must fit within one 500 MB upload. The attachment is stored compressed, so the PDF grows by about its size, or much less for text-like files that compress well."},
    ],
    "add-hyperlinks": [
        {"q": "Can I link to other pages in the same PDF?", "a": "No. It only links web addresses already written in the text. For jumps to pages within the document, add bookmarks with the Bookmarks tool."},
        {"q": "Are the links visible to the user?", "a": "The clickable area is invisible and sits over the address text, which looks as it did before. To make links stand out, draw an underline with Edit PDF."},
        {"q": "Will hyperlinks survive printing or PDF/A conversion?", "a": "A link has no printed appearance, so paper copies show only the address text. PrivaTools' PDF to PDF/A keeps the links: it re-saves the file with a PDF/A-2b label and does not remove annotations."},
    ],
    "add-shapes": [
        {"q": "Are shapes flattened into the page?", "a": "Yes — shapes become part of the page's content stream, not annotations. They can't be moved or deleted afterwards without re-editing the PDF."},
        {"q": "Can I draw filled or only outlined shapes?", "a": "Both. Pick a fill color for a filled shape; leave the fill empty and only the outline is drawn. Set both for an outlined fill."},
        {"q": "What about transparency?", "a": "Not supported: shapes are drawn in solid colors. Leave the fill empty to keep the content inside a rectangle or circle visible."},
    ],
    "alternate-mix": [
        {"q": "When would I use this?", "a": "The classic case is double-sided scanning on a single-sided scanner: scan the odd pages, flip the stack, scan the even pages in reverse, then alternate-mix them with reverse-alternate."},
        {"q": "What if the PDFs have different page counts?", "a": "PrivaTools alternates pages until one source is exhausted, then appends the remaining pages from the longer source at the end."},
        {"q": "Does this preserve bookmarks?", "a": "No. Bookmarks from the originals are dropped because they would point to incorrect pages after interleaving."},
    ],
    "annotate-pdf": [
        {"q": "Are annotations flattened?", "a": "No. They stay as separate annotations, so anyone with a PDF editor can move, change or delete them."},
        {"q": "Can I attach sticky-note comments?", "a": "Yes. Choose Sticky note and type its text; readers display it as an icon that opens a popup with the text on click. No author name is set."},
        {"q": "Do annotations survive PDF/A conversion?", "a": "They survive PrivaTools' PDF to PDF/A, which re-saves the file with a PDF/A-2b label and leaves annotations, notes included, in place."},
    ],
    "auto-crop": [
        {"q": "Will this make text run off the page?", "a": "Not text or images: a 20-point margin is kept around them. Vector graphics such as lines, boxes and charts drawn as shapes are not detected, so they can end up outside the new area. A page with no text or images is left as it is."},
        {"q": "What if my PDF has different page sizes after scanning?", "a": "Auto-crop computes the bounding box per-page, so pages are independently cropped to their own content."},
        {"q": "Will this affect printing?", "a": "The pages become smaller than the paper, so choose how your print dialog should place them, for example Fit to page. Do not run Resize afterwards: it removes the crop box and brings the whole page back."},
    ],
    "bates-numbering": [
        {"q": "What's Bates numbering used for?", "a": "Sequential page identification across legal discovery documents. Each page in a production gets a unique identifier so attorneys can reference exact pages."},
        {"q": "Can I start the numbering at a value other than 1?", "a": "Yes — set start_number to any positive integer. This is the standard workflow for continuing a numbering scheme across multiple production batches."},
        {"q": "Does it survive redaction?", "a": "Yes — Bates numbers are stamped directly onto the page content, so they remain after redaction (unless the redaction rectangle covers them)."},
    ],
    "bmp-to-pdf": [
        {"q": "Will the PDF be smaller than the BMPs?", "a": "Usually, because BMP is uncompressed and the PDF stores the pixels with lossless Flate compression. How much depends on the picture: screenshots and flat graphics shrink dramatically, photos much less, and very noisy images may not shrink at all."},
        {"q": "Will quality degrade?", "a": "No. The BMP pixels are stored with lossless compression, so the PDF shows exactly the same image; there is no JPEG step."},
        {"q": "How many BMPs can I convert at once?", "a": "Up to 50 images, with a combined size of up to 200 MB, in one PDF. Uncompressed BMPs are large, so big photos reach the size limit first."},
    ],
    "booklet-pdf": [
        {"q": "Why were blank pages added?", "a": "A folded booklet is made from sheets that each carry four pages, two on each side. When your page count is not a multiple of four, blank pages are added at the end so the imposition works."},
        {"q": "Does it place two pages on each sheet?", "a": "No. It reorders the pages into booklet sequence; the two-per-sheet layout comes from your printer's print dialog. That keeps the file at its original page size and lets you choose the paper at print time."},
        {"q": "My booklet printed out of order.", "a": "Check the double-sided setting. It must flip on the short edge; flipping on the long edge turns every other page upside down relative to its neighbour."},
        {"q": "Is there a limit on the number of pages?", "a": "Not a fixed one, but a single folded booklet becomes hard to fold and staple beyond a few dozen sheets. Split long documents into several booklets first."},
        {"q": "Will the content be shrunk?", "a": "Not by this tool. Fitting two pages onto one sheet is done by your printer's two-per-sheet setting, which scales each page down to half a sheet."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and reordered on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "compare-pdf": [
        {"q": "Does this work on scanned PDFs?", "a": "Visual mode does, because it compares how the pages look, but scanner noise and small shifts between two scans also show up as changes. Text mode needs a text layer, so run OCR PDF on both files first."},
        {"q": "How accurate is the text diff?", "a": "It compares the extracted text line by line, so changing one word marks the whole line as removed and added again. Fonts, colours and other formatting are ignored, and moved text shows up as a deletion plus an addition. Use Visual mode to spot layout changes."},
        {"q": "Can I compare more than two files?", "a": "Run Compare twice (A vs B, then B vs C) to chain a multi-revision comparison."},
    ],
    "crop-pdf": [
        {"q": "Difference between Crop and Auto-Crop?", "a": "Crop uses your manual margins (same on every page). Auto-Crop detects each page's actual content bounding box automatically."},
        {"q": "Will the cropped content be deleted from the file?", "a": "No — only the visible region changes. The full page content is still in the file, so the trimmed parts can be shown again. If what you are trimming is sensitive, remove it with Redact PDF first."},
        {"q": "How do I undo a crop?", "a": "Keep your original: cropping writes a new PDF and leaves your upload unchanged. The Crop tool cannot widen the box again, since negative margins are rejected, but Resize with Custom set to the original page size in points removes the crop box and shows the full page again."},
    ],
    "delete-annotations": [
        {"q": "Will this remove form fields too?", "a": "No. Form fields are technically annotations too, but they are kept, so a fillable form stays fillable."},
        {"q": "Are hyperlinks deleted?", "a": "Yes — hyperlinks are link annotations, so they are removed along with the comments and markup. Form fields remain, so the result is not completely static."},
        {"q": "Does this remove signatures?", "a": "No. Signature fields are form fields and are kept, but the file is rewritten, which breaks any digital signature in it."},
    ],
    "delete-pages": [
        {"q": "Can I undo a deletion?", "a": "The deleted pages are not in the new file, but your original PDF is untouched, so you can always start again from it. Keep the original until you have checked the result."},
        {"q": "How do I delete a range of pages?", "a": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page."},
        {"q": "Is this the same as Extract Pages?", "a": "It is the reverse. Delete Pages removes the pages you list; Extract Pages keeps only the pages you list. Both produce a new PDF and leave the original alone."},
        {"q": "Can I remove blank pages automatically?", "a": "Yes — Remove Blank Pages detects empty and near-empty pages for you, which is quicker than listing them by hand after a scan."},
        {"q": "Will the remaining pages lose quality?", "a": "No. The pages you keep are copied as they are, so text stays selectable and images are not recompressed."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and processed on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "deskew-pdf": [
        {"q": "My scans look fine — should I run deskew?", "a": "Pages whose detected tilt is 0.3° or less keep their original content, but the file is rebuilt, so bookmarks and document metadata are dropped either way. A tilted page is replaced by a rotated image, so any text layer on that page is lost. Use it on scans only: on born-digital pages the detector reported tilts of 0.5° to 1° that were not there."},
        {"q": "Will deskew add white margins?", "a": "Yes — rotated pages need a slightly larger canvas. PrivaTools fills it with white and scales the result to fit the original page size."},
        {"q": "Should I deskew before or after OCR?", "a": "Before. A straightened page is replaced by an image without a text layer, so OCR has to run on the deskewed file anyway."},
    ],
    "esign-pdf": [
        {"q": "Is this a certificate-based digital signature?", "a": "No. It places a visible image of your signature on the page. That suits informal agreements and forms that accept an electronic signature, but it is not the cryptographic, certificate-backed kind some regulated processes require."},
        {"q": "Will a typed signature be accepted?", "a": "That depends on who is receiving the document, not on the tool. Many everyday agreements accept a typed signature as a sign of intent; if in doubt, ask the recipient."},
        {"q": "Does the signed PDF show if it was altered later?", "a": "No. A visible signature does not lock the document or detect changes. Keep a copy of the exact file you signed."},
        {"q": "Can I sign more than one page?", "a": "One signature is placed per run. Sign the output again to add the signature to another page."},
        {"q": "How is this different from Sign PDF?", "a": "Both add a visible signature image. eSign PDF offers typed signatures in several script styles in addition to drawing and uploading."},
        {"q": "What happens to my document after I upload it?", "a": "It is uploaded over HTTPS and signed on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the document and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "excel-to-pdf": [
        {"q": "Will my formulas be visible?", "a": "No. Each formula shows the result saved with the workbook the last time a spreadsheet app calculated it. Files written by tools that do not store those results show formula cells as blank."},
        {"q": "What about charts and images?", "a": "They are left out: only cell values are converted, so charts, pictures, and shapes do not appear. Office to PDF, which uses LibreOffice, includes them."},
        {"q": "How does it handle very wide sheets?", "a": "All columns are squeezed across one landscape A4 page and long values are cut short to fit, so very wide sheets become hard to read. The header row is not repeated on later pages."},
    ],
    "extract-images": [
        {"q": "Will the images be the original resolution?", "a": "Yes. Each image is saved at the pixel size stored in the PDF, without resampling. RGB and greyscale JPEGs are copied byte for byte, CMYK JPEGs are re-saved as high-quality JPEG, and other images are saved without further quality loss, but a separate transparency mask is not applied, so a logo with a transparent background comes out on a solid one."},
        {"q": "What if the same image appears multiple times?", "a": "Each page that uses it gets its own copy in the ZIP, so a logo repeated on every page comes out once per page. Remove the duplicates afterwards if you need to."},
        {"q": "Does it work on scanned PDFs?", "a": "Yes — each page of a scanned PDF is one big image. The tool extracts that page-image directly."},
    ],
    "extract-pages": [
        {"q": "How is this different from Delete Pages?", "a": "They are mirror images. Extract Pages keeps only the pages you list; Delete Pages keeps everything except the pages you list. Pick whichever list is shorter to type."},
        {"q": "Can I get each extracted page as a separate file?", "a": "Not here — the extracted pages come back together in one PDF. Split PDF's Every page mode produces one file per page."},
        {"q": "What range syntax is accepted?", "a": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page. Words such as odd or even are not understood."},
        {"q": "Why was my page list rejected?", "a": "Usually because it refers to a page the document does not have, includes page 0, or has a range written backwards, such as 9-4. The message tells you which part is wrong."},
        {"q": "Does it affect the quality of the pages?", "a": "No. Pages are copied as they are rather than re-rendered, so text stays selectable and images are not recompressed."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and processed on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "fill-form": [
        {"q": "How do I know what the form field names are?", "a": "You do not need to. Detect form fields lists every field with its name, type and current value, ready to fill, without changing anything. Developers can get the same list from the /api/fill-form/fields endpoint."},
        {"q": "Can I flatten the filled form?", "a": "Partly. The Flatten tool marks the filled fields read-only so PDF viewers stop offering to edit them, but the fields stay in the file as form fields and their values are not baked into the page content."},
        {"q": "Does this work on signed forms?", "a": "Filling a signed form invalidates the signature. Sign last, after filling."},
    ],
    "gif-to-pdf": [
        {"q": "Do animated GIFs animate inside the PDF?", "a": "No — PDF doesn't support animation. Only the first frame is used. To convert animation to PDF, use GIF to MP4 and then Video to PDF, which lays out evenly spaced frames, one per page."},
        {"q": "How is transparency handled?", "a": "It is not kept. Transparent pixels show the colour stored in their palette entry, which is often black, and PNG to PDF does not keep transparency either. Flatten the GIF onto a white background first if needed."},
        {"q": "Can the GIF stay as a GIF inside the PDF?", "a": "No. PDF has no GIF image type, so the first frame is decoded and stored with lossless Flate compression; no JPEG step is involved."},
    ],
    "grayscale-pdf": [
        {"q": "Will text still be searchable?", "a": "Only if all the text and drawings were already black or gray: then only the images change and the text layer is kept. If anything is in color, every page becomes an image and the text is no longer searchable; run OCR PDF afterwards to add a text layer back."},
        {"q": "Why convert to grayscale?", "a": "Cheaper printing on black-and-white printers, a predictable look on monochrome devices, and archival storage."},
        {"q": "How does this differ from black-and-white?", "a": "Grayscale preserves shading (256 grey levels). True black-and-white (1-bit) is harsher but smaller — not currently offered as a separate option."},
    ],
    "header-footer": [
        {"q": "Will the header/footer overlap existing content?", "a": "It can. The header sits about 20 points below the top edge and the footer about 20 points above the bottom edge, drawn on top of whatever is already there, and each line starts at the middle of the page and runs to the right. Check pages whose content comes close to the edges, and keep the text short or the font small."},
        {"q": "Can I exclude the cover page?", "a": "Not in one pass: the header and footer go on every page. To leave the cover plain, split it off with Split PDF, add the header and footer to the rest, then join the two files again with Merge PDF."},
        {"q": "Are these editable annotations or baked-in?", "a": "Baked into the page content. They can't be removed without re-editing — use Whiteout to cover them if needed later."},
    ],
    "heic-to-pdf": [
        {"q": "Will the PDF be much larger than the HEIC?", "a": "Often, yes. Each photo is re-encoded as a JPEG at quality 92 inside the PDF, and JPEG generally needs more space than HEIC for the same picture. How much larger depends on the photo."},
        {"q": "Does this preserve image quality?", "a": "Photos keep their full pixel dimensions and are re-encoded once as JPEG at quality 92, a high setting. For a lossless copy, convert the photos to PNG first and use PNG to PDF, which gives much larger files."},
        {"q": "What happens to GPS metadata?", "a": "Stripped during conversion. Use View EXIF first if you want to record GPS coordinates before they're gone."},
    ],
    "invert-colors": [
        {"q": "Why would I invert colors?", "a": "Dark-mode reading on tablets, contrast-flipped scanning of light text on dark backgrounds, or accessibility for users sensitive to bright whites."},
        {"q": "Will the text still be searchable after?", "a": "Inverted pages become images, so the text layer is lost. To preserve searchability, OCR the inverted PDF afterwards."},
        {"q": "Can I invert only certain pages?", "a": "Currently inversion applies to all pages. Run Extract Pages → Invert → Merge to apply selectively."},
    ],
    "jpg-to-pdf": [
        {"q": "Which page size should I choose?", "a": "Auto keeps each page the shape of its image, which is ideal for viewing on screen. Choose A4 or Letter when the PDF will be printed or submitted somewhere that expects standard pages; the images are fitted onto the page."},
        {"q": "Can I combine many images into one PDF?", "a": "Yes. Every image you add becomes a page of the same PDF, in the order shown — the usual way to turn photos of a multi-page document into a single file."},
        {"q": "Will the images lose quality?", "a": "No detail is removed on purpose: each photo is placed in the PDF at its full resolution and scaled on the page to fit. That also means large photos produce a large PDF; run Compress PDF afterwards if you need it smaller."},
        {"q": "What about other image formats?", "a": "This page takes JPG. Image to PDF accepts other common formats, such as PNG and WebP, with the same page-size options."},
        {"q": "Is there a limit on image size?", "a": "Very large images are rejected rather than processed, to protect the server's memory; normal photos and scans are far below that limit. One PDF can take up to 50 images with a combined size of up to 200 MB."},
        {"q": "Can I make the text in my photographed pages searchable?", "a": "Not in this step — a PDF of photos is just pictures. Run OCR PDF on the result to add a searchable text layer."},
        {"q": "What happens to my images after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the images and the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "markdown-to-pdf": [
        {"q": "Are images included?", "a": "Only images embedded in the Markdown as data: URIs. The Markdown file is uploaded on its own, so relative image paths cannot be found, and web addresses are not fetched; each such image appears as an [image] placeholder."},
        {"q": "Can I customize the styling?", "a": "Not at the moment. The PDF uses a fixed, GitHub-inspired style with monospace code blocks, and custom CSS is not supported."},
        {"q": "Does it handle code-block syntax highlighting?", "a": "No. Fenced code blocks are set in a monospace font, but the code is not coloured, whatever language hint you add."},
    ],
    "metadata": [
        {"q": "What metadata does a typical PDF carry?", "a": "Usually: producer (the software that created it) and creation date. Often also: author name, original filename, software version. Scanned PDFs may carry scanner model + driver."},
        {"q": "Why does this matter for privacy?", "a": "Producer + Creator + Author fields can identify the person or machine that created a document — useful in forensics, problematic for whistleblowers."},
        {"q": "Is XMP metadata shown too?", "a": "No. Only the Info dictionary (old format) is shown; the XMP stream (new format) is not read. When you edit, the new values are written to both."},
    ],
    "nup": [
        {"q": "Why is this called 'N-up'?", "a": "Print-industry terminology: '2-up' = 2 pages per sheet, '4-up' = 4 per sheet, etc. Saves paper and ink for review prints."},
        {"q": "Are page numbers preserved?", "a": "Original page numbers (rendered on the page) shrink with the page. Add new page numbers afterwards if you need them readable."},
        {"q": "What aspect ratio works best?", "a": "Sheets are always A4 landscape. Portrait pages fill 2-up side-by-side with no wasted space, while landscape pages fill 4-up, 9-up and 16-up. Mismatches add whitespace around each sub-page."},
    ],
    "odt-to-pdf": [
        {"q": "What about ODT-specific features (math equations, drawings)?", "a": "OpenDocument math (Formula) and drawings render correctly as the LibreOffice converter handles them natively."},
        {"q": "Will fonts that aren't on the server cause problems?", "a": "Missing fonts get substituted. Embedded fonts in the ODT are honored."},
        {"q": "Does it handle macros?", "a": "Macros are not executed — only the static document content is converted."},
    ],
    "organize-pages": [
        {"q": "What can I change with this tool?", "a": "The order of the pages, and which pages are included. It does not rotate, edit or add pages; use Rotate PDF, Edit PDF or Merge PDF for those."},
        {"q": "Can I move a page from one PDF into another?", "a": "Merge the two files first with Merge PDF, then open the merged document here and drag the page to where it belongs."},
        {"q": "Is there a quicker way to reverse every page?", "a": "Yes. Reverse PDF flips the whole document in one step, which is handy when a scanner fed the pages last page first."},
        {"q": "Will the pages lose quality?", "a": "No. Pages are reordered, not re-rendered, so text stays selectable and images are not recompressed."},
        {"q": "Do the thumbnails mean my PDF is uploaded twice?", "a": "The PDF is sent to the server to render the thumbnails and again to build the reordered file. Both requests use the same temporary per-request handling."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and reorganised on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "overlay": [
        {"q": "What's the difference between overlay and merge?", "a": "Merge concatenates files page-by-page. Overlay composites pages on top of each other — useful for adding letterheads, watermarks-from-PDF, or repeating templates."},
        {"q": "Can I overlay only some pages?", "a": "No. Every base page gets an overlay page: overlay page 1 goes on base page 1, page 2 on page 2, and so on, and once the overlay runs out its first page is reused for the remaining base pages. A one-page overlay, such as a letterhead, therefore lands on every page."},
        {"q": "Does transparency work?", "a": "Yes — PDF supports transparency and the overlay's alpha is honored. White rectangles still cover what's beneath; transparent regions show base content through."},
    ],
    "page-numbers": [
        {"q": "Can I use Roman numerals or letters?", "a": "No. Page numbers are Arabic digits only; Roman numerals and letters are not supported."},
        {"q": "How is this different from Bates numbering?", "a": "Page numbers are simple sequential digits. Bates numbers have a prefix, configurable padding, and are used in legal contexts."},
        {"q": "Can I start from a specific page?", "a": "Not directly: every page gets a number, and the first page gets the starting number you set. To leave a cover or contents pages unnumbered, split them off, number the rest from the right starting value, then merge the files back together."},
    ],
    "pdf-to-bmp": [
        {"q": "Why are BMPs so much larger than PNG?", "a": "BMP stores every pixel uncompressed. PNG compresses the same pixels losslessly, which for a page of text usually means a small fraction of the BMP size. Use BMP only when you specifically need uncompressed pixel data."},
        {"q": "What's BMP good for?", "a": "Legacy Windows software that doesn't support modern formats; embedded systems; precise pixel manipulation."},
        {"q": "Can I get just one page as BMP?", "a": "Extract that page first with Extract Pages, then convert."},
    ],
    "pdf-to-epub": [
        {"q": "How accurate is the EPUB compared to the PDF?", "a": "The text comes across line by line, in the order it is stored in the PDF, with its font sizes, bold, italics and colors. Headings, lists and chapters are not detected, and multi-column layouts, footnotes, and figure captions may need cleanup in an e-book editor such as calibre."},
        {"q": "Does it preserve images?", "a": "Yes — images are embedded inside the page as inline data, at the resolution stored in the PDF, rather than as separate image files in the EPUB."},
        {"q": "Will the table of contents work?", "a": "No table of contents is created, even when the PDF has bookmarks: the whole document is a single section of the book."},
    ],
    "pdf-to-gif": [
        {"q": "Will the GIFs look good?", "a": "GIF's 256-color palette quantizes the page. Text remains readable but gradients and photos show banding. Use PNG for higher quality."},
        {"q": "Does this make an animated GIF?", "a": "No — each page is one static GIF, and the tool does not combine pages into an animation."},
        {"q": "How big are the output files?", "a": "It depends on how much is on the page. At the 150 DPI this tool uses, a page with a few lines of text can be under 20 KB, while a page packed with small text can approach 400 KB."},
    ],
    "pdf-to-jpg": [
        {"q": "Why JPG instead of PNG?", "a": "JPG is much smaller for photos and photographic scans. Use PDF-to-PNG if your PDF has crisp text or graphics where JPEG compression artifacts would show as ringing around letter edges."},
        {"q": "What about transparency?", "a": "JPG doesn't support transparency. Pages are rendered onto a white background, so transparent regions come out white. PDF-to-PNG renders onto white as well, so neither gives a transparent image."},
        {"q": "How long does it take?", "a": "Roughly 50-100 ms per page at 150 DPI on the server. A 100-page PDF takes ~10 seconds end-to-end, depending on how complex the pages are."},
        {"q": "What happens to a confidential PDF after I upload it?", "a": "The PDF is uploaded over HTTPS and rendered in isolated temporary per-request storage on the PrivaTools server, using local libraries rather than a third-party API. Response cleanup removes the PDF and the generated JPGs after the result is sent, and a background sweep clears anything left behind by an interrupted request."},
        {"q": "What resolution are the JPGs?", "a": "150 DPI, which makes an A4 page about 1240 x 1755 pixels, plenty for on-screen viewing and social-media sharing. For 72 DPI thumbnails or 300 DPI print copies, use PDF to Image, which lets you choose."},
        {"q": "Can I convert just specific pages?", "a": "Not on this page; every page is converted. Pull the pages you need into a smaller PDF with Extract Pages first, then convert it. Longer PDFs come as a ZIP. A one-page PDF returns a single JPG, which currently downloads with a .zip name, so rename it to .jpg."},
        {"q": "What's the file size limit?", "a": "Up to 500 MB per file on the hosted site. Each page becomes its own JPG, so a very long document produces a large ZIP and can hit the request timeout; split the PDF first if that happens. Fair-use rate limits apply."},
        {"q": "Do the JPGs carry a watermark or need an account?", "a": "No. The images carry no watermark and the tool works without an account. Fair-use rate limits apply to conversions."},
    ],
    "pdf-to-markdown": [
        {"q": "How accurate is the structural detection?", "a": "Headings work well when source fonts are larger: text of 20 pt or more becomes a level-1 heading, 16 pt a level-2 heading, and bold text of 13 pt or more a level-3 heading. Tables, lists and code blocks are not detected, and table cells come out as separate lines, so review the result."},
        {"q": "What about images?", "a": "Images are skipped, so the Markdown file holds text only. Use Extract Images to save the pictures from the PDF separately."},
        {"q": "Will hyperlinks be preserved?", "a": "No. Only the visible text is kept: a web address printed on the page stays as plain text, but the target of a clickable link is dropped."},
    ],
    "pdf-to-png": [
        {"q": "Why PNG instead of JPG?", "a": "PNG is lossless — text and graphics stay crisp. JPG compresses better for photos but introduces compression artifacts on text."},
        {"q": "How big are the PNGs?", "a": "It depends on the page. At the 150 DPI this tool uses, a page with a few lines of text can be under 30 KB, a page packed with small text is about 500 KB, and a full-page photo can run to several megabytes."},
        {"q": "Does this preserve PDF transparency?", "a": "No. Pages are rendered onto a white background and saved without an alpha channel, so transparent areas come out white."},
    ],
    "pdf-to-pptx": [
        {"q": "Will the text be editable in PowerPoint?", "a": "No. Each slide holds a single picture of the page and no text boxes, so the text cannot be edited. Use PDF to Word for editable text, or copy it out with PDF to Text."},
        {"q": "What about embedded charts and graphics?", "a": "They appear as part of the page image. Re-creating editable charts requires manual recreation in PowerPoint."},
        {"q": "Can I get one slide per section instead of per page?", "a": "No, it is always one slide per page. To make a deck from a single section, pull those pages into a smaller PDF with Extract Pages first, then convert that."},
    ],
    "pdf-to-tiff": [
        {"q": "Why TIFF for archival?", "a": "TIFF supports lossless compression (LZW, Deflate) and is the format of choice for long-term preservation in libraries and government archives."},
        {"q": "Single multi-page TIFF or one per page?", "a": "Always one multi-page TIFF; there is no per-page option. If your software only reads single-page TIFFs, split the PDF into one file per page with Split PDF and convert those files together: each gives a single-page TIFF."},
        {"q": "Does it preserve text searchability?", "a": "TIFF is raster only — the text layer is lost, so the pages cannot be searched. Keep the original PDF alongside the TIFF if you need searchable text."},
    ],
    "pdfa-validator": [
        {"q": "What is PDF/A and why does it matter?", "a": "PDF/A is an ISO standard for long-term archival. It requires self-contained PDFs (all fonts embedded, no external scripts, no encryption) so the document will render identically in 50 years."},
        {"q": "What's the difference between PDF/A-1, A-2, A-3?", "a": "A-1 is the strictest (no transparency, no XFA forms). A-2 adds transparency, JPEG 2000, and PDF attachments. A-3 allows arbitrary file attachments — useful for invoice + machine-readable data bundles."},
        {"q": "If it's not PDF/A, can I convert it?", "a": "The PDF to PDF/A tool re-saves the file and adds a PDF/A-2b label, which this check then detects. It does not embed fonts or add a colour profile, so the result is not guaranteed to conform."},
    ],
    "png-to-pdf": [
        {"q": "Will the PDF be larger than the PNGs?", "a": "It depends on the image. Screenshots and flat graphics come out about the same size, but photographic PNGs can come out noticeably larger, because the pixels are recompressed losslessly without the filters PNG uses."},
        {"q": "How is transparency handled?", "a": "It is not kept. The PDF stores only the colour of each pixel, so fully transparent areas show whatever colour is stored beneath them, often black rather than white. Flatten the image onto a white background before converting if that matters; Image to PDF behaves the same way."},
        {"q": "Is there a max number of images?", "a": "Yes. One conversion takes up to 50 images with a combined size of up to 200 MB. For more, convert them in batches and join the PDFs with Merge PDF."},
    ],
    "pptx-to-pdf-convert": [
        {"q": "Will animations be preserved?", "a": "No. Animations are ignored and every text box on a slide is drawn, including text that would only appear later in the animation."},
        {"q": "How are speaker notes handled?", "a": "Speaker notes are not included in the PDF, and there is no option to add them. Export the notes from your presentation software if you need them."},
        {"q": "What about embedded videos?", "a": "They are left out, poster frame included, because only text is converted. If you have the video file itself, Video to PDF can lay out evenly spaced frames from it."},
    ],
    "qr-code": [
        {"q": "Can I customize colors?", "a": "Yes. Pick any colour for the code and the background, and optionally add a small centre logo as a PNG, JPG or WebP image. Keep a dark code on a light background with strong contrast, and scan the finished code before sharing it."},
        {"q": "How do I encode a URL with parameters?", "a": "Just paste the full URL. Special characters are encoded automatically inside the QR."},
        {"q": "What's the maximum data I can encode?", "a": "About 2,200 characters of ordinary text, such as a long URL, or about 5,300 digits, at the error correction level M the tool uses. Adding a centre logo switches to level H and roughly halves that. Longer input cannot be encoded."},
    ],
    "remove-blank-pages": [
        {"q": "How does it decide a page is blank?", "a": "Each page is rendered at a low resolution and the proportion of near-white pixels is measured. A page that is white enough for the sensitivity you chose is treated as blank. Pages carrying text are normally kept."},
        {"q": "My scanned blank pages were not removed.", "a": "Scanners rarely produce pure white: dust, texture and faint show-through from the other side all count as content. Lower the sensitivity a step or two and run it again until the empty sides disappear."},
        {"q": "Could it remove a page I want to keep?", "a": "At low settings, a page with only a few faint marks can be judged blank. Check the result before discarding the original, and raise the sensitivity if anything important went missing."},
        {"q": "Why does a higher number remove fewer pages?", "a": "Because the number is how strict the tool is about whiteness: at 100 a page has to be essentially pure white to count as blank. Lowering it lets more imperfect pages qualify."},
        {"q": "Can I choose which blank pages to keep?", "a": "Not in this tool — it removes every page it judges blank. To keep a deliberate blank page, remove the others here and put it back with Merge PDF, or delete pages by number with Delete Pages instead."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and checked on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "repair-pdf": [
        {"q": "What kinds of damage can it fix?", "a": "Missing or corrupt cross-reference tables, broken trailers, dangling object references, slightly-truncated streams. Cannot recover from missing object data."},
        {"q": "Will the repaired PDF look identical?", "a": "Yes if the damage was in metadata/structure. Visible content damage (cropped images, missing fonts) requires the original to fix."},
        {"q": "Can it merge two damaged PDFs?", "a": "Repair each separately first, then use Merge."},
    ],
    "resize-pdf": [
        {"q": "Will my content be cropped if I resize to a smaller page?", "a": "Yes. The content is not scaled, so anything beyond the new width or height, measured from the bottom-left corner, is cut off: resizing an A4 page to Letter loses about the top 50 points. If you want to choose what to trim, use the Crop tool."},
        {"q": "Difference between Resize and Crop?", "a": "Resize changes the page dimensions without scaling the content. Crop keeps the page and hides its margins by setting a smaller visible area; the hidden parts stay in the file."},
        {"q": "Does this affect text quality?", "a": "No. Nothing is scaled or re-rendered; only the page size changes, so text and images stay exactly as they were."},
    ],
    "reverse-pdf": [
        {"q": "Why would I reverse a PDF?", "a": "Most often because a scanner or printer produced the pages last-to-first. Reversing fixes the whole document in one step rather than dragging every page into place."},
        {"q": "Can I reverse only part of a document?", "a": "No, the whole file is reversed. For a partial change, use Organize Pages, or split the section out, reverse it and merge it back."},
        {"q": "Does it change the pages themselves?", "a": "No. Only the order changes; text, images and page sizes are copied as they are."},
        {"q": "I scanned odd and even pages separately. Will this help?", "a": "Partly. Reverse the stack that came out backwards, then interleave the two files with Alternate Mix, which is built for exactly that single-sided-scanner workflow."},
        {"q": "Can I reverse several PDFs at once?", "a": "One file at a time. Run it again for each document."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and reordered on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "rtf-to-pdf": [
        {"q": "What about RTF features like fields?", "a": "Fields are not recalculated. The converter only strips RTF codes, so a field shows its last saved result, and parts of the field code can appear as stray text. Form fields are not converted to PDF form fields; use Form Creator to add fillable fields."},
        {"q": "Does it preserve fonts?", "a": "No. All text is set in 11 pt Helvetica, whatever fonts the RTF names. Accented letters stored as RTF escape codes, which is how Word and WordPad usually save them, are dropped, and characters from other scripts come out as question marks."},
        {"q": "How does this differ from DOCX-to-PDF?", "a": "RTF is an older Microsoft format and DOCX a newer ZIP-based one. The tools differ too: Word to PDF keeps headings and some bold and italic styling from a DOCX, while this tool keeps only plain text. For a conversion that keeps the formatting, use Office to PDF, which lays the file out with LibreOffice."},
    ],
    "sanitize-pdf": [
        {"q": "What is sanitization protecting against?", "a": "In general, malicious PDFs that abuse embedded scripts or attachments. This tool does not remove those: in a test, a document-level JavaScript action, a link that launches a program and an embedded file all survived. Use it to clear identifying document info, not to neutralise a suspicious file."},
        {"q": "Does this remove form fields?", "a": "No — form fields are kept, along with any actions attached to them."},
        {"q": "Are hyperlinks removed?", "a": "No. All links are kept, including links that launch another program or use a javascript: address."},
    ],
    "set-permissions": [
        {"q": "What's the difference between owner password and user password?", "a": "User password = required to OPEN. Owner password = required to override permissions (print, edit). This tool sets only the owner password + permission flags, so the file still opens without a password. Protect PDF adds an open password, but its owner password is generated at random and never shown."},
        {"q": "How strong is the protection?", "a": "It's enforced by readers as a courtesy — Adobe Acrobat respects it strictly, some open-source readers ignore it. For real security, encrypt with a user password."},
        {"q": "Can users still copy text?", "a": "Only if allow_copy is true. If false, the reader disables text selection. Note: screenshots still work (no PDF protection can prevent that)."},
    ],
    "split-by-bookmarks": [
        {"q": "Which bookmarks does it split on?", "a": "The top-level ones. Nested sub-bookmarks stay inside their parent's part rather than producing a file of their own, which keeps a chapter together with its sections."},
        {"q": "What if my PDF has no bookmarks?", "a": "The tool stops with a message saying there are no bookmarks to split on. Use Split PDF to split by page numbers instead, or Split by Text if each section starts with a recognisable heading."},
        {"q": "How can I tell whether my PDF has bookmarks?", "a": "Open the bookmarks or outline panel in your PDF reader. If it is empty, or lists only the document title, there is nothing for this tool to use."},
        {"q": "Does it change the pages?", "a": "No. Pages are copied into the new files as they are; only the division into files is new."},
        {"q": "Can I choose which chapters to export?", "a": "The tool produces every part. Keep the ones you need from the ZIP, or use Extract Pages when you only want a single chapter's page range."},
        {"q": "What happens to my PDF after I upload it?", "a": "It is uploaded over HTTPS and split on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "stamp-pdf": [
        {"q": "Are stamps editable annotations or baked-in?", "a": "Baked into the page content. They survive copying, printing, and PDF/A conversion. To remove, use Whiteout to cover them."},
        {"q": "Can I apply a stamp to only specific pages?", "a": "Yes. Enter the page numbers separated by commas, such as 1,3,5, or leave it as all. Ranges such as 1-3 are rejected, so list each page."},
        {"q": "How big is the stamp?", "a": "It is sized automatically from the page width and the length of the text, up to 72 pt: on an A4 page CONFIDENTIAL spans most of the width and VOID about a third of it. The size cannot be set by hand."},
    ],
    "strip-metadata": [
        {"q": "Why strip metadata?", "a": "Author / producer / original-filename fields can identify who created or owns a document — a privacy concern for whistleblowers, journalists, or before public release."},
        {"q": "What about embedded images' EXIF?", "a": "It is not removed. EXIF inside images embedded in the PDF is left as it is: in a test, the camera make stored in an embedded JPEG was still in the output. Only the document's own Info and XMP metadata is cleared."},
        {"q": "Is this the same as Sanitize?", "a": "No — Strip Metadata removes informational fields, including XMP. Sanitize clears only the document Info fields and Movie and RichMedia (Flash) annotations; it leaves JavaScript, embedded files and XMP in place."},
    ],
    "svg-to-pdf": [
        {"q": "Will my SVG stay as vector inside the PDF?", "a": "No. Each SVG is rendered with CairoSVG to a PNG image 2400 pixels wide, and that image is placed on the page. It looks sharp at normal sizes, but edges soften when you zoom in far, and text cannot be selected or searched."},
        {"q": "What about embedded raster images inside SVG?", "a": "Images embedded in the SVG as data: URIs are drawn. References to images in other files or at web addresses are blocked for security, and an SVG that contains one is rejected with an error."},
        {"q": "Does it handle CSS styles inside SVG?", "a": "Styles written inside the SVG, in a style element or style attributes, are applied, but external stylesheets are not loaded. Note that transparency is not kept: areas with no background come out black, so add a white background rectangle to drawings that need one."},
    ],
    "tiff-to-pdf": [
        {"q": "Will quality be preserved?", "a": "For standard 8-bit TIFFs, yes: the decoded pixels are stored with lossless Flate compression and no JPEG step is added. The trade-off is file size, since nothing is recompressed to save space."},
        {"q": "What about CMYK TIFFs (for print)?", "a": "CMYK TIFFs stay CMYK: the pixels are embedded as DeviceCMYK image data. An embedded ICC colour profile is not carried over, so check colour-critical print jobs with your printer."},
        {"q": "How are multi-page TIFFs handled?", "a": "Only the first page of each TIFF is converted; the other pages are ignored. Every TIFF file you add becomes one PDF page, in the order shown, so save each page as a separate TIFF first if you need them all."},
    ],
    "transparent-background": [
        {"q": "Will text be affected?", "a": "Dark text is kept fully opaque. Each pixel is either kept or made fully transparent, with nothing in between, so light grey text at or above the threshold disappears. Raise the threshold toward 255 to remove only the purest white, or lower it to clear off-white backgrounds as well. The text also stops being selectable, because each page becomes an image."},
        {"q": "What's the output format?", "a": "A PDF with transparent regions where the background was: each page holds one PNG image with transparency, on a page of the original size. Open it in a reader to see the underlying canvas show through."},
        {"q": "Can I use this on photos?", "a": "It works best on text/diagram documents with clean backgrounds. Photos with light skies become weirdly transparent — use Remove Background (rembg) for photos."},
    ],
    "verify-signature": [
        {"q": "Does this require uploading my certificates?", "a": "No. No certificates are read or checked at all, neither yours nor the ones embedded in the PDF."},
        {"q": "What if a signature is invalid?", "a": "This tool cannot tell you: it does not validate signatures. Use a PDF reader that validates signatures to see why one fails."},
        {"q": "Can I verify multiple signatures?", "a": "PDFs can have multiple signatures (e.g. one per signing party), but this tool verifies none of them, and at present it does not recognise signature fields, so the list comes back empty."},
    ],
    "webp-to-pdf": [
        {"q": "Will the PDF be much smaller than from JPG?", "a": "No, usually larger. WebP pixels are decoded and stored with lossless compression, so a lossy WebP photo can grow many times over, while a JPG is placed in the PDF without re-encoding."},
        {"q": "What about animated WebP?", "a": "Only the first frame is used. PDF doesn't support animation."},
        {"q": "Does this preserve transparency?", "a": "No. Only the colour of each pixel is stored, so transparent areas show whatever colour is stored beneath them, which is often black. Flatten the image onto a white background first if you need a white page."},
    ],
    "whiteout-pdf": [
        {"q": "Is whiteout the same as redaction?", "a": "No — whiteout covers content visually but the underlying text remains in the file. For permanent redaction (text removed), use Redact PDF or Smart Redact."},
        {"q": "Can I use any color, not just white?", "a": "No. The boxes are always white. To take text out of the file rather than just cover it, use Redact PDF."},
        {"q": "Does it work on scanned PDFs?", "a": "Yes — the cover rectangle is added on top of the rendered page. Behind, the original pixels are still in the file."},
    ],
    "add-subtitles": [
        {"q": "Why burn subtitles in instead of using a soft track?", "a": "Burned-in captions show on platforms and players that ignore separate subtitle tracks. The trade-off is that viewers cannot turn them off, and this tool does not create a soft, switchable track."},
        {"q": "What subtitle formats are supported?", "a": "SRT files. The captions are rendered into the picture, so the MP4 shows them in any player; no separate subtitle track is produced."},
        {"q": "Can I customize the font / size / color?", "a": "Not at the moment. Burned-in subtitles use fixed defaults — white text with a black outline in a sans-serif font — and custom styling is not supported."},
    ],
    "audio-merge": [
        {"q": "What if my files have different sample rates?", "a": "FFmpeg resamples them to a common rate automatically; a 44.1 kHz MP3 joined to a 48 kHz WAV came out at 44.1 kHz. The result is always an MP3, so the merge is never lossless, even from FLAC or WAV inputs."},
        {"q": "Are gaps between tracks added?", "a": "No — files are concatenated seamlessly. To add silence, prepare it as a separate file with the same format and insert it in the order."},
        {"q": "Maximum total length?", "a": "The limits apply to what you upload: up to 50 files, and the whole upload has to fit within the 500 MB request limit. A merge that takes longer than three minutes to encode is stopped."},
    ],
    "color-converter": [
        {"q": "Does it work with alpha (transparency)?", "a": "No. Input is a 3- or 6-digit HEX code without alpha, and the RGBA row always shows an alpha of 1."},
        {"q": "What does the contrast badge mean?", "a": "It rates the color against white or black text, whichever contrasts more, with the WCAG formula: AAA at 7:1 or more, AA at 4.5:1, AA Large at 3:1, and Fail below that."},
        {"q": "Is the calculation done locally?", "a": "Yes — pure browser JavaScript. No network requests."},
    ],
    "create-zip": [
        {"q": "Can I password-protect the ZIP?", "a": "Not yet. Create ZIP produces standard, unencrypted ZIP archives; password-protected archives are not supported."},
        {"q": "Will it preserve folder structure?", "a": "No. Every file is placed at the root of the archive, and a file whose name is already taken gets a numbered suffix. There is no folder option; to keep a folder structure, zip the folder on your own device."},
        {"q": "What compression level should I choose?", "a": "Balanced is best for most files. Store is fastest for already-compressed files like JPG, MP4, and PDF. Smallest size can shrink text-heavy files more but takes longer."},
    ],
    "csv-json": [
        {"q": "How does CSV escaping work?", "a": "Standard RFC 4180: commas in values must be quoted; quotes inside values are doubled (\"\"). PrivaTools handles both."},
        {"q": "What about nested JSON?", "a": "Nested objects and arrays go into a single cell as JSON text; they are not split into dot-notation columns (JSON to CSV Schema does that). CSV to JSON keeps every value as a string and does not rebuild nesting."},
        {"q": "Will my data be uploaded?", "a": "No — pure-browser conversion. No data leaves your machine."},
    ],
    "extract-archive": [
        {"q": "What about password-protected archives?", "a": "Password-protected archives are not supported yet. Extract Archive handles unencrypted ZIP and TAR-family archives."},
        {"q": "Does it support RAR / 7z?", "a": "No. Extract Archive supports ZIP and TAR-family archives (.tar, .tar.gz, .tar.bz2, .tar.xz). RAR and 7z are not supported."},
        {"q": "What if the archive contains many small files?", "a": "Up to 5,000 files and 2 GB of extracted data per archive. The page lists the first 1,000 entries, but the download contains everything."},
    ],
    "extract-audio": [
        {"q": "Will quality be preserved?", "a": "WAV and FLAC store the decoded audio without further loss. MP3, AAC and OGG are re-encoded at the encoders' default settings, about 128 kbps for stereo MP3 and AAC, and there is no bitrate setting here."},
        {"q": "What if the video has multiple audio tracks?", "a": "The first (default) audio track is extracted. Choosing another track, or extracting several at once, is not supported."},
        {"q": "Can I extract just a section of the audio?", "a": "Use Trim Media first to isolate the section, then extract audio from the trimmed video."},
    ],
    "generate-barcode": [
        {"q": "What barcode type for a URL?", "a": "Use QR code — barcodes like Code 128 work for text but are much wider for the same content."},
        {"q": "Will it scan reliably?", "a": "Usually. Linear barcodes are drawn at the python-barcode library's default size, and QR codes use 10-pixel modules with a four-module quiet zone. Test a printout with the scanner you will use, especially if you shrink it."},
        {"q": "Can I include a check digit?", "a": "EAN-13, EAN-8, UPC-A and ISBN-13 auto-calculate the check digit. Code 128 has a built-in checksum. Code 39 always gets a mod-43 check character added."},
    ],
    "generate-favicon": [
        {"q": "Which sizes are in the icon?", "a": "16×16, 32×32 and 48×48, packed into one .ico file so the browser can pick the size it needs, such as 16×16 for a tab. Larger icons for phone home screens or installed web apps, such as 192×192 or 512×512, are not included; make those as separate PNG files."},
        {"q": "Which source image works best?", "a": "A square PNG with a transparent background. SVG files are not accepted, so convert a vector logo with SVG to PNG first. JPG works too, but it has no transparency and loses some sharpness from compression."},
        {"q": "Will my logo become circular?", "a": "No — favicons render exactly as uploaded. To get a circular look, upload a circular PNG with transparency."},
    ],
    "gif-to-mp4": [
        {"q": "Why convert GIF to MP4?", "a": "MP4 is dramatically smaller (better compression), supports audio, and plays smoother. Most social platforms now auto-convert uploaded GIFs to MP4 anyway."},
        {"q": "Will the loop work in MP4?", "a": "MP4 doesn't have built-in loop info — players decide. Embed with <video loop autoplay muted> to mimic GIF behavior on the web."},
        {"q": "Does it preserve transparency?", "a": "MP4 doesn't support transparency. Transparent areas come out white, because the GIF is decoded onto white before encoding. Use WebM with VP9 if you need alpha."},
    ],
    "hash-generator": [
        {"q": "Can it make MD5 hashes?", "a": "No. The browser's Web Crypto API has no MD5, so this tool calculates SHA-1, SHA-256 and SHA-512. MD5 and SHA-1 are both broken for security uses such as signatures; use SHA-256 or SHA-512."},
        {"q": "Why are file hashes useful?", "a": "Verifying file integrity after download, deduplication, change detection, content-addressed storage."},
        {"q": "Is the hash calculation done in the browser?", "a": "Yes — Web Crypto API runs the hash in your browser. Files are not uploaded."},
    ],
    "image-converter": [
        {"q": "Which formats can I convert between?", "a": "JPG, PNG, WebP, BMP and TIFF, in any direction between them. Other formats are not accepted here: iPhone HEIC photos go through HEIC to JPG or HEIC to PNG, and GIFs through GIF to JPG or GIF to PNG."},
        {"q": "Which format should I choose?", "a": "JPG for photographs you need to be small and universally accepted. PNG for screenshots, logos and anything needing transparency or perfect edges. WebP for images going onto a web page. TIFF and BMP mainly when a print, scanning or legacy system demands them."},
        {"q": "Can I set the quality?", "a": "Not here. The output uses default encoder settings, which means JPEG is written at quality 75. If you want to control the size-versus-quality trade-off, Image Compressor exposes a quality setting; to change pixel dimensions, use Resize and Crop Image."},
        {"q": "What happens to transparency?", "a": "PNG, WebP and TIFF keep an alpha channel. Converting to JPG or BMP discards it, and because the alpha is dropped rather than composited onto white, previously transparent areas take whatever colour sat beneath them — commonly black."},
        {"q": "Are animations and multi-page files handled?", "a": "No. Only the first frame of an animated WebP, and only the first page of a multi-page TIFF, is converted. The remaining frames and pages are not included in the output."},
        {"q": "Is EXIF metadata preserved?", "a": "No. A fresh image is written without copying EXIF, so camera, timestamp and GPS details are dropped. That makes the converter a reasonable way to strip metadata in passing, though Remove EXIF is the tool that does it deliberately and keeps the original format."},
        {"q": "Why is my TIFF output so large?", "a": "TIFF is written uncompressed here, so it stores every pixel in full. That is exactly what archival and print workflows ask for, but expect a file many times the size of the source."},
        {"q": "What happens to my images after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "image-ocr": [
        {"q": "How accurate is the OCR?", "a": "Tesseract handles clean printed text well. Handwriting, low-resolution, or low-contrast images are harder."},
        {"q": "Should I preprocess the image first?", "a": "Deskew helps a lot for tilted scans. Convert to grayscale doesn't help (Tesseract converts internally)."},
        {"q": "What about handwriting?", "a": "Tesseract is trained on print. Use a specialized handwriting OCR for cursive."},
    ],
    "image-watermark": [
        {"q": "Can the watermark be removed?", "a": "Not by toggling anything: the text is drawn into the pixels. That said, a determined person with an editor can crop it out or paint over it, particularly a small mark in a corner. Treat a watermark as a clear statement of ownership, not as a technical lock."},
        {"q": "Where should I put it?", "a": "A corner is tidy and suits a signature or a site name, but it is the easiest to crop off. The centre sits over your subject. Tile repeats the text across the whole image, which is the usual choice for proofs you do not want reused. Pick according to whether you are signing your work or deterring reuse."},
        {"q": "What opacity works best?", "a": "Low enough that the picture stays readable, high enough to survive resizing and re-sharing. The starting point of a little over half is a reasonable compromise; raise it for proofs and lower it when the image matters more than the mark."},
        {"q": "Can I use my logo instead of text?", "a": "This tool stamps text. For a PDF, Watermark PDF accepts an image such as a logo and offers more placement control."},
        {"q": "Can I watermark a batch with the same text?", "a": "Yes. Add the images together and each is stamped with the same settings; the batch comes back as a single ZIP, which is the usual way to prepare a set of proofs or product photos."},
        {"q": "Does it change the original file?", "a": "No. You download a new, marked copy and the file on your device is untouched."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "json-xml-formatter": [
        {"q": "Will it validate the input?", "a": "Yes — invalid JSON / XML shows an error with the line and column. Common errors (trailing commas, unclosed strings, mismatched tags) are highlighted."},
        {"q": "Can it convert JSON ↔ XML?", "a": "No. This tool formats, minifies and validates; it does not convert between JSON and XML."},
        {"q": "Is the indent customizable?", "a": "Yes — 2 spaces, 4 spaces, or tabs."},
    ],
    "lorem-ipsum": [
        {"q": "Why use Lorem Ipsum and not English?", "a": "It has roughly Latin letter frequencies so designs feel real, without distracting reviewers with the actual content. English placeholder text always gets read instead of looked at."},
        {"q": "Can I get other languages?", "a": "Not other languages or scripts. Besides classic Latin, it offers three themed word lists in English: Cyberpunk, Pirate and Hacker."},
        {"q": "Is it copyrighted?", "a": "Cicero died in 43 BC. Public domain."},
    ],
    "make-collage": [
        {"q": "How are the images arranged?", "a": "In a grid, filled left to right and top to bottom. The automatic setting picks a near-square layout; set the columns yourself for a different shape — one column for a vertical strip, or a high number for a wide banner."},
        {"q": "Do the pictures need to be the same size?", "a": "No, but a set of similar shapes produces a tidier grid. Mixing portrait and landscape shots leaves uneven tiles, so resizing them to a common size first with Resize and Crop Image gives a cleaner result."},
        {"q": "What does the spacing setting do?", "a": "It sets the gap between tiles in pixels, from none at all up to 100. Zero produces a seamless block; a wider gap with a contrasting background colour gives the framed, scrapbook look."},
        {"q": "Can I change the background colour?", "a": "Yes. It defaults to white and shows in the gaps and borders. Black or a brand colour makes a set of photographs look deliberate rather than accidental."},
        {"q": "Can I rearrange the tiles?", "a": "Yes. Drag the thumbnails in the preview to reorder them before you build the collage; the finished image follows that order."},
        {"q": "What do I get back?", "a": "A single image containing the whole grid, which you can then treat like any other picture — compress it, resize it, or add a watermark."},
        {"q": "What happens to my images after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "markdown-html": [
        {"q": "What about extensions like tables and code blocks?", "a": "Fenced code blocks work. Tables, strikethrough and task lists are not converted and stay as plain text, nested lists are flattened, and images appear as links."},
        {"q": "Will inline CSS be preserved?", "a": "No. Raw HTML in the Markdown, inline styles included, is escaped and shown as text rather than rendered."},
        {"q": "Is the conversion lossless?", "a": "Not for every document: the converter handles the core Markdown subset listed above, so the extensions it skips come through as plain text. There is no HTML-to-Markdown direction."},
    ],
    "merge-images": [
        {"q": "Will images be cropped?", "a": "No — they're scaled to a common dimension (width for vertical, height for horizontal). Every image is brought up to the height of the tallest (side by side) or the width of the widest (top to bottom), so smaller images are enlarged and none are shrunk."},
        {"q": "What if my images have different aspect ratios?", "a": "Each image keeps its own shape and nothing is padded: side by side, a wider image simply takes more of the row; top to bottom, a taller one takes more of the column. The grid option instead fits each image inside an equal cell on a white background. Use Resize Crop Image first to force a common aspect ratio."},
        {"q": "Difference from Make Collage?", "a": "Merge joins images in a single row or column, or in a grid whose columns are chosen for you. Make Collage lets you set the number of columns, the spacing and the background colour yourself."},
    ],
    "password-generator": [
        {"q": "How strong is the password?", "a": "Length 20 with mixed classes ≈ 130 bits of entropy — uncrackable by brute force. Length 12 ≈ 78 bits — still very strong."},
        {"q": "Why exclude ambiguous characters?", "a": "Visual confusion: l vs 1 vs I, 0 vs O. Excluding them makes the password easier to type / read aloud at the cost of slightly less entropy."},
        {"q": "Is it really random?", "a": "Yes — Web Crypto's getRandomValues uses the OS's cryptographically secure RNG (e.g. /dev/urandom on Linux, BCryptGenRandom on Windows)."},
    ],
    "qr-reader": [
        {"q": "Can it read damaged QR codes?", "a": "QR codes have built-in error correction (up to 30%). Slightly damaged codes still read; heavily damaged ones fail."},
        {"q": "Multiple QR codes in one image?", "a": "All detected QR codes are returned with their position. Useful for batch scanning of labels."},
        {"q": "What about other barcode types?", "a": "pyzbar also reads Code 128, Code 39, EAN-13, UPC-A, etc. The decoder identifies the type automatically."},
    ],
    "resize-crop-image": [
        {"q": "What is the difference between resizing and cropping?", "a": "Resize forces the picture to the exact width and height, so everything stays in frame but it stretches if the proportions differ from the original. Crop never distorts: it scales the picture until it covers the target size and cuts off whatever overflows, taking equal amounts from both sides."},
        {"q": "Can I choose which part of the picture the crop keeps?", "a": "No. The crop is always centred, so equal amounts come off opposite edges. If the subject is off to one side, the centre crop may cut into it; resize or trim the image in an editor first in that case."},
        {"q": "Will resizing make my photo blurry?", "a": "Making an image smaller is generally clean. Making it larger cannot invent detail that was never captured, so an enlarged photo looks soft. Image Upscaler is the tool aimed at enlargement, though it faces the same underlying limit."},
        {"q": "What are the size limits?", "a": "Width and height each accept values from 1 to 8000 pixels. Very large images are also subject to a pixel-count limit on the server, which protects it from images that would exhaust memory; an image beyond that is rejected rather than processed slowly."},
        {"q": "Does resize keep the aspect ratio?", "a": "Only if the width and height you enter match the original proportions. A different ratio stretches the picture, so either work out the matching dimension first or use crop, which fills the size without distortion."},
        {"q": "Is the original file changed?", "a": "No. The file on your device is untouched — you receive a new image, and the copy on the server is temporary."},
        {"q": "What happens to my image after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "subtitle-converter": [
        {"q": "What's the difference between SRT and VTT?", "a": "SRT is the simplest format. VTT (WebVTT) is the one HTML5 video players load through their track element, and it supports styling. ASS (Advanced SubStation Alpha) allows rich styling such as karaoke colours, but fewer players support it."},
        {"q": "Will styling carry over?", "a": "Text and timing always carry over, and inline tags such as italics are copied as they are. WebVTT cue settings (position and alignment) and STYLE blocks are dropped, and ASS styling and override codes are removed."},
        {"q": "Is my subtitle file uploaded?", "a": "No — pure browser conversion."},
    ],
    "svg-to-png": [
        {"q": "Why convert an SVG to PNG?", "a": "Because plenty of places will not take vector artwork. Image fields in older software, some document and presentation tools, social previews and many upload forms expect a raster image, and PNG is the lossless choice that keeps transparency."},
        {"q": "What scale should I pick?", "a": "Work out the pixel size you actually need. The default of 2 renders at twice the SVG's own dimensions, which suits high-resolution displays. Raise it to 3× or 4× for print or large artwork; 1× keeps the SVG's own size, the smallest option here."},
        {"q": "Is transparency preserved?", "a": "Yes. PNG supports an alpha channel, so an SVG with no background produces a PNG with a transparent one — which is what you want for a logo going over another colour."},
        {"q": "Will the PNG stay sharp if I enlarge it later?", "a": "No, and this is the trade you are making. The SVG is resolution-independent; the PNG is a fixed grid of pixels. Render at the size you need, and keep the SVG as the master for any future size."},
        {"q": "My fonts look wrong in the PNG.", "a": "An SVG that refers to a font by name needs that font to be available where it is rendered, and the server will not have every typeface. Converting text to outlines in your design tool before exporting the SVG makes the result predictable."},
        {"q": "What happens to my file after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
    ],
    "url-encoder": [
        {"q": "What's the difference between URL encoding and base64?", "a": "URL encoding only escapes characters that have special meaning in URLs. Base64 encodes any binary as ASCII (longer but binary-safe). Use Base64 for arbitrary data."},
        {"q": "Why decode a JWT here?", "a": "All in your browser — never paste a real production JWT into a server-side decoder. The standalone JWT Decoder tool shows expiry and claim details too."},
        {"q": "Will the encoded URL be browser-safe?", "a": "Yes — it uses encodeURIComponent, so the output holds only letters, digits, - _ . ! ~ * ' ( ) and %XX escapes. Characters with a special meaning in a URL, such as ? & = / # and spaces, are escaped."},
    ],
    "url-to-pdf": [
        {"q": "Will JavaScript-rendered content show up?", "a": "WeasyPrint doesn't execute JS — only the server-rendered HTML is converted. For JS-heavy SPAs (React, Vue), use the site's print stylesheet or a server-side rendered version."},
        {"q": "Can I convert pages behind a login?", "a": "No — only publicly reachable pages can be converted. Pages behind a login are not supported, because the server fetches the page without your session."},
        {"q": "Does it use my browser cookies?", "a": "No — the fetch is server-side from a clean session. Anonymous, no cookies."},
    ],
    "uuid-generator": [
        {"q": "What's the difference between v4 and v7?", "a": "v4 is purely random — unsortable. v7 (new in 2024) embeds a timestamp prefix so UUIDs sort chronologically. Use v7 for database primary keys."},
        {"q": "How likely is a collision?", "a": "v4 collision after generating 2^61 ≈ 2.3 quintillion UUIDs. Practically impossible."},
        {"q": "Are they cryptographically random?", "a": "Yes. v4 comes from the browser's crypto.randomUUID() and the random part of v7-like IDs from crypto.getRandomValues, both cryptographically secure."},
    ],
    "video-converter": [
        {"q": "Which format to choose?", "a": "MP4: most compatible. WebM: smaller, used for web embedding. MOV: works in Apple ecosystem and Final Cut. MKV: open-source flexible container."},
        {"q": "Will quality suffer?", "a": "Every output is re-encoded, so a small loss is normal. MP4, MOV and MKV use H.264 at CRF 23, WebM uses VP9 at about 1 Mbit/s, and AVI uses MPEG-4 with MP3 audio. None of the outputs is lossless, MKV included."},
        {"q": "How long does it take?", "a": "It depends on the length, the resolution and the format; WebM (VP9) encodes several times more slowly than the others. A conversion that runs longer than three minutes is stopped, so trim or resize long videos first."},
    ],
    "video-merge": [
        {"q": "Do the videos need the same resolution?", "a": "Yes. Clips are not resized, so every clip must have the same width and height; a mix of sizes makes the merge fail. Video Resizer can bring clips that share an aspect ratio to the same height first."},
        {"q": "What about audio-less videos?", "a": "Silent audio is added (anullsrc) for missing tracks so concatenation succeeds."},
        {"q": "Can I add a transition between clips?", "a": "No. Clips are joined directly, one after another; transitions such as crossfades are not supported."},
    ],
    "video-resizer": [
        {"q": "Will upscaling improve quality?", "a": "No — upscaling can't add detail. Use it to match a target resolution, not to improve quality."},
        {"q": "Does this re-encode the audio?", "a": "Yes. The audio is always re-encoded as AAC, alongside the H.264 video."},
        {"q": "Can I crop to a different aspect ratio?", "a": "Not directly — the resizer preserves aspect ratio. For aspect-ratio crops, use a video editor."},
    ],
    "video-thumbnail": [
        {"q": "How do I find a good thumbnail moment?", "a": "Scrub the preview to the moment you want; the slider shows that frame before you run it. To compare several moments at once, Video to PDF lays out evenly spaced frames as PDF pages."},
        {"q": "What resolution will the JPG be?", "a": "1280 pixels wide, with the height set by the video's shape; smaller videos are scaled up to that width. Use Resize Crop Image after if you need a specific size for social media."},
        {"q": "Can I extract multiple thumbnails at once?", "a": "Yes, in two ways: add several videos here to get one frame from each at the same timestamp, or use Video to PDF to lay out evenly spaced frames from one video as PDF pages."},
    ],
    "video-to-pdf": [
        {"q": "Why convert video to PDF?", "a": "Storyboarding, content moderation review, video summarisation for accessibility, lecture notes from recorded talks."},
        {"q": "Can I get just keyframes (scene changes)?", "a": "Frames are sampled at even intervals across the video. Picking frames at scene changes is not supported."},
        {"q": "What resolution are the frames?", "a": "Frames are scaled to 1280 pixels wide and placed one per US Letter page, fitted inside the margins."},
    ],
    "word-counter": [
        {"q": "What counts as a word?", "a": "Whitespace-separated tokens. Hyphenated words ('self-host') count as one. Apostrophes ('don't') keep the word as one."},
        {"q": "How is reading time calculated?", "a": "Word count ÷ 220 words per minute, rounded up to a whole minute. Adjust for technical content (slower) or casual reading (faster)."},
        {"q": "Is my text saved?", "a": "No — everything runs in your browser and persists only in this session."},
    ],

    # ── filled in 2026-09-02 alongside the missing How-To steps ──────
    "accessibility-check": [
        {"q": 'Does passing this check make my PDF legally compliant?', "a": 'No, and no automated tool can tell you that. A checker verifies the machine-testable requirements: whether the document is tagged, declares a language, has a title, and carries alternative text on images. Whether that alt text is actually useful, or the reading order makes sense, is a human judgement. Treat a clean report as the floor, not the finish line.'},
        {"q": 'What is the difference between PDF/UA and WCAG here?', "a": 'PDF/UA is the standard written specifically for PDF structure. WCAG is the general accessibility standard and applies to PDFs as documents people have to read. They overlap heavily, so the report covers both rather than making you run two tools.'},
        {"q": 'Why does my scanned PDF fail almost everything?', "a": 'A scan is a picture of a page. There is no text layer, no tag tree, and nothing for a screen reader to announce. Run OCR first to add real text, then check again.'},
        {"q": "Is my document uploaded to be checked?", "a": "Yes. It is uploaded over HTTPS and checked in the same isolated temporary per-request storage every server tool here uses. Response cleanup removes the job's temporary files after the report is sent, and a background sweep clears anything left behind by an interrupted request. The document is not added to an account or used for model training."},
        {"q": 'Can it fix the problems it finds?', "a": 'No. It reports; it does not rewrite your document. Structural accessibility has to be fixed where the file is authored, because that is the only place the intent is known.'},
    ],
    "bates-remove": [
        {"q": 'Will this remove numbering added by another program?', "a": 'Usually, if the stamps were added as text and you can describe their shape: prefix, digit count, suffix. Numbers burned into a scanned image are part of the picture and cannot be lifted this way.'},
        {"q": 'Why type the prefix and digits?', "a": 'So the tool removes stamps and nothing else. A bare search for numerals would happily delete page numbers, figures and dates. With a prefix or suffix, only text with exactly that around a number is removed; with both blank, anything in the top or bottom inch shaped like letters and at least the given number of digits goes.'},
        {"q": "Does removing Bates numbers change the rest of the page?", "a": "No. Only the matching stamp objects are removed; the remaining text, images and layout are untouched. The result is a new PDF, so the file on your device stays as it was."},
        {"q": 'Can I renumber after removing?', "a": 'Yes. Strip the old stamps here, then use Bates Numbering to apply a fresh sequence with whatever prefix and starting number you need.'},
        {"q": "Is it free and account-free?", "a": "Yes. No account and no watermark, the same as every other tool on the site. Fair-use rate limits apply."},
    ],
    "pdf-to-long-image": [
        {"q": 'Why would I want one tall image instead of a PDF?', "a": 'Because some places will not take a PDF. Chat apps, image-only uploaders, social posts and some ticketing systems accept an image and nothing else. A single tall PNG shows the whole document without asking anyone to download a file.'},
        {"q": 'Should I choose PNG or JPG?', "a": 'PNG for text, screenshots and line art, where it stays sharp and lossless. JPG for scans and photographs, where it produces a far smaller file at quality 90. A long text document saved as JPG will show fringing around the letters.'},
        {"q": 'What resolution are the pages rendered at?', "a": '100 DPI by default, which keeps a normal page readable while stopping a long document from becoming an unusable image. You can also pick 36, 72, 150 or 200 DPI. At 100 DPI a 30-page A4 document produces an image roughly 35,000 pixels tall.'},
        {"q": 'What happens if my pages are different sizes?', "a": 'The canvas takes the width of the widest page and every narrower page is centred on it, so a document mixing portrait and landscape stays aligned instead of stepping left and right.'},
        {"q": 'Is there a page limit?', "a": 'Yes. The tool stitches at most 200 pages, and a JPG cannot be taller than 65,500 pixels, which is about 55 A4 pages at 100 DPI, so choose PNG or a lower resolution for longer documents. Very long images can also be refused by some software; if you hit that, split the PDF first and stitch each part separately.'},
    ],
    "remove-watermark": [
        {"q": 'What kind of watermarks can this actually remove?', "a": 'Text watermarks such as DRAFT or CONFIDENTIAL that repeat across the pages and are see-through or rotated. Removal works when the mark is stored as a separate object, the way the PrivaTools Watermark tool stores it; if it is drawn straight into the page content, the tool reports that it cannot remove it. Image watermarks such as logos are not detected, and a watermark flattened into a scanned page is part of the image and this tool will not find it.'},
        {"q": 'Why does it show me candidates instead of removing everything?', "a": 'Because the repeated text on your page might be a faint letterhead, a rotated margin note or a footer you want to keep. The tool finds what behaves like a watermark and lets you decide, rather than silently stripping page furniture.'},
        {"q": "Will the rest of the page survive?", "a": "Yes. Only the objects you confirm are removed. Surrounding text, images and layout are untouched, and the result is a new PDF, so your original file stays as it was."},
        {"q": 'My watermark is part of a scan. What now?', "a": 'Rasterised watermarks need pixel repair, not object removal. Convert the page to an image and use Remove Image Watermark, accepting that the repair is a reconstruction rather than a perfect recovery.'},
        {"q": 'Should I remove a watermark from a document I did not create?', "a": "Only where you have the right to. A watermark is often a copyright or confidentiality marker, and removing one from someone else's document can be a legal problem regardless of how easy a tool makes it."},
    ],
    "remove-image-watermark": [
        {"q": 'How does the removal actually work?', "a": 'The selected area is reconstructed from the pixels surrounding it. Nothing underneath the watermark was ever stored, so the result is a plausible fill, not a recovery of hidden detail.'},
        {"q": 'When does it look convincing?', "a": 'Over flat or gently textured backgrounds such as sky, walls, paper or a blurred backdrop. Over fine detail, faces or text, the reconstruction will be visible under any real scrutiny.'},
        {"q": 'Which formats can I use?', "a": 'JPG, PNG, WebP and BMP, and the result comes back in the same format. Transparency is not kept: see-through areas usually turn black, so place a transparent PNG on a background first if that matters.'},
        {"q": "Does the image leave my device?", "a": "Yes, for the repair step. It is uploaded over HTTPS to the PrivaTools server, processed in isolated temporary per-request storage, and removed by response cleanup after the result is sent; a background sweep clears anything left behind by an interrupted request. It is not passed to a third-party service or used for model training."},
        {"q": 'Is it legal to remove a watermark?', "a": "That depends entirely on the image. A watermark is usually an ownership mark, and stripping one from a stock photo or someone else's work to avoid licensing it is copyright infringement. Use this on your own images, or where you hold the rights."},
    ],
    "translate-pdf": [
        {"q": "Is my PDF uploaded anywhere?", "a": "The PDF itself is not. With the default 'On this device' engine, text extraction and translation both run in your browser. Two optional steps do send text out: 'My own API key' sends the extracted text directly to the AI provider you chose, and 'Save as PDF' sends the translated text to the PrivaTools server, where it is typeset in temporary per-request storage."},
        {"q": "Why does the first translation take a while?", "a": "Because the model for that language pair, about 107 MB, downloads the first time you use it. After that it is cached in your browser and reused on later visits."},
        {"q": "How good is the translation?", "a": "Good enough to read and understand a document. These are compact models chosen so they can run in a browser, so they will not match a large cloud translator on nuance or long, complex sentences. For better quality, 'My own API key' uses a model from your provider instead."},
        {"q": "Does it keep the original layout?", "a": "No. Text is translated, not typeset: the result is plain text per page, and 'Save as PDF' produces a simple text PDF in a basic Latin font, not a copy of the original design. That font has no letters for scripts such as Cyrillic, Chinese, Arabic or Hindi, or for letters such as ř and ł, which print as boxes, so use the .txt download for those languages."},
        {"q": "Which languages are supported?", "a": "On this device, English can be translated into 19 languages, and 24 languages can be translated into English; each direction is its own model, so English to French does not also fetch French to English. Pairs that do not involve English are not available on-device. 'My own API key' detects the source language itself and offers a wider list of targets."},
        {"q": "Why is nothing translated from my scanned PDF?", "a": "A scan has no text layer, so there is nothing to extract. Run OCR PDF first, then translate the result."},
    ],
}


# Phase 2 conversion aliases share the same proven converter backends as the
# existing image/audio/video format tools, so generate consistent HowTo + FAQ
# coverage instead of hand-writing near-identical blocks 26 times.
_P2_FORMAT_ALIAS_CONTENT: tuple[tuple[str, str, str, str, str], ...] = (
    ("jpg-to-tiff", "JPG to TIFF", "a JPG or JPEG image", "a TIFF image", "image"),
    ("png-to-tiff", "PNG to TIFF", "a PNG image", "a TIFF image", "image"),
    ("webp-to-tiff", "WebP to TIFF", "a WebP image", "a TIFF image", "image"),
    ("jpg-to-bmp", "JPG to BMP", "a JPG or JPEG image", "a BMP image", "image"),
    ("png-to-bmp", "PNG to BMP", "a PNG image", "a BMP image", "image"),
    ("webp-to-bmp", "WebP to BMP", "a WebP image", "a BMP image", "image"),
    ("mp3-to-wav", "MP3 to WAV", "an MP3 audio file", "a WAV audio file", "audio"),
    ("wav-to-mp3", "WAV to MP3", "a WAV audio file", "an MP3 audio file", "audio"),
    ("flac-to-mp3", "FLAC to MP3", "a FLAC audio file", "an MP3 audio file", "audio"),
    ("ogg-to-mp3", "OGG to MP3", "an OGG audio file", "an MP3 audio file", "audio"),
    ("aac-to-mp3", "AAC to MP3", "an AAC audio file", "an MP3 audio file", "audio"),
    ("mp3-to-ogg", "MP3 to OGG", "an MP3 audio file", "an OGG audio file", "audio"),
    ("mp3-to-flac", "MP3 to FLAC", "an MP3 audio file", "a FLAC audio file", "audio"),
    ("mp3-to-aac", "MP3 to AAC", "an MP3 audio file", "an AAC audio file", "audio"),
    ("wav-to-flac", "WAV to FLAC", "a WAV audio file", "a FLAC audio file", "audio"),
    ("wav-to-ogg", "WAV to OGG", "a WAV audio file", "an OGG audio file", "audio"),
    ("mkv-to-mp4", "MKV to MP4", "an MKV video file", "an MP4 video file", "video"),
    ("mp4-to-mov", "MP4 to MOV", "an MP4 video file", "a MOV video file", "video"),
    ("mov-to-webm", "MOV to WebM", "a MOV video file", "a WebM video file", "video"),
    ("mkv-to-webm", "MKV to WebM", "an MKV video file", "a WebM video file", "video"),
    ("mp4-to-avi", "MP4 to AVI", "an MP4 video file", "an AVI video file", "video"),
    ("avi-to-webm", "AVI to WebM", "an AVI video file", "a WebM video file", "video"),
    ("webm-to-mov", "WebM to MOV", "a WebM video file", "a MOV video file", "video"),
    ("mov-to-mkv", "MOV to MKV", "a MOV video file", "an MKV video file", "video"),
    ("webm-to-gif", "WebM to GIF", "a WebM video file", "an animated GIF", "gif"),
    ("mov-to-gif", "MOV to GIF", "a MOV video file", "an animated GIF", "gif"),
)


# Per-slug bespoke FAQ for the format-alias converters. Without these, every
# converter in a media-kind cluster (image/audio/video/gif) renders a
# byte-identical template FAQ — a near-duplicate "doorway" pattern Google
# declines to index. Each entry answers the REAL technical distinction of that
# specific conversion (lossy vs lossless, container vs codec, format use) so the
# 26 pages read as genuinely different from one another.
_ALIAS_FAQ_OVERRIDES: dict[str, list[dict[str, str]]] = {
    # ── Image ──────────────────────────────────────────────────────────
    "jpg-to-tiff": [
        {"q": "Does converting JPG to TIFF improve quality?", "a": "No. JPG is already lossy, and TIFF stores those exact pixels without further loss — but it cannot recover detail JPG discarded. Convert when a workflow (archival, print, scanning, OCR) needs a lossless/uncompressed container, not to 'upscale' a JPG."},
        {"q": "Why is the TIFF so much larger than the JPG?", "a": "TIFF is uncompressed or losslessly compressed, so a 2 MB JPG can become 20–40 MB. That's expected — you trade file size for a lossless, edit- and print-friendly format."},
        {"q": "Is the conversion private?", "a": "It runs on the PrivaTools server with local image libraries, not a third-party API. The upload is held in isolated temporary per-request storage, and response cleanup removes the input and output after the TIFF is sent."},
    ],
    "png-to-tiff": [
        {"q": "Is PNG transparency preserved in the TIFF?", "a": "Yes. The TIFF keeps the alpha channel, so transparent areas stay transparent. Some print and scanning workflows ignore TIFF transparency, so flatten the image onto a background first if the recipient needs an opaque file."},
        {"q": "Why convert PNG to TIFF?", "a": "TIFF is the standard for print prepress, scanning, and long-term archival. PNG→TIFF is lossless, so no image detail is lost in the conversion."},
        {"q": "Are my images uploaded to a third party?", "a": "No. The conversion runs on the PrivaTools server with local image libraries. Uploads are held in temporary per-request storage and removed by response cleanup after the result is sent."},
    ],
    "webp-to-tiff": [
        {"q": "Does WebP to TIFF lose quality?", "a": "If your WebP is lossy, TIFF can't restore discarded detail; if it's lossless WebP, the TIFF is pixel-identical. Either way TIFF gives you the lossless container that print and archival tools expect."},
        {"q": "Why not just keep the WebP?", "a": "Many print, scanner, and legacy desktop applications don't read WebP at all. TIFF is universally supported by those workflows."},
        {"q": "Is it processed privately?", "a": "The WebP is uploaded to the PrivaTools server and converted with local image libraries, not a third-party API. Response cleanup removes the input and the TIFF from temporary storage after the result is sent."},
    ],
    "jpg-to-bmp": [
        {"q": "Why convert JPG to BMP?", "a": "BMP is an uncompressed bitmap that legacy Windows apps, embedded systems, and some signage/industrial tools require. JPG→BMP decodes to raw pixels (lossless from the JPG) for maximum compatibility."},
        {"q": "Will the BMP be much larger?", "a": "Yes — BMP stores every pixel uncompressed, so expect roughly 5–20× the JPG's size."},
        {"q": "Are files kept after conversion?", "a": "No. Input and output are temporary files; response cleanup removes them after the BMP is sent, and a background sweep clears anything left behind by an interrupted request."},
    ],
    "png-to-bmp": [
        {"q": "Is PNG transparency kept in BMP?", "a": "No. The alpha channel is dropped rather than blended onto white, so transparent areas usually come out black in the BMP. If you need to keep transparency, use PNG to TIFF instead."},
        {"q": "Why convert to BMP?", "a": "For legacy Windows software, embedded displays, and tools that only accept uncompressed bitmap input."},
        {"q": "Is the conversion private?", "a": "It runs on the PrivaTools server with local image libraries, not a third-party API. The files are temporary and are removed by response cleanup after the BMP is sent."},
    ],
    "webp-to-bmp": [
        {"q": "Why convert WebP to BMP?", "a": "To use a modern WebP image in older software or hardware that only reads uncompressed bitmaps. The BMP is a raw, maximally-compatible copy."},
        {"q": "Is the BMP lossless?", "a": "The BMP is a lossless copy of the decoded WebP pixels; if the source WebP was lossy, those pixels are already final and can't be improved."},
        {"q": "Are uploads retained?", "a": "No. Files are temporary and are removed by response cleanup after the download is sent; a background sweep clears anything an interrupted request leaves behind."},
    ],
    # ── Audio ──────────────────────────────────────────────────────────
    "mp3-to-wav": [
        {"q": "Does MP3 to WAV improve sound quality?", "a": "No. MP3 is lossy; WAV just stores that same audio uncompressed. The detail MP3 removed can't be restored — convert when a DAW, CD-authoring, or editing tool requires uncompressed PCM/WAV input."},
        {"q": "Why is the WAV file so big?", "a": "WAV is uncompressed PCM — roughly 10 MB per minute of stereo audio — so a 4 MB MP3 can become around 40 MB."},
        {"q": "Are my audio files stored?", "a": "No. Input and output are temporary and deleted after the download response is sent. Conversion uses FFmpeg server-side."},
    ],
    "wav-to-mp3": [
        {"q": "What bitrate is used?", "a": "192 kbps, a solid default for music and speech; this page has no bitrate setting. MP3 is lossy, so a higher bitrate keeps more detail at the cost of a larger file: Audio Converter offers 256 and 320 kbps."},
        {"q": "How much smaller will the MP3 be?", "a": "About 7× smaller than a CD-quality WAV, because the MP3 is encoded at 192 kbps."},
        {"q": "Is the conversion private?", "a": "FFmpeg runs on the PrivaTools server, not a third-party service. The WAV and the MP3 are temporary files that response cleanup removes after the result is sent."},
    ],
    "flac-to-mp3": [
        {"q": "Will I lose quality converting FLAC to MP3?", "a": "Yes — FLAC is lossless and MP3 is lossy, so the conversion discards some audio data. This page encodes at 192 kbps; Audio Converter goes up to 320 kbps. Either way it's a one-way trade for a smaller, universally-compatible file."},
        {"q": "Why convert FLAC to MP3 at all?", "a": "MP3 plays on virtually every device and is roughly 3–6× smaller than FLAC — ideal for phones, portable players, and sharing."},
        {"q": "Are files retained?", "a": "No. Uploads and outputs are temporary files, removed by response cleanup after the download is sent."},
    ],
    "ogg-to-mp3": [
        {"q": "Why convert OGG to MP3?", "a": "OGG Vorbis isn't supported by some players, car stereos, and editing apps; MP3 is nearly universal. Both are lossy, so this is about compatibility, not quality."},
        {"q": "Is there quality loss?", "a": "Re-encoding one lossy format to another (transcoding) loses a little quality. This page encodes at 192 kbps; Audio Converter offers up to 320 kbps to keep the loss smaller."},
        {"q": "Is it processed privately?", "a": "The file is converted by FFmpeg on the PrivaTools server, not a third-party service, and the temporary input and output are removed by response cleanup after the result is sent."},
    ],
    "aac-to-mp3": [
        {"q": "Does AAC to MP3 reduce quality?", "a": "Both are lossy, so transcoding AAC→MP3 loses a little detail. This page encodes at 192 kbps; Audio Converter offers up to 320 kbps. Convert for devices that don't support AAC/M4A."},
        {"q": "Why isn't my AAC playing everywhere?", "a": "AAC (often in an .m4a wrapper) has excellent quality-per-byte, but some older or non-Apple devices prefer MP3."},
        {"q": "Are files kept?", "a": "No — temporary input/output, deleted after the download response."},
    ],
    "mp3-to-ogg": [
        {"q": "Will MP3 to OGG sound better?", "a": "No — both are lossy, and the source MP3's lost detail can't be recovered. OGG Vorbis can be slightly more efficient at the same bitrate, which is useful for open-format projects and games."},
        {"q": "Why use OGG?", "a": "It's a royalty-free, open format favored by game engines (Godot, Unity) and open-source software."},
        {"q": "Is the conversion private?", "a": "Yes — local FFmpeg on the PrivaTools backend; files removed after the response."},
    ],
    "mp3-to-flac": [
        {"q": "Does MP3 to FLAC restore lossless quality?", "a": "No. FLAC will losslessly preserve whatever is in the MP3, but it cannot recreate the detail MP3 already discarded — you get a larger file, not better audio. Convert only when a tool specifically requires a lossless container."},
        {"q": "When is MP3 to FLAC actually useful?", "a": "When a workflow or device only accepts FLAC/lossless input, or to archive the file without further generational loss."},
        {"q": "Are files retained?", "a": "No. Uploads and outputs are temporary and deleted after the download."},
    ],
    "mp3-to-aac": [
        {"q": "Is AAC better than MP3?", "a": "AAC generally sounds better than MP3 at the same bitrate, but transcoding an existing MP3 won't recover lost detail. The output is a raw .aac file, not an .m4a."},
        {"q": "What bitrate is used?", "a": "A 192 kbps target, with no setting on this page; Audio Converter offers 64 to 320 kbps. AAC is efficient, so 128–192 kbps often matches a higher-bitrate MP3."},
        {"q": "Is it private?", "a": "The conversion is a local FFmpeg run on the PrivaTools server. Input and output are temporary files that response cleanup removes after the result is sent."},
    ],
    "wav-to-flac": [
        {"q": "Is WAV to FLAC lossless?", "a": "Yes — FLAC compresses WAV losslessly, typically to 40–60% of the size with zero quality loss. It's the ideal way to archive uncompressed audio."},
        {"q": "Will the FLAC play everywhere?", "a": "FLAC is widely supported on desktops and modern players, but not on every older or portable device. Keep WAV or use WAV→MP3 for those."},
        {"q": "Are files kept?", "a": "No — temporary input/output, removed after the download response."},
    ],
    "wav-to-ogg": [
        {"q": "Why convert WAV to OGG?", "a": "OGG Vorbis produces small, good-quality lossy files in a royalty-free format — handy for games, web audio, and open-source projects, and far smaller than WAV."},
        {"q": "Is OGG lossy or lossless?", "a": "OGG Vorbis here is lossy, encoded with a 192 kbps target and no quality setting on this page. For lossless, use WAV→FLAC instead."},
        {"q": "Is the conversion private?", "a": "It is a local FFmpeg run on the PrivaTools server, with no third-party service involved. The temporary input and output are removed by response cleanup after the result is sent."},
    ],
    # ── Video ──────────────────────────────────────────────────────────
    "mkv-to-mp4": [
        {"q": "Does MKV to MP4 re-encode the video?", "a": "Yes. Every file is re-encoded to H.264 video (CRF 23) and AAC audio, even when the MKV's streams would already fit in an MP4, so it is not a lossless container swap. Only one audio track is kept."},
        {"q": "Why MP4 instead of MKV?", "a": "MP4 plays natively on phones, browsers, TVs, and editors; MKV is a flexible container but far less universally supported."},
        {"q": "Are videos retained after conversion?", "a": "No. Uploaded videos and outputs are temporary and deleted after the response."},
    ],
    "mp4-to-mov": [
        {"q": "Why convert MP4 to MOV?", "a": "MOV is Apple's QuickTime container, preferred by Final Cut Pro, iMovie, and some macOS/iOS workflows. This tool re-encodes the video rather than rewrapping it, even when the codecs would fit."},
        {"q": "Is quality lost?", "a": "A little. Every file is re-encoded as H.264 at CRF 23 with AAC audio, so the MOV is not a bit-for-bit copy of the MP4's streams."},
        {"q": "Are files kept?", "a": "No — temporary input/output, deleted after the download."},
    ],
    "mov-to-webm": [
        {"q": "Why convert MOV to WebM?", "a": "WebM (VP9/Opus) is the open format for fast-loading HTML5 video and is well-supported in browsers. MOV→WebM always re-encodes because the codecs differ."},
        {"q": "Will the file get smaller?", "a": "Usually yes. The video is encoded at about 1 Mbit/s, far below the bitrate of most phone and camera MOVs, so the file shrinks a lot; a MOV that is already small may not."},
        {"q": "Is it processed privately?", "a": "Yes — local FFmpeg on the PrivaTools backend; files removed after the response."},
    ],
    "mkv-to-webm": [
        {"q": "Does MKV to WebM re-encode?", "a": "Yes, fully. The video is always re-encoded as VP9 at about 1 Mbit/s and the audio as Opus, even when the MKV already holds VP8, VP9, Vorbis or Opus."},
        {"q": "Why convert to WebM?", "a": "To embed open-format video on the web without proprietary codecs."},
        {"q": "Are uploads retained?", "a": "No — temporary files, deleted after the response."},
    ],
    "mp4-to-avi": [
        {"q": "Why convert MP4 to AVI?", "a": "AVI is an older container some legacy editors, players, and devices still require. The conversion re-encodes into an AVI-friendly codec, so expect a larger file than the MP4."},
        {"q": "Will quality drop?", "a": "AVI codecs are less efficient than modern H.264/MP4, so files are larger and re-encoding causes minor loss. Use AVI only when something specifically needs it."},
        {"q": "Are files kept?", "a": "No — temporary input/output, removed after the download response."},
    ],
    "avi-to-webm": [
        {"q": "Why convert AVI to WebM?", "a": "To turn an old AVI clip into a small, web-ready, open-format video. WebM (VP9/Opus) re-encodes the AVI for efficient browser playback."},
        {"q": "Will it shrink the file?", "a": "It depends on the AVI's bitrate. The WebM video is encoded at about 1 Mbit/s, so a high-bitrate capture shrinks a lot, while a compact DivX or Xvid file may stay about the same size."},
        {"q": "Is it private?", "a": "Yes — local FFmpeg conversion; files deleted after the response."},
    ],
    "webm-to-mov": [
        {"q": "Why convert WebM to MOV?", "a": "To bring web video into Apple editors (Final Cut, iMovie) that prefer QuickTime/MOV. The codecs differ, so this re-encodes to a MOV-friendly codec like H.264."},
        {"q": "Any quality loss?", "a": "Re-encoding causes minor loss; the defaults target visual parity with the source."},
        {"q": "Are files retained?", "a": "No — temporary files, deleted after the download."},
    ],
    "mov-to-mkv": [
        {"q": "Why convert MOV to MKV?", "a": "MKV is a flexible archival container that can hold multiple audio and subtitle tracks. This tool re-encodes the streams rather than moving them across, so it is not a lossless remux."},
        {"q": "Is it lossless?", "a": "No. The video is re-encoded as H.264 at CRF 23 and the audio as AAC, so there is a small quality loss."},
        {"q": "Are uploads kept?", "a": "No — temporary input/output, removed after the response."},
    ],
    # ── Video → GIF ────────────────────────────────────────────────────
    "webm-to-gif": [
        {"q": "Why is the GIF larger than the WebM?", "a": "GIF stores every frame as a separate image and is capped at 256 colors, so it's inefficient — a short WebM can become a much larger GIF. Trim the clip first to keep the size down."},
        {"q": "Will the GIF have sound?", "a": "No — GIF is a silent image-animation format and cannot contain audio."},
        {"q": "What clip length works best?", "a": "Keep it under about 6–10 seconds; longer clips produce very large GIFs."},
    ],
    "mov-to-gif": [
        {"q": "How long should the clip be?", "a": "Short — a few seconds. GIF encodes every frame as an image, so a long MOV becomes a very large GIF. Trim before converting."},
        {"q": "Does the GIF keep audio?", "a": "No — GIF has no audio track. Convert to MP4 or WebM if you need sound."},
        {"q": "Why convert MOV to GIF?", "a": "For short looping clips in chats, docs, and on the web where autoplaying video isn't supported."},
    ],
}


for _slug, _name, _input_label, _output_label, _kind in _P2_FORMAT_ALIAS_CONTENT:
    TOOL_HOWTO.setdefault(_slug, [
        {"name": f"Upload {_input_label}", "text": f"Drop or select {_input_label}. Files are processed by the same local PrivaTools converter used by the main {_kind} tools."},
        {"name": f"Convert to {_output_label}", "text": f"Click Convert. PrivaTools preselects the right output format for {_name}, so there are no extra settings to configure."},
        {"name": f"Download {_output_label}", "text": "The converted file downloads when it is ready. Response cleanup removes the temporary input and output files after the response is sent."},
    ])
    _bespoke_faq = _ALIAS_FAQ_OVERRIDES.get(_slug)
    if _bespoke_faq:
        TOOL_FAQ.setdefault(_slug, _bespoke_faq)
    elif _kind == "image":
        TOOL_FAQ.setdefault(_slug, [
            {"q": "Does this upload to a third-party image service?", "a": "No. The conversion runs on the self-hosted PrivaTools backend with Pillow/libvips-style local processing. Files are not sent to an external conversion API."},
            {"q": "Will image metadata be kept?", "a": "Image conversion strips sensitive metadata by default for privacy, including GPS and camera metadata where present."},
            {"q": "Can I use this for legacy software?", "a": "Yes. TIFF and BMP outputs are included specifically for archive, print, scanner, and older Windows workflows that reject modern formats."},
        ])
    elif _kind == "audio":
        TOOL_FAQ.setdefault(_slug, [
            {"q": "Does conversion improve the original audio quality?", "a": "No conversion can restore detail that was already lost. Use it for compatibility, smaller files, or a required container/codec."},
            {"q": "What engine handles the audio conversion?", "a": "FFmpeg runs server-side with standard codecs for MP3, WAV, OGG, FLAC, and AAC."},
            {"q": "Are audio files stored?", "a": "No. Input and output files are temporary and deleted after the download response is returned."},
        ])
    elif _kind == "gif":
        TOOL_FAQ.setdefault(_slug, [
            {"q": "Can I make a GIF from a long video?", "a": "Short clips work best. GIFs grow quickly because every frame is stored as an image; trim the source first for smaller output."},
            {"q": "Does the GIF include audio?", "a": "No. GIF is an image animation format and cannot contain audio."},
            {"q": "What engine creates the GIF?", "a": "FFmpeg extracts frames from the uploaded video and encodes them as an animated GIF on the PrivaTools backend."},
        ])
    else:
        TOOL_FAQ.setdefault(_slug, [
            {"q": "Will the converted video work everywhere?", "a": "MP4 is the most compatible output. MOV is best for Apple workflows, WebM for web embeds, AVI for legacy devices, and MKV for archival containers."},
            {"q": "Does video conversion reduce quality?", "a": "PrivaTools uses sensible FFmpeg defaults. Some re-encoding is normal when changing containers/codecs, but the defaults target compatibility without obvious quality loss."},
            {"q": "Are videos retained after conversion?", "a": "No. Uploaded videos and converted outputs are temporary and deleted after the response is sent."},
        ])
