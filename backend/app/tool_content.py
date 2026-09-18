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
        {"name": "Add your PDFs", "text": "Drop or select one or more PDFs, up to 500 MB each and up to 100 in one go. Documents full of photos or scans shrink the most."},
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
        {"name": "Set permission restrictions", "text": "Optionally restrict printing, text copying, form filling, content modification, and page extraction independently. Defaults to 'all allowed once unlocked'."},
        {"name": "Download the encrypted PDF", "text": "Click Protect. The output uses AES-256 encryption and requires your password to open in any PDF reader."},
    ],
    "unlock-pdf": [
        {"name": "Add the locked PDFs", "text": "Drop or select one or more password-protected PDFs, up to 100 at a time and 500 MB each."},
        {"name": "Enter the password", "text": "Type the existing password. It must be correct: this tool removes protection you already have the key to, it does not guess or crack passwords."},
        {"name": "Unlock and download", "text": "Run it. The result opens without a password, and restrictions such as no-print or no-copy are removed as well."},
    ],
    "rotate-pdf": [
        {"name": "Drop your PDF", "text": "Select a PDF up to 500 MB. Thumbnail previews of every page load automatically so you can see what needs rotating."},
        {"name": "Select pages to rotate", "text": "Click individual page thumbnails to target specific pages, or 'Select all' for whole-document rotation. Mix-and-match is supported (different angles per page)."},
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
        {"name": "Select the document language", "text": "Choose the primary language (or multiple languages) so the OCR engine uses the correct dictionary for accuracy."},
        {"name": "Run OCR and download", "text": "Click Process. Tesseract extracts text and creates an invisible text layer, making the PDF fully searchable and copyable."},
    ],
    "redact-pdf": [
        {"name": "Upload the PDF", "text": "Select the document containing sensitive information you need to permanently remove."},
        {"name": "Mark areas to redact", "text": "Draw rectangles over text, images, or regions on each page. You can also search for a word or phrase to auto-select all occurrences."},
        {"name": "Preview the redactions", "text": "Toggle the preview to verify that the correct areas are blacked out before committing."},
        {"name": "Apply redactions and download", "text": "Click Redact. The underlying content is permanently destroyed — it cannot be recovered, even by removing the black boxes."},
    ],
    "flatten-pdf": [
        {"name": "Upload the PDF", "text": "Select a PDF that contains form fields, annotations, or layers you want to flatten."},
        {"name": "Choose flattening options", "text": "Decide whether to flatten form fields only, annotations only, or everything. Flattening converts interactive elements into static page content."},
        {"name": "Download the flattened PDF", "text": "Click Flatten. The result is a clean PDF where all content is baked into the pages, preventing further edits."},
    ],
    "bookmarks": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB. Existing bookmarks, if any, are listed automatically."},
        {"name": "Edit the bookmark tree", "text": "Add, rename, reorder, or delete bookmarks. Set the target page number for each entry. You can nest bookmarks to create a multi-level table of contents."},
        {"name": "Save and download", "text": "Click Save. The updated bookmark tree is embedded into the PDF for easy navigation in any reader."},
    ],
    "form-creator": [
        {"name": "Upload a PDF or start blank", "text": "Upload an existing PDF to add form fields on top, or start with a blank page."},
        {"name": "Add form fields", "text": "Drag text inputs, checkboxes, dropdowns, radio buttons, or signature fields onto the page. Set field names and validation rules."},
        {"name": "Configure form properties", "text": "Set tab order, default values, and required-field flags. Preview the form to test interactivity."},
        {"name": "Export the fillable PDF", "text": "Click Save. The PDF contains standard AcroForm fields that work in any PDF reader."},
    ],
    "extract-tables": [
        {"name": "Upload the PDF", "text": "Select a PDF that contains one or more tables you need to extract as structured data."},
        {"name": "Select pages", "text": "Choose specific pages or let the tool auto-detect all tables across the entire document."},
        {"name": "Pick the output format", "text": "Choose CSV, Excel (.xlsx), or JSON. Each detected table becomes a separate sheet or file."},
        {"name": "Download the extracted data", "text": "Click Extract. Tables are parsed using Camelot/Tabula and delivered in the chosen format inside a ZIP."},
    ],
    "pdf-to-pdfa": [
        {"name": "Upload the PDF", "text": "Select a standard PDF you want to convert into the PDF/A archival format."},
        {"name": "Choose the conformance level", "text": "Select PDF/A-1b (basic), PDF/A-2b (supports transparency and JPEG2000), or PDF/A-3b (allows embedded files)."},
        {"name": "Convert and download", "text": "Click Convert. The tool embeds fonts, converts color spaces to sRGB, and validates compliance before returning the PDF/A file."},
    ],

    # ── PDF conversion ────────────────────────────────────────────────
    "image-to-pdf": [
        {"name": "Upload images", "text": "Select one or more images (JPG, PNG, WebP, BMP, TIFF). Each image can be up to 500 MB."},
        {"name": "Arrange and configure", "text": "Reorder images by dragging thumbnails. Set page size (A4, Letter, or fit-to-image) and orientation."},
        {"name": "Convert to PDF", "text": "Click Convert. Each image becomes a full page in the resulting PDF, maintaining original resolution."},
    ],
    "txt-to-pdf": [
        {"name": "Upload a text file or paste text", "text": "Select a .txt file up to 500 MB or paste plain text directly into the editor."},
        {"name": "Choose formatting", "text": "Pick the font family, font size, page size, and margins. Monospace fonts work best for code or tabular content."},
        {"name": "Generate the PDF", "text": "Click Convert. The text is reflowed into paginated PDF pages with the selected formatting."},
    ],
    "office-to-pdf": [
        {"name": "Upload an Office document", "text": "Select a Word (.docx), Excel (.xlsx), or PowerPoint (.pptx) file up to 500 MB."},
        {"name": "Convert via LibreOffice", "text": "The server uses LibreOffice in headless mode for high-fidelity conversion, preserving fonts, tables, charts, and layouts."},
        {"name": "Download the PDF", "text": "Click Convert. The resulting PDF is ready within seconds for most documents."},
    ],
    "word-to-pdf": [
        {"name": "Add the Word document", "text": "Drop or select a .docx file up to 500 MB. Older .doc files are not accepted here; Office to PDF handles a wider range of formats."},
        {"name": "Convert to PDF", "text": "Run the conversion. The document is laid out by LibreOffice on the server and exported as a PDF."},
        {"name": "Download and check the PDF", "text": "Open the PDF and check fonts, page breaks and any tables, especially if the document uses unusual typefaces."},
    ],
    "epub-to-pdf": [
        {"name": "Upload an EPUB file", "text": "Select an .epub e-book file up to 500 MB."},
        {"name": "Choose page layout", "text": "Select a page size (A4, Letter, or custom dimensions). The tool reflows text and embeds images to match the chosen layout."},
        {"name": "Convert and download", "text": "Click Convert. Chapters, formatting, and embedded images are preserved in the output PDF."},
    ],
    "html-to-pdf": [
        {"name": "Enter a URL or paste HTML", "text": "Type a public URL to render, or paste raw HTML/CSS directly into the editor."},
        {"name": "Configure rendering options", "text": "Set page size, margins, and whether to include background graphics. JavaScript rendering is supported for dynamic pages."},
        {"name": "Generate the PDF", "text": "Click Convert. The server uses a headless browser to render the page and produce a pixel-perfect PDF."},
    ],
    "xml-to-pdf": [
        {"name": "Upload an XML file", "text": "Select an .xml file up to 500 MB. Common schemas like RSS, Atom, and XHTML are supported."},
        {"name": "Choose display format", "text": "Select tree view (collapsible hierarchy) or formatted table view for structured data."},
        {"name": "Convert and download", "text": "Click Convert. The XML is rendered into a readable, paginated PDF document."},
    ],
    "csv-to-pdf": [
        {"name": "Upload a CSV file", "text": "Select a .csv or .tsv file up to 500 MB. The first row is treated as column headers by default."},
        {"name": "Customize table appearance", "text": "Set font size, enable zebra striping, choose landscape or portrait orientation. Wide tables automatically wrap or scale to fit."},
        {"name": "Convert to PDF", "text": "Click Convert. The data is rendered into a clean, paginated table in the output PDF."},
    ],
    "json-to-pdf": [
        {"name": "Upload a JSON file or paste JSON", "text": "Select a .json file up to 500 MB or paste JSON directly into the editor."},
        {"name": "Choose the rendering style", "text": "Pick syntax-highlighted code view for developers or a table/tree view for structured data."},
        {"name": "Convert and download", "text": "Click Convert. The JSON is rendered into a paginated, readable PDF with proper indentation and optional line numbers."},
    ],
    "pdf-to-word": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB. Documents created digitally, with real text rather than scanned images, convert best."},
        {"name": "Convert to Word", "text": "Run the conversion. The text is read page by page and rebuilt as Word paragraphs, keeping font names, text colours and paragraph spacing where the PDF provides them."},
        {"name": "Download and review the .docx", "text": "Open the result in Word or another editor and check the layout, especially tables, columns and headers, before relying on it."},
    ],
    "pdf-to-excel": [
        {"name": "Drop your PDF", "text": "Select a PDF up to 500 MB that contains tables or tabular data. Scanned PDFs need OCR first via the OCR PDF tool."},
        {"name": "Choose pages to scan", "text": "Pick specific pages with tables, or let the tool auto-detect tables across the whole document using Camelot and Tabula libraries."},
        {"name": "Tune detection (optional)", "text": "For borderless or unusual tables, switch detection mode (lattice for ruled tables, stream for whitespace-separated). Default auto-selects the best."},
        {"name": "Convert and download", "text": "Click Convert. Each detected table becomes a separate sheet in the resulting .xlsx file, with rows and columns preserved. Multiple tables across pages are combined into one workbook."},
    ],
    "pdf-to-text": [
        {"name": "Upload the PDF", "text": "Select a text-based or scanned PDF up to 500 MB."},
        {"name": "Choose extraction mode", "text": "Select plain text extraction for text-based PDFs, or enable OCR for scanned documents. Pick the OCR language if needed."},
        {"name": "Download the text", "text": "Click Convert. The extracted text is returned as a .txt file with page breaks preserved."},
    ],
    "pdf-to-image": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB. The tool displays a page-count summary."},
        {"name": "Configure output settings", "text": "Choose the image format (PNG, JPG, or WebP), resolution (72–600 DPI), and which pages to convert."},
        {"name": "Convert and download", "text": "Click Convert. Each page becomes a separate image file, delivered in a ZIP archive."},
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
        {"name": "Trim and download", "text": "Run the trim. Audio is cut without re-encoding (FLAC is rewritten losslessly); video is re-encoded so the cut starts on the exact frame you chose."},
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
        {"name": "Add the audio file", "text": "Drop or select an audio file up to 500 MB."},
        {"name": "Choose the output format", "text": "Pick MP3, AAC, OGG, FLAC or WAV. MP3 is the most widely compatible; FLAC and WAV are lossless."},
        {"name": "Choose a bitrate", "text": "For MP3, AAC and OGG choose from 64 to 320 kbps; the default is 192. Higher bitrates keep more detail and make bigger files. WAV and FLAC are lossless, so the bitrate does not apply."},
        {"name": "Convert and download", "text": "Run the conversion and save the new file."},
    ],

    # ── v1.1.0 + v1.2.0 additions ─────────────────────────────────────────
    "highlight-pdf": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB containing the text you want to highlight."},
        {"name": "Enter your search phrase", "text": "Type the word or phrase to highlight. Use the case-sensitive toggle for exact matches."},
        {"name": "Pick a highlight color", "text": "Choose yellow, green, pink, blue, or orange. Highlights are added as real PDF annotations."},
        {"name": "Download the highlighted PDF", "text": "Click Highlight. The tool finds every occurrence on every page and writes a new PDF with permanent highlight annotations."},
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
        {"name": "Pick a summary length", "text": "Choose Short, Medium or Long. The setting controls how much is written for each chunk of the document, so a long PDF still produces a longer summary than a short one."},
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
        {"name": "Convert and download", "text": "Click Convert. The tool extracts vector graphics page-by-page using PyMuPDF and packages the SVGs into a ZIP."},
    ],
    "pdf-to-html": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB. PyMuPDF's HTML exporter preserves fonts and positioning."},
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
        {"name": "Upload multiple PDFs", "text": "Drag up to 50 PDF files. Up to 500 MB per file."},
        {"name": "Pick compression level", "text": "Light (modest reduction, best quality), Recommended (balanced — default), Extreme (smallest files, some image-quality loss)."},
        {"name": "Compress and download as ZIP", "text": "Click Compress. Files are processed in parallel across 4 workers. Results are bundled into a ZIP with a savings summary."},
    ],
    "pdf-page-counter": [
        {"name": "Upload up to 100 PDFs", "text": "Drag up to 100 PDF files. The tool reads only metadata, not content — page counts come back almost instantly."},
        {"name": "Read the per-file count", "text": "Each filename appears with its page count. The total across all files appears at the bottom — ideal for print quotes."},
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
        {"name": "Add the file to attach", "text": "Drop any file — image, spreadsheet, .zip, even another PDF. PrivaTools embeds it without altering the visible content."},
        {"name": "Download the result", "text": "Click Attach. The output PDF has your file embedded as an attachment; readers like Acrobat show it in the Attachments panel."},
    ],
    "add-hyperlinks": [
        {"name": "Upload your PDF", "text": "Select a PDF up to 500 MB."},
        {"name": "Define each link", "text": "Specify the page, rectangle coordinates (x, y, width, height in PDF points), and target URL. Coordinates use the PDF coordinate system where (0,0) is bottom-left."},
        {"name": "Download the linked PDF", "text": "Click Add Links. PrivaTools embeds clickable hyperlink annotations at each rectangle, opening the target URL on click in any PDF reader."},
    ],
    "add-shapes": [
        {"name": "Upload the PDF", "text": "Select a PDF up to 500 MB."},
        {"name": "Define shapes", "text": "For each shape, specify type (rectangle, ellipse, line, polygon), page number, coordinates, color, and stroke width."},
        {"name": "Apply and download", "text": "Click Add Shapes. The shapes are drawn directly onto the page content; they survive copy-paste, printing, and PDF/A conversion."},
    ],
    "alternate-mix": [
        {"name": "Upload two PDFs", "text": "Select two PDFs to interleave. They don't need the same page count."},
        {"name": "Choose mode", "text": "Alternate: page 1A, 1B, 2A, 2B… Reverse-alternate: same, but the second PDF is reversed first (useful for double-sided scans where the back side scans bottom-to-top)."},
        {"name": "Download the mixed PDF", "text": "Click Mix. The output is a single PDF with pages interleaved from both inputs."},
    ],
    "annotate-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Add annotations", "text": "Use the toolbar to add highlights, underlines, strikethroughs, sticky notes, and text boxes. Each annotation has a position, page, content, and color."},
        {"name": "Save and download", "text": "Click Save. Annotations are added as standard PDF annotation objects — they appear in every PDF reader and can be edited later."},
    ],
    "auto-crop": [
        {"name": "Upload the PDF", "text": "Drop a PDF up to 500 MB. Best for scanned documents with consistent margins."},
        {"name": "Let auto-detection scan", "text": "PrivaTools analyses the bounding box of actual content on each page using PyMuPDF — ignoring whitespace, page numbers in margins, and scan-edge artifacts."},
        {"name": "Download the cropped PDF", "text": "Click Auto Crop. Each page's MediaBox is shrunk to the detected content bounding box, eliminating dead margins."},
    ],
    "bates-numbering": [
        {"name": "Upload the PDF (or batch)", "text": "Drop a PDF up to 500 MB. The numbering is applied to one document per run."},
        {"name": "Configure the Bates format", "text": "Set the prefix (e.g. BATES), starting number, padding digits (e.g. 0001), and position on the page (top/bottom × left/center/right)."},
        {"name": "Download with stamps", "text": "Click Apply. PrivaTools stamps each page with the next Bates number — e.g. BATES0001, BATES0002, etc."},
    ],
    "bmp-to-pdf": [
        {"name": "Upload BMP images", "text": "Drop one or many .bmp files. BMP is the legacy Windows bitmap format — uncompressed and lossless."},
        {"name": "Choose page size", "text": "Letter (8.5 × 11 in) or A4 (210 × 297 mm). Each BMP scales to fit the page while preserving aspect ratio."},
        {"name": "Download the PDF", "text": "Click Convert. All input images are combined into a single PDF, one image per page in upload order."},
    ],
    "booklet-pdf": [
        {"name": "Add the PDF", "text": "Drop or select the document you want to print as a folded booklet, up to 500 MB."},
        {"name": "Create the booklet order", "text": "Run it. The pages are rearranged into saddle-stitch order, and blank pages are added at the end if needed so the total is a multiple of four."},
        {"name": "Print two per sheet, double-sided", "text": "Print the result with two pages per sheet, on both sides, flipping on the short edge. Fold the stack in half and it reads in order."},
    ],
    "compare-pdf": [
        {"name": "Upload two PDFs", "text": "The first is the baseline; the second is the revised version."},
        {"name": "Choose comparison mode", "text": "Text: word-level diff. Visual: side-by-side rendered pages with changes highlighted."},
        {"name": "Download or view the diff", "text": "PrivaTools returns a report PDF with additions in green and deletions in red, plus a summary of changed pages and word counts."},
    ],
    "crop-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Set crop margins", "text": "Specify top / bottom / left / right margins to remove, in PDF points (1 pt = 1/72 inch)."},
        {"name": "Download the cropped PDF", "text": "Click Crop. Each page's MediaBox + CropBox is shrunk by the specified margins."},
    ],
    "delete-annotations": [
        {"name": "Upload the PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Strip annotations", "text": "Click Delete. PrivaTools removes every annotation object (highlights, comments, sticky notes, form fields, links)."},
        {"name": "Download the cleaned PDF", "text": "The visible page content is unchanged; all interactive annotations are gone."},
    ],
    "delete-pages": [
        {"name": "Add the PDF", "text": "Drop or select the PDF you want to trim, up to 500 MB."},
        {"name": "List the pages to remove", "text": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page."},
        {"name": "Delete and download", "text": "Run it and save the new PDF, which contains every page you did not list, in the original order."},
    ],
    "deskew-pdf": [
        {"name": "Upload a scanned PDF", "text": "Drop a scanned PDF up to 500 MB. Works best on documents where text lines are visible."},
        {"name": "PrivaTools detects skew per page", "text": "The algorithm analyses the text line angle on each page and computes the rotation needed to straighten it."},
        {"name": "Download the deskewed PDF", "text": "Each page is rotated by its detected angle (typically -5° to +5°) and the corners are cropped to fit. Result: text rows are perfectly horizontal."},
    ],
    "esign-pdf": [
        {"name": "Add the PDF", "text": "Drop or select the document to sign, up to 500 MB."},
        {"name": "Make your signature", "text": "Draw it, type your name and pick one of the script styles — Classic italic, Flowing script, Formal cursive or Handwritten — or upload an image of your signature."},
        {"name": "Position it", "text": "Choose the page and set the position, width and height so the signature sits on the signing line."},
        {"name": "Sign and download", "text": "Apply it and save the signed PDF, with the signature drawn onto the page."},
    ],
    "excel-to-pdf": [
        {"name": "Upload an .xlsx file", "text": "Drop an Excel workbook up to 500 MB."},
        {"name": "PrivaTools converts each sheet to a PDF page", "text": "Cell values, formulas (as computed), formatting, and column widths are preserved. Each worksheet becomes one or more pages depending on content size."},
        {"name": "Download the PDF", "text": "Click Convert. The output PDF has one section per worksheet."},
    ],
    "extract-images": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "PrivaTools pulls out every image", "text": "Each embedded image (raster or vector) is extracted at its native resolution, with original format preserved (JPEG, PNG, TIFF, etc.)."},
        {"name": "Download as ZIP", "text": "All extracted images are bundled into a ZIP archive, named by page and order."},
    ],
    "extract-pages": [
        {"name": "Add the PDF", "text": "Drop or select the PDF that contains the pages you need, up to 500 MB."},
        {"name": "List the pages to keep", "text": "Pages are written as numbers and ranges separated by commas, such as 1-3, 5, 8-end; an open range like 4- runs to the last page."},
        {"name": "Extract and download", "text": "Run it. The pages you listed are copied into one new PDF; the original is left untouched."},
    ],
    "fill-form": [
        {"name": "Upload a fillable PDF form", "text": "Drop a PDF with AcroForm fields up to 500 MB. The tool detects form fields automatically."},
        {"name": "Fill in the values", "text": "Provide a JSON object mapping field names to values: text strings for text fields, true/false for checkboxes, option labels for radio buttons / dropdowns."},
        {"name": "Download the filled form", "text": "Click Fill. The PDF is returned with values populated. Field structure is preserved so the form can be filled again later."},
    ],
    "gif-to-pdf": [
        {"name": "Upload GIF images", "text": "Drop one or many .gif files. Animated GIFs use only the first frame."},
        {"name": "Choose page size", "text": "Letter or A4. Each GIF scales to fit while preserving aspect ratio."},
        {"name": "Download the PDF", "text": "All GIFs are combined into one PDF, one image per page in upload order."},
    ],
    "grayscale-pdf": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Convert all content to grayscale", "text": "PrivaTools renders each page at the source DPI, converts to single-channel grayscale, and re-embeds. Text, images, and vector content all become greyscale."},
        {"name": "Download the grayscale PDF", "text": "File size typically drops 30–50% because color channels are eliminated."},
    ],
    "header-footer": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Enter header and footer text", "text": "Optional left/center/right slots for both header and footer. Use placeholders like {page}, {total}, {date} for dynamic content."},
        {"name": "Apply and download", "text": "Click Apply. The text is stamped at the top and bottom of every page in the chosen font size."},
    ],
    "heic-to-pdf": [
        {"name": "Upload HEIC images", "text": "Drop one or many .heic / .heif files (e.g. from iPhone photos)."},
        {"name": "Choose page size", "text": "Letter or A4. Each HEIC is decoded via libheif and scaled to fit."},
        {"name": "Download the PDF", "text": "All images become one PDF, one photo per page. EXIF metadata is stripped by default."},
    ],
    "invert-colors": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose DPI for rendering", "text": "Higher DPI gives sharper output but larger file size. 150 DPI is the default; 300 for archival, 96 for web previews."},
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
        {"name": "PrivaTools renders to HTML, then PDF", "text": "Standard Markdown syntax: headings, lists, links, images, code blocks, tables, blockquotes. GitHub-flavored extensions supported."},
        {"name": "Download the styled PDF", "text": "The output has a clean typographic style with proper headings, monospace code, and clickable links."},
    ],
    "metadata": [
        {"name": "Upload the PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "View the metadata", "text": "PrivaTools displays the document's Title, Author, Subject, Keywords, Producer, Creator, Creation Date, Modified Date, and any custom XMP fields."},
        {"name": "Decide what to do next", "text": "If you want to strip the metadata, use Strip Metadata. To set new values, use Update Metadata."},
    ],
    "nup": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose pages-per-sheet", "text": "2, 4, 6, 8, 9, or 16. Each input page is shrunk to fit; output pages are filled left-to-right, top-to-bottom."},
        {"name": "Download the n-up PDF", "text": "Use this to save paper when printing or to create thumbnail-style overviews."},
    ],
    "odt-to-pdf": [
        {"name": "Upload an .odt file", "text": "Drop an OpenDocument Text file (LibreOffice / OpenOffice) up to 500 MB."},
        {"name": "PrivaTools renders via LibreOffice headless", "text": "Fonts, styles, embedded images, tables, footnotes, and bibliography are preserved."},
        {"name": "Download the PDF", "text": "Click Convert. The output PDF matches the on-screen rendering closely."},
    ],
    "organize-pages": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB. A thumbnail of every page is generated so you can see what you are rearranging."},
        {"name": "Reorder the pages", "text": "Drag thumbnails into a new position, or use the move left and move right buttons for precise single steps."},
        {"name": "Remove pages you do not need", "text": "Use the remove button on any thumbnail to leave that page out of the result."},
        {"name": "Save the new PDF", "text": "Apply the changes and download the PDF with the pages in the order you arranged."},
    ],
    "overlay": [
        {"name": "Upload the base PDF", "text": "The PDF that forms the background."},
        {"name": "Upload the overlay PDF", "text": "A PDF whose pages will be layered on top of the base."},
        {"name": "Choose mode and download", "text": "Overlay: foreground on top. Underlay: behind. Stamp: applied to every page repeatedly. Output: a merged PDF with the overlay rendered onto each base page."},
    ],
    "page-numbers": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose position and starting number", "text": "Position: top-left/top-center/top-right/bottom-left/bottom-center/bottom-right. Starting number: defaults to 1, but use any integer to continue a multi-document sequence."},
        {"name": "Apply and download", "text": "PrivaTools stamps each page with its number in the chosen position and font size."},
    ],
    "pdf-to-bmp": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose DPI", "text": "Higher DPI gives sharper output. 150 DPI for screen, 300 for print, 600 for archival."},
        {"name": "Download a ZIP of BMPs", "text": "Each page becomes one BMP file. BMP is uncompressed so files are LARGE — typically 5-30 MB per page at 300 DPI."},
    ],
    "pdf-to-epub": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB. Works best on text-heavy PDFs with a clear structure."},
        {"name": "PrivaTools extracts text and reflows it", "text": "Headings, paragraphs, lists, and embedded images are identified and converted into EPUB chapter structure."},
        {"name": "Download the EPUB", "text": "Open in any e-reader (Kindle, Apple Books, calibre) for a reflowable reading experience."},
    ],
    "pdf-to-gif": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose DPI", "text": "Lower DPI for smaller files; GIF is limited to 256 colors so detail loss is acceptable for previews."},
        {"name": "Download a ZIP of GIFs", "text": "Each page becomes one GIF file. Useful for embedding PDF previews in legacy systems."},
    ],
    "pdf-to-jpg": [
        {"name": "Drop your PDF", "text": "Upload a PDF up to 500 MB. It is processed in isolated temporary per-request storage for the conversion, and response cleanup removes the job's temporary files after your download is sent."},
        {"name": "Choose DPI", "text": "96 DPI for web preview/thumbnails, 150 DPI for general on-screen viewing (default), 300 DPI for printable copies, 600 DPI for archival. Higher DPI means larger files."},
        {"name": "Set JPEG quality", "text": "Quality 70-95 (default 85). Lower values produce smaller files with more visible compression artifacts; higher values are nearly indistinguishable from the source."},
        {"name": "Pick pages (optional)", "text": "Enter ranges like '1-3, 7, 12-15' to convert only specific pages, or leave blank to convert every page."},
        {"name": "Convert and download", "text": "Click Convert. Each page becomes one JPG. Multi-page PDFs return as a ZIP; single-page PDFs return as a single JPG file."},
    ],
    "pdf-to-markdown": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB. Text-heavy PDFs convert best."},
        {"name": "PrivaTools extracts and structures text", "text": "Headings, paragraphs, lists, code blocks, and tables are identified by typographic cues (font size, weight, indentation)."},
        {"name": "Download the .md file", "text": "Open in any Markdown editor for editing or further conversion to HTML / EPUB / DOCX."},
    ],
    "pdf-to-png": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose DPI", "text": "Higher DPI = sharper PNG. 96 for screen, 150 default, 300 for print archival."},
        {"name": "Download a ZIP of PNGs", "text": "Each page becomes one PNG file with lossless compression. PNG preserves transparency if present."},
    ],
    "pdf-to-pptx": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "PrivaTools creates one slide per page", "text": "Each page is rendered to an image and placed as the slide background. Text is also extracted as separate slide text boxes for editability."},
        {"name": "Download the .pptx file", "text": "Open in PowerPoint / Keynote / Google Slides for further editing."},
    ],
    "pdf-to-tiff": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose DPI", "text": "Higher DPI = sharper TIFF. 300 DPI is standard for archival; 600 for high-resolution professional output."},
        {"name": "Download the TIFF", "text": "PrivaTools produces a single multi-page TIFF (one image per PDF page) or a ZIP of individual TIFFs."},
    ],
    "pdfa-validator": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB to check whether it conforms to PDF/A archive standards."},
        {"name": "PrivaTools runs a conformance check", "text": "Tests against PDF/A-1, PDF/A-2, and PDF/A-3 requirements: embedded fonts, color profiles, no JavaScript, no encryption, no external references."},
        {"name": "Read the validation report", "text": "Either 'compliant' with the highest PDF/A level achieved, or a list of specific violations preventing compliance."},
    ],
    "png-to-pdf": [
        {"name": "Upload PNG images", "text": "Drop one or many .png files up to 500 MB total."},
        {"name": "Choose page size", "text": "Letter or A4. Transparency in PNGs renders against a white page background."},
        {"name": "Download the PDF", "text": "All images become a single PDF, one per page. Lossless — PNG pixels map directly to PDF image objects."},
    ],
    "pptx-to-pdf-convert": [
        {"name": "Upload a .pptx file", "text": "Drop a PowerPoint presentation up to 500 MB."},
        {"name": "Each slide becomes one PDF page", "text": "PrivaTools renders fonts, animations (first state), embedded images, and SmartArt diagrams."},
        {"name": "Download the PDF", "text": "The output preserves slide aspect ratio (16:9 or 4:3 as designed)."},
    ],
    "qr-code": [
        {"name": "Enter the data to encode", "text": "URL, contact card (vCard), wifi credentials, plain text, or any string up to ~2,500 characters."},
        {"name": "Choose size and format", "text": "Pixel dimensions of the output QR. Format: PNG (raster) or SVG (vector, scales infinitely)."},
        {"name": "Download the QR", "text": "PrivaTools generates a QR code with error correction level L (default; supports up to 7% damage)."},
    ],
    "remove-blank-pages": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB. Scanned documents from a duplex scanner, which often contain empty reverse sides, are the typical case."},
        {"name": "Set the sensitivity", "text": "The slider runs from 50 to 100 and starts at 85. Higher values only remove pages that are almost perfectly white; lower values also remove scanned blank pages that carry specks, show-through or scanner noise."},
        {"name": "Remove and download", "text": "Run it and check the result. Every page judged blank is dropped and the rest keep their order."},
    ],
    "repair-pdf": [
        {"name": "Upload the corrupt PDF", "text": "Drop a PDF up to 500 MB that won't open or shows errors in your viewer."},
        {"name": "PrivaTools rebuilds the file structure", "text": "Uses pikepdf to parse the PDF tolerantly, recover damaged cross-reference tables, and rewrite the file with a clean structure."},
        {"name": "Download the repaired PDF", "text": "Most viewer-breaking issues (broken xref, missing trailer, corrupted streams) are fixable."},
    ],
    "resize-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Choose target page size", "text": "A4, Letter, Legal, Tabloid, or custom dimensions in millimeters/inches."},
        {"name": "Download the resized PDF", "text": "PrivaTools scales each page's MediaBox to the target. Content is preserved at relative position; aspect ratio is maintained."},
    ],
    "reverse-pdf": [
        {"name": "Add the PDF", "text": "Drop or select a PDF up to 500 MB."},
        {"name": "Reverse the order", "text": "Run it. There are no options: the last page becomes the first and the first becomes the last."},
        {"name": "Download the result", "text": "Save the reversed PDF. The pages themselves are copied unchanged."},
    ],
    "rtf-to-pdf": [
        {"name": "Upload an .rtf file", "text": "Drop a Rich Text Format file (Word, WordPad, TextEdit, Pages all save in RTF)."},
        {"name": "PrivaTools renders to PDF", "text": "Bold, italic, underline, paragraph styles, lists, tables, and embedded images transfer faithfully."},
        {"name": "Download the PDF", "text": "Click Convert. Open in any PDF viewer."},
    ],
    "sanitize-pdf": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB containing potentially risky elements."},
        {"name": "PrivaTools removes risky content", "text": "Strips embedded JavaScript, executable links to external apps, embedded files marked for auto-launch, and hidden 'flash' (deprecated SWF) content."},
        {"name": "Download the sanitized PDF", "text": "Visible content is preserved; security-risky elements are gone."},
    ],
    "set-permissions": [
        {"name": "Upload a PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Set an owner password and permissions", "text": "Choose which operations are allowed for users without the owner password: print, copy text, modify, annotate."},
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
        {"name": "Set opacity and position", "text": "Opacity 0-1 (default 0.5). Position: top/middle/bottom × left/center/right. Click Apply."},
    ],
    "strip-metadata": [
        {"name": "Upload PDF(s)", "text": "Drop one or many PDFs up to 500 MB each. Multi-file batches are supported."},
        {"name": "PrivaTools removes all metadata", "text": "Title, Author, Subject, Keywords, Producer, Creator, Creation Date, Modified Date, all XMP fields, and any custom-defined metadata."},
        {"name": "Download the clean PDF (or ZIP)", "text": "Single file → single PDF; multiple files → ZIP. Visible content is unchanged."},
    ],
    "svg-to-pdf": [
        {"name": "Upload SVG images", "text": "Drop one or many .svg files. Vector content scales infinitely."},
        {"name": "Choose page size", "text": "Letter or A4. Each SVG scales proportionally to fit while preserving aspect ratio."},
        {"name": "Download the PDF", "text": "All SVGs become one PDF, one per page. Vector content stays vector — no rasterization."},
    ],
    "tiff-to-pdf": [
        {"name": "Upload TIFF images", "text": "Drop .tif / .tiff files. Multi-page TIFFs are supported and each page becomes a PDF page."},
        {"name": "Choose page size", "text": "Letter or A4. Single-page TIFFs scale; multi-page TIFFs preserve their per-page sizes."},
        {"name": "Download the PDF", "text": "All TIFFs become one PDF. Compression (LZW, Deflate, JPEG inside TIFF) is converted to PDF-native equivalents."},
    ],
    "transparent-background": [
        {"name": "Upload a PDF (or image)", "text": "Drop a PDF up to 500 MB. PrivaTools renders each page and detects the background color."},
        {"name": "Set threshold", "text": "How close to pure white (or off-white) should be treated as background. 240 (default) catches most scanned documents."},
        {"name": "Download with transparency", "text": "The output has white/off-white pixels converted to alpha=0. Useful for overlaying scans on dark backgrounds."},
    ],
    "verify-signature": [
        {"name": "Upload a signed PDF", "text": "Drop a PDF with one or more digital signatures."},
        {"name": "PrivaTools verifies each signature", "text": "Checks that the signed content hasn't been modified since signing, the certificate chain is intact, and the signing date is consistent."},
        {"name": "Read the report", "text": "For each signature: signer name, signing time, certificate authority, validity status (valid / modified / expired / untrusted CA)."},
    ],
    "webp-to-pdf": [
        {"name": "Upload WebP images", "text": "Drop one or many .webp files up to 500 MB total."},
        {"name": "Choose page size", "text": "Letter or A4. Transparency in WebP is rendered against a white page background."},
        {"name": "Download the PDF", "text": "All images become one PDF in upload order. WebP's smaller size is reflected in a smaller PDF."},
    ],
    "whiteout-pdf": [
        {"name": "Upload your PDF", "text": "Drop a PDF up to 500 MB."},
        {"name": "Draw white-out rectangles", "text": "Specify region(s) per page to cover with white (or chosen color). Content underneath is permanently hidden from view."},
        {"name": "Download the cleaned PDF", "text": "Hidden regions are covered with the chosen color in the rendered output."},
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
        {"name": "Upload files", "text": "Drop multiple files of any type, up to 500 MB per file."},
        {"name": "Choose compression level", "text": "Use Store for speed, Balanced for everyday ZIPs, or Maximum for the smallest output."},
        {"name": "Download the ZIP", "text": "All files are bundled into a single .zip with their original filenames and extensions."},
    ],
    "csv-json": [
        {"name": "Paste your CSV or JSON", "text": "Or upload a file. Auto-detects the format."},
        {"name": "Click Convert", "text": "CSV → JSON: each row becomes an object using the first row as keys. JSON → CSV: array of objects → rows; keys → header."},
        {"name": "Copy or download the result", "text": "Runs entirely in your browser. Your data never leaves your device."},
    ],
    "extract-archive": [
        {"name": "Upload an archive", "text": "Drop a .zip, .tar, .tar.gz, .tar.bz2, or .tar.xz archive up to 500 MB."},
        {"name": "PrivaTools extracts and returns each file", "text": "All files inside are extracted and bundled into a folder-style download."},
        {"name": "Download the extracted folder as a ZIP", "text": "Or download individual files from the result preview."},
    ],
    "extract-audio": [
        {"name": "Upload a video file", "text": "Drop an MP4/MOV/MKV/WebM file up to 200 MB."},
        {"name": "Choose output format", "text": "MP3 (universal), WAV (uncompressed), OGG (open), FLAC (lossless), AAC (high quality)."},
        {"name": "Download the audio track", "text": "FFmpeg extracts the audio stream and re-encodes it to the chosen format, even when the video already carries that format."},
    ],
    "generate-barcode": [
        {"name": "Enter the data to encode", "text": "The string or number you want to encode. Format limits vary (e.g. EAN-13 needs exactly 12-13 digits)."},
        {"name": "Choose barcode type", "text": "Code 128 (most flexible), Code 39, EAN-13 (retail), UPC-A (US retail), QR code (also available via the QR tool)."},
        {"name": "Download as PNG", "text": "Configurable size; ready for printing on labels or embedding in documents."},
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
        {"name": "Paste Markdown or HTML", "text": "Auto-detects direction. Markdown → HTML for publishing; HTML → Markdown for content extraction."},
        {"name": "Click Convert", "text": "Standard CommonMark spec for Markdown. HTML converts to GitHub-flavored Markdown."},
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
        {"name": "Choose the scale", "text": "Set how large to render, from 0.1 up to 8 times the SVG's own dimensions; the default is 2 for a crisp result on high-resolution screens."},
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
        {"name": 'Convert and download', "text": 'Run the conversion. Matroska can hold multiple audio and subtitle tracks, though this conversion keeps one video and one audio track.'},
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
        {"name": 'Download the stitched image', "text": 'Pages are rendered at 100 DPI and joined top to bottom on a white canvas. Pages narrower than the widest one are centred, so a mixed-size document stays aligned.'},
    ],
    "bates-remove": [
        {"name": 'Upload the stamped PDF', "text": 'Select a PDF that carries Bates numbering applied by PrivaTools or another tool.'},
        {"name": 'Describe the stamp', "text": 'Give the prefix, digit count and any suffix used when the numbers were applied, so the tool matches those stamps and leaves real page content alone.'},
        {"name": "Download the clean PDF", "text": "The matching stamps are removed and the rest of the page is untouched. You download a new PDF; the original on your device is not changed."},
    ],
    "accessibility-check": [
        {"name": 'Upload the PDF', "text": 'Select the PDF you need to audit. Tagged, untagged, scanned and born-digital files are all accepted.'},
        {"name": 'Run the audit', "text": 'The document is checked against PDF/UA and WCAG expectations: tag structure, document language, title metadata, and alternative text on images.'},
        {"name": 'Read the report', "text": 'Each finding names the requirement it relates to, so you can fix the document at source. The report is advice, not a legal certification.'},
    ],
    "remove-watermark": [
        {"name": 'Upload the watermarked PDF', "text": 'Select a PDF that carries a visible watermark.'},
        {"name": 'Review the candidates', "text": 'The tool scans the page content for repeated text and image objects that behave like watermarks, and lists what it found.'},
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
        {"name": "Save the result", "text": "Download the translation as a .txt file, which stays on your device. 'Save as PDF' is optional and sends the translated text, not your original PDF, to the PrivaTools server to be typeset."},
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
        {"q": "Can I compress many PDFs at once?", "a": "Yes, up to 100 files in one request, each up to 500 MB. Compression is one of the heavier jobs, so fair-use rate limits apply and very large batches are best split into smaller runs."},
        {"q": "The result is still too big. What next?", "a": "Try Extreme, or Custom with a lower quality and a smaller maximum image dimension. If it still will not fit, Split by Size divides the document into parts under a size you choose."},
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
        {"q": "What encryption does PrivaTools use?", "a": "PDFs are encrypted with AES-256 (the same standard used by banks and governments) by default. AES-128 is available for backward compatibility with older PDF readers, though AES-256 is supported by every reader from the last decade. RC4 is explicitly NOT offered — it's been broken since the 2000s."},
        {"q": "Can I allow printing but block copying text?", "a": "Yes. You can set granular permissions independently: allow or deny printing (with optional 'low-resolution print only'), text copying, form filling, content modification, page extraction, and accessibility/screen-reader access."},
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
        {"q": "Can I rotate individual pages instead of the entire PDF?", "a": "Yes. Click individual page thumbnails to select specific pages, then apply the rotation angle only to those pages. Mix-and-match is supported: rotate page 3 by 90°, page 7 by 180°, leave the rest untouched."},
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
        {"q": "What languages does the OCR support?", "a": "PrivaTools ships Tesseract's full language pack: 100+ languages including English, Spanish, French, German, Italian, Portuguese, Chinese (Simplified and Traditional), Japanese, Korean, Arabic, Hindi, Russian, Hebrew, Thai, and Vietnamese. Pick the language explicitly for best accuracy; auto-detect works but adds a few seconds."},
        {"q": "Will OCR change how my scanned PDF looks?", "a": "No — the visual page stays pixel-identical to the input. OCR adds an invisible text layer behind the scan so the PDF becomes searchable and copy-pasteable, but the human-readable appearance is unchanged."},
        {"q": "How accurate is the OCR?", "a": "Clean 300 DPI scans typically reach 95–99% accuracy on Latin scripts. Lower resolutions or skewed pages drop to 85–95%. For best results, run Deskew PDF before OCR if pages are tilted, and crank up the scanner DPI if you control the scan."},
        {"q": "Can I get the extracted text as a separate file?", "a": "Yes. The default output is a searchable PDF, but you can also download just the extracted text as .txt (per page or combined) or as structured JSON with per-page text and bounding boxes."},
        {"q": "Where is my document processed?", "a": "That depends on the engine you pick. 'On our server' (the default) uploads the PDF over HTTPS and runs Tesseract in isolated temporary per-request storage; response cleanup removes the job's temporary files after the result is sent, and a background sweep clears anything left behind by an interrupted request. 'In this browser' runs OCR on your device after a one-time engine download, and with your own AI key the page images go from your browser straight to that provider."},
        {"q": "Can I OCR a scanned PDF in a language I don't have the keyboard for?", "a": "Yes. OCR needs the right language to be available to the engine, not a keyboard. Once the text is recognised you can copy it, or use Translate PDF to translate the searchable result."},
    ],
    "redact-pdf": [
        {"q": "Is redaction permanent and truly irreversible?", "a": "Yes. The underlying text glyphs and image pixels under each redaction rectangle are destroyed before the new PDF is written. The original bytes are not preserved in the file. No forensic tool can recover them — there is nothing left to recover."},
        {"q": "Can I search and redact every occurrence of a name or number?", "a": "Yes. Use the search-and-redact mode to type a phrase (case-sensitive optional) and the tool marks every occurrence across the whole document. Review the matches, then apply the redactions in one batch."},
        {"q": "What's the difference between redacting and drawing a black box?", "a": "Drawing a black annotation rectangle, as a comment or markup tool does, covers the text visually but leaves it in the file underneath — anyone can move or delete the annotation and recover the secret. True redaction removes the text and image data and rewrites the file. PrivaTools uses true redaction, not annotation."},
        {"q": "Will the redacted PDF still be searchable for non-redacted text?", "a": "Yes. Only the content under the redaction rectangles is destroyed. Text outside the rectangles, along with bookmarks, hyperlinks, and the text-search layer, are preserved intact."},
        {"q": "Is metadata also redacted?", "a": "By default the rectangles destroy on-page text and images. Author name, title, software, and other XMP/Info metadata are NOT automatically stripped — use the Strip Metadata tool afterward (or use Smart Redact which redacts both). For maximum safety: redact, then strip metadata, then sanitize."},
        {"q": "What happens to the original, unredacted PDF I upload?", "a": "It is uploaded over HTTPS and held in isolated temporary per-request storage while the redactions are applied. Response cleanup removes both the original and the redacted output after the result is sent, and a background sweep clears anything left behind by an interrupted request. The redaction code is open source under the MIT licence, so it can be reviewed, or self-hosted if the original must not leave your network."},
    ],
    "flatten-pdf": [
        {"q": "What does flattening a PDF mean?", "a": "Flattening converts interactive elements like form fields, annotations, and layers into static page content. The visual appearance stays the same but the elements can no longer be edited."},
        {"q": "When should I flatten a PDF?", "a": "Flatten before sharing filled forms (to prevent edits), before printing (to avoid rendering issues), or when a recipient's PDF viewer does not display annotations correctly."},
        {"q": "Does flattening reduce file size?", "a": "Sometimes. Removing form field metadata and annotation data can slightly reduce file size, but the effect depends on the document."},
    ],
    "bookmarks": [
        {"q": "Can I create a multi-level bookmark tree?", "a": "Yes. You can nest bookmarks under parent entries to create a hierarchical table of contents with multiple levels."},
        {"q": "Do bookmarks work in all PDF readers?", "a": "Yes. The bookmarks use the standard PDF outline format supported by Adobe Reader, Preview, Chrome, Firefox, and all major PDF viewers."},
        {"q": "Can I import a bookmark structure from a text file?", "a": "Currently, bookmarks are created manually in the editor. You can copy-paste titles and set page numbers individually."},
    ],
    "form-creator": [
        {"q": "What field types can I add?", "a": "Text inputs, text areas, checkboxes, radio buttons, dropdowns, date pickers, and signature fields."},
        {"q": "Will the form work in Adobe Reader?", "a": "Yes. The forms use the standard AcroForm format, which is compatible with Adobe Reader, Foxit, and all major PDF viewers."},
        {"q": "Can I set fields as required?", "a": "Yes. Mark any field as required to prevent submission without filling it in. You can also set validation rules like numeric-only or email format."},
    ],
    "extract-tables": [
        {"q": "What output formats are supported?", "a": "CSV, Excel (.xlsx), and JSON. Each table is extracted separately and all results are packaged in a ZIP file."},
        {"q": "Can it extract tables from scanned PDFs?", "a": "For best results, run OCR first using the OCR tool to create a text layer, then use table extraction. The tool works best with text-based PDFs."},
        {"q": "How does the tool detect table boundaries?", "a": "It uses Camelot and Tabula libraries, which detect ruled lines and text alignment patterns to identify table structures. Tables without visible borders may need manual page selection."},
    ],
    "pdf-to-pdfa": [
        {"q": "What is PDF/A and why would I need it?", "a": "PDF/A is an ISO-standardized archival format that ensures documents remain viewable long-term. Government agencies, courts, and archives often require PDF/A submissions."},
        {"q": "What changes does the conversion make?", "a": "The tool embeds all fonts, converts color spaces to sRGB, removes JavaScript and multimedia, and adds the required PDF/A metadata."},
        {"q": "Will the document look different after conversion?", "a": "Visually the document should look the same. Transparency may be flattened in PDF/A-1b, and embedded multimedia will be removed since PDF/A does not allow it."},
    ],
    "image-to-pdf": [
        {"q": "What image formats are supported?", "a": "JPG, PNG, WebP, BMP, and TIFF. Each image can be up to 500 MB."},
        {"q": "Can I control the page size?", "a": "Yes. Choose A4, Letter, or fit-to-image (where the page matches the image dimensions exactly). You can also set landscape or portrait orientation."},
        {"q": "Are multiple images combined into one PDF?", "a": "Yes. All uploaded images become pages in a single PDF. Drag to reorder them before converting."},
    ],
    "txt-to-pdf": [
        {"q": "Can I change the font and page size?", "a": "Yes. Choose from several font families (serif, sans-serif, monospace), set the font size, and select A4 or Letter page size with custom margins."},
        {"q": "Does the tool handle Unicode text?", "a": "Yes. UTF-8 encoded text is fully supported, including non-Latin scripts like Chinese, Arabic, Cyrillic, and Devanagari."},
        {"q": "Is there a character or line limit?", "a": "No character limit beyond the 500 MB file-size cap. The text is automatically reflowed and paginated."},
    ],
    "office-to-pdf": [
        {"q": "Which Office formats are supported?", "a": "Word (.doc, .docx), Excel (.xls, .xlsx), PowerPoint (.ppt, .pptx), and OpenDocument formats (.odt, .ods, .odp)."},
        {"q": "Are charts and images preserved?", "a": "Yes. The conversion uses LibreOffice, which preserves charts, images, tables, headers, footers, and most formatting accurately."},
        {"q": "How long does conversion take?", "a": "Most documents convert in 2-10 seconds. Large files with many images or complex layouts may take up to 30 seconds."},
    ],
    "word-to-pdf": [
        {"q": "Will the PDF look exactly like my Word document?", "a": "Usually very close. The layout is recalculated by LibreOffice rather than Microsoft Word, so complex documents can differ in small ways, most often in line breaks and page breaks."},
        {"q": "Why do the fonts look different?", "a": "If the document uses a font the server does not have, a similar one is substituted, which can change spacing and page breaks. Embedding fonts when saving in Word, or using common fonts, gives the most faithful result."},
        {"q": "Which file types can I convert?", "a": "This page takes .docx. For .doc, .odt, .rtf, spreadsheets or presentations, use Office to PDF, which accepts a wider set of formats."},
        {"q": "Are comments and tracked changes included?", "a": "Accept or reject tracked changes and remove comments before converting if you do not want them to appear. Converting exactly the version you intend to share avoids surprises."},
        {"q": "Do links and headings carry over?", "a": "Clickable links generally survive the export. Check the result if a table of contents or internal cross-references matter to you."},
        {"q": "What happens to my document after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the document and the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "epub-to-pdf": [
        {"q": "Are images and formatting preserved?", "a": "Yes. Chapter headings, bold/italic text, embedded images, and basic CSS styling are preserved in the PDF output."},
        {"q": "Can I convert DRM-protected EPUBs?", "a": "No. DRM-protected e-books cannot be converted. The tool only works with DRM-free EPUB files."},
        {"q": "What page size options are available?", "a": "A4, Letter, and custom dimensions. The text is reflowed to fit the chosen page size while keeping chapter breaks."},
    ],
    "html-to-pdf": [
        {"q": "Can I convert a live website URL to PDF?", "a": "Yes. Enter any public URL and the server will render the page — including CSS, images, and JavaScript — and convert it to PDF."},
        {"q": "Is JavaScript rendered?", "a": "Yes. A headless browser executes JavaScript before capturing the page, so dynamically loaded content appears in the PDF."},
        {"q": "Are external stylesheets and images included?", "a": "Yes. The renderer fetches external CSS, web fonts, and images. Only resources behind authentication may not load."},
    ],
    "xml-to-pdf": [
        {"q": "What XML schemas are supported?", "a": "Any well-formed XML file is supported. The tool renders the structure as a readable tree or table — it does not apply XSL transforms."},
        {"q": "Is syntax highlighting included?", "a": "Yes. Element names, attributes, and values are color-coded for readability in the PDF output."},
        {"q": "Can I convert large XML files?", "a": "Files up to 500 MB are supported. Very deeply nested structures may produce many pages."},
    ],
    "csv-to-pdf": [
        {"q": "Does the tool auto-detect delimiters?", "a": "Yes. Comma, semicolon, tab, and pipe delimiters are automatically detected. You can also specify the delimiter manually."},
        {"q": "How are wide tables handled?", "a": "Wide tables can be rendered in landscape orientation. If they still exceed the page width, columns are scaled to fit or split across pages."},
        {"q": "Is the first row treated as a header?", "a": "By default yes — the first row is bolded as a header. You can disable this if your data has no header row."},
    ],
    "json-to-pdf": [
        {"q": "Is JSON validated before conversion?", "a": "Yes. The tool validates the JSON and shows a clear error message with the line number if the syntax is invalid."},
        {"q": "How are nested objects displayed?", "a": "Nested objects and arrays are indented with syntax highlighting. Collapsible sections are shown in the preview but expanded in the PDF."},
        {"q": "Can I convert JSON arrays into tables?", "a": "Yes. Arrays of objects with consistent keys are rendered as a table, with keys as column headers and each object as a row."},
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
        {"q": "Does it convert the entire PDF or just tables?", "a": "The tool focuses on extracting tabular data. Each detected table becomes a separate sheet in the Excel file. Non-table text (paragraphs, headers, footers) is not included — use PDF to Word or PDF to Text for that."},
        {"q": "Can I choose which tables to extract?", "a": "Yes. Select specific pages, or let the tool auto-detect all tables across the document. Auto-detect uses Camelot and Tabula libraries which identify ruled lines and text-alignment patterns."},
        {"q": "What if my PDF has no visible table borders?", "a": "The tool can detect tables based on text alignment even without ruled borders, but results are more reliable on clearly bordered tables. For borderless tables with very irregular spacing, manual page selection plus column-position hints in the advanced settings give better accuracy."},
        {"q": "What happens to a confidential financial PDF after I upload it?", "a": "The PDF is uploaded over HTTPS and converted in isolated temporary per-request storage on the PrivaTools server, using local libraries rather than a third-party API. Response cleanup removes the PDF and the generated .xlsx after the result is sent, and a background sweep clears anything left behind by an interrupted request."},
        {"q": "What's the file size limit?", "a": "Up to 500 MB per file on the hosted site. Table extraction is one of the heavier jobs, so fair-use rate limits apply and a very long PDF can hit the request timeout; splitting the document first avoids that."},
        {"q": "Does it work on scanned PDFs?", "a": "Scanned PDFs need OCR first. Run the OCR PDF tool (you can pick the language and deskew the pages), then convert the OCR'd PDF to Excel. The text layer added by OCR is what the table detector reads."},
        {"q": "Can I batch-convert multiple PDFs to Excel?", "a": "Yes — upload multiple PDFs and each is converted independently, then bundled into a ZIP of .xlsx files. Useful for processing a folder of monthly statements or invoices."},
        {"q": "Which tables convert most reliably?", "a": "Tables with clear ruled lines and one value per cell. Merged cells, tables that break across pages and borderless layouts with irregular spacing are the hardest cases and usually need tidying in the spreadsheet afterwards."},
    ],
    "pdf-to-text": [
        {"q": "Is formatting preserved in the text output?", "a": "The tool extracts raw text only. Bold, italic, font sizes, and layout are not preserved — you get clean plain text."},
        {"q": "Can I extract text from a specific page range?", "a": "Yes. Specify page numbers or ranges to extract text from only the pages you need."},
        {"q": "How does it handle multi-column layouts?", "a": "The tool reads text in natural reading order. Two-column layouts are generally handled correctly, but complex magazine-style layouts may interleave columns."},
    ],
    "pdf-to-image": [
        {"q": "What DPI should I use?", "a": "150 DPI is good for on-screen viewing. Use 300 DPI for printing. Higher values like 600 DPI produce large files but maximum detail."},
        {"q": "Which image formats are available?", "a": "PNG (lossless, best for text-heavy pages), JPG (smaller files, good for photos), and WebP (modern format with excellent compression)."},
        {"q": "Can I convert just specific pages?", "a": "Yes. Enter individual page numbers or ranges (e.g. 1-3, 7) to convert only the pages you need."},
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
        {"q": "How precise is the trimming?", "a": "Video cuts are frame-accurate, because the video is re-encoded. Audio is copied, so an audio cut lands on the nearest compressed-audio frame, within a few hundredths of a second."},
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
        {"q": "What happens to my file after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the audio file and the result and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],

    # ── v1.1.0 + v1.2.0 additions ─────────────────────────────────────────
    "highlight-pdf": [
        {"q": "Are the highlights real PDF annotations or flattened images?", "a": "Real PDF annotations. They render in every PDF viewer and can be removed later if you reopen the file in an editor. Nothing about the underlying text is changed."},
        {"q": "Can I highlight multiple phrases at once?", "a": "Run the tool once per phrase. Each run preserves previous highlights, so you can layer different colors for different keywords."},
        {"q": "Does the highlighter respect case?", "a": "Toggle case-sensitive matching for exact-case search; leave it off for case-insensitive flexible matching. Case-insensitive is the default."},
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
        {"q": "Is there a file size or page limit?", "a": "Nothing is uploaded, so the server's 500 MB cap does not apply; the practical limit is your browser's memory and your patience. Very long PDFs are slow on the on-device engine because every chunk is summarized in turn."},
        {"q": "Why does my scanned PDF produce no summary?", "a": "A scan is a set of page images with no text layer, so there is nothing for the tool to read. Run OCR PDF first to add real text, then summarize the result."},
    ],
    "smart-redact": [
        {"q": "What does it detect?", "a": "Pattern matching finds email addresses, phone numbers, SSN-style numbers (3-2-4 digits), runs of 13 to 19 digits that look like card numbers, and numeric dates. The entity model adds people, organisations, locations and other named entities. It does not look for postal addresses, IP addresses or custom identifiers, so check the document for those yourself."},
        {"q": "Which parts run in my browser and which on the server?", "a": "Text extraction, pattern matching and the default entity model all run in your browser, so nothing is uploaded while you scan and review. When you apply, the PDF and the strings you approved are sent over HTTPS to the PrivaTools server, which writes the redactions in isolated temporary per-request storage; response cleanup removes the job's temporary files after the result is sent."},
        {"q": "What is sent if I use my own AI key?", "a": "The extracted text of the PDF goes from your browser directly to the provider you chose, using your key, so that provider's terms apply. Values the pattern pass already found, such as emails, phone numbers, SSNs and card numbers, are masked before the text is sent. Applying the redactions still happens on the PrivaTools server."},
        {"q": "Is the redaction reversible?", "a": "No. The server applies PyMuPDF redactions, which remove the matched text from the page content instead of drawing a box over it, and the file is rewritten without the removed objects. Document metadata is separate: run Strip Metadata afterwards if the author or title fields are sensitive."},
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
        {"q": "How many SVG files come back?", "a": "One per page, packaged into a ZIP."},
        {"q": "Can I edit the SVGs after?", "a": "Yes. Open in any vector editor (Illustrator, Inkscape, Figma). Text and paths are editable."},
    ],
    "pdf-to-html": [
        {"q": "How accurate is the conversion?", "a": "PyMuPDF preserves text positioning and fonts via inline styles. Layout is faithful for simple documents; complex multi-column or floating-element layouts may need manual cleanup."},
        {"q": "Are images included?", "a": "Yes. Embedded images come through as base64-encoded inline data URLs, so the HTML is fully self-contained — no external image files needed."},
        {"q": "Why convert PDF to HTML?", "a": "Web archiving, accessibility (screen readers handle HTML better than complex PDFs), republishing offline documents online, or any use where you need the content as a web page."},
    ],
    "pdf-to-rtf": [
        {"q": "What's RTF good for?", "a": "Rich Text Format opens in every word processor (Word, Pages, LibreOffice, WordPad) without the bloat of .docx and with better text fidelity than .txt. Useful for legacy or cross-platform document exchange."},
        {"q": "Are images preserved?", "a": "No. The current implementation focuses on text and structure. For full visual fidelity, use PDF to Word instead."},
        {"q": "Does it handle Unicode?", "a": "Yes. Non-ASCII characters are encoded via the standard RTF \\uN escape mechanism."},
    ],
    "web-optimize-pdf": [
        {"q": "What does linearization actually do?", "a": "It reorganizes the PDF byte layout so the first page's objects come first in the file. A byte-range-aware viewer can then start rendering the first page while the rest still downloads."},
        {"q": "Does it change file size?", "a": "Usually slightly smaller, sometimes slightly larger — the rearrangement adds a small overhead but qpdf also re-streams and recompresses where it can."},
        {"q": "Do I need this for a PDF served from my own server?", "a": "Only if you're serving large PDFs and want the inline-viewer experience to feel fast. For small (<2 MB) PDFs the difference is invisible."},
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
        {"q": "What happens to my photo after I upload it?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server using local imaging libraries, not a third-party conversion service. The file sits in isolated temporary per-request storage while it is read; response cleanup removes the input and the output once your download has been sent, and a background sweep clears anything an interrupted request leaves behind."},
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
        {"q": "How many PDFs can I upload?", "a": "Up to 50 files per batch, up to 500 MB per file."},
        {"q": "Are they compressed in parallel?", "a": "Yes — the backend runs 4 worker processes simultaneously, so 4 files compress at once. Total time scales nearly linearly with file count divided by 4."},
        {"q": "What's the difference between Light, Recommended, and Extreme?", "a": "Light shrinks structure only (5–30% reduction, no visible quality loss). Recommended (default) resamples images at 150 DPI (40–70% reduction). Extreme drops to 96 DPI and lower JPEG quality (60–90% reduction)."},
    ],
    "pdf-page-counter": [
        {"q": "How is this faster than opening each PDF?", "a": "The tool reads only the PDF's page metadata, not the page content. For 100 PDFs the total scan time is typically under a second."},
        {"q": "Does it work on encrypted PDFs?", "a": "Yes for most. Password-protected PDFs that block metadata access return as invalid."},
        {"q": "Useful for print pricing?", "a": "Yes — print shops use this exact tool to count total pages across multi-file print jobs for instant quotes."},
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
        {"q": "What rules does it follow?", "a": "Patch increments the third number, minor increments the second and resets patch, major increments the first and resets minor and patch."},
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
    ],
    "flip-image": [
        {"q": "Horizontal vs vertical — when do I use which?", "a": "Horizontal flip mirrors left↔right — the most common use is fixing selfies that come out mirrored. Vertical flip mirrors top↔bottom, like a reflection in water, which suits design layouts. It is not the same as turning a picture upside down: for an upside-down scan, use Rotate Image at 180°."},
        {"q": "Does flipping change the file size?", "a": "It can. Flipping is a pure pixel rearrangement, and a PNG comes out close to its original size. JPG and WEBP files are re-encoded at quality 92, so a photo that was saved at a lower quality can grow noticeably."},
        {"q": "Is metadata preserved?", "a": "No. The flipped copy is saved without the original EXIF data, such as camera details and location. A camera orientation tag is not applied first, so a phone photo that relies on one can come out turned on its side; Rotate Image can put it upright."},
    ],

    # ── Auto-generated content for v1.3.1 SEO coverage push ──────────────
    "add-attachment": [
        {"q": "What's the difference between an attachment and embedding?", "a": "An attachment is a file stored inside the PDF that the reader can open separately. Embedding means inlining content (images, fonts) into the page itself. Use attachments when you want recipients to access the supporting file but keep the visible PDF clean."},
        {"q": "Will email clients flag attached PDFs as suspicious?", "a": "No, attachments inside a PDF aren't visible to email gateway scanners as separate attachments — the file is part of the PDF structure. Most spam filters don't flag them."},
        {"q": "How big can the embedded file be?", "a": "Up to the 500 MB total file limit. The PDF size grows by approximately the embedded file's size."},
    ],
    "add-hyperlinks": [
        {"q": "Can I link to other pages in the same PDF?", "a": "Currently the tool supports external URLs. For internal page jumps, use the Bookmarks tool instead."},
        {"q": "Are the links visible to the user?", "a": "The clickable rectangle is invisible by default. To add visible underlined link text, use the Edit PDF tool to draw the underline first."},
        {"q": "Will hyperlinks survive printing or PDF/A conversion?", "a": "Hyperlinks don't print (they're interactive annotations) but they're preserved through most PDF/A conversions. PDF/A-1a strips them; PDF/A-2 keeps them."},
    ],
    "add-shapes": [
        {"q": "Are shapes flattened into the page?", "a": "Yes — shapes become part of the page's content stream, not annotations. They can't be moved or deleted afterwards without re-editing the PDF."},
        {"q": "Can I draw filled or only outlined shapes?", "a": "Both. Set fillColor for a filled shape; omit it and only the stroke renders. Set both for an outlined fill."},
        {"q": "What about transparency?", "a": "Use a color with alpha (e.g., rgba(255,0,0,0.5)) or pass an opacity value (0–1)."},
    ],
    "alternate-mix": [
        {"q": "When would I use this?", "a": "The classic case is double-sided scanning on a single-sided scanner: scan the odd pages, flip the stack, scan the even pages in reverse, then alternate-mix them with reverse-alternate."},
        {"q": "What if the PDFs have different page counts?", "a": "PrivaTools alternates pages until one source is exhausted, then appends the remaining pages from the longer source at the end."},
        {"q": "Does this preserve bookmarks?", "a": "No. Bookmarks from the originals are dropped because they would point to incorrect pages after interleaving."},
    ],
    "annotate-pdf": [
        {"q": "Are annotations flattened?", "a": "By default no — they remain as editable annotations. If you want them permanently baked into the page, run the Flatten tool afterwards."},
        {"q": "Can I attach sticky-note comments?", "a": "Yes. Add a note annotation with author + content; readers display it as an icon that opens a popup with the text on click."},
        {"q": "Do annotations survive PDF/A conversion?", "a": "Some do (text, highlight, square) but interactive ones (file attachments, popup notes) get flattened or stripped depending on the PDF/A profile."},
    ],
    "auto-crop": [
        {"q": "Will this make text run off the page?", "a": "No — the algorithm leaves a small safety margin around detected content. If a page has no content (blank), the original MediaBox is kept."},
        {"q": "What if my PDF has different page sizes after scanning?", "a": "Auto-crop computes the bounding box per-page, so pages are independently cropped to their own content."},
        {"q": "Will this affect printing?", "a": "After auto-crop, printing produces a smaller paper size. If you need the same paper size with less margin, use the Resize tool afterwards."},
    ],
    "bates-numbering": [
        {"q": "What's Bates numbering used for?", "a": "Sequential page identification across legal discovery documents. Each page in a production gets a unique identifier so attorneys can reference exact pages."},
        {"q": "Can I start the numbering at a value other than 1?", "a": "Yes — set start_number to any positive integer. This is the standard workflow for continuing a numbering scheme across multiple production batches."},
        {"q": "Does it survive redaction?", "a": "Yes — Bates numbers are stamped directly onto the page content, so they remain after redaction (unless the redaction rectangle covers them)."},
    ],
    "bmp-to-pdf": [
        {"q": "Why is the output PDF so much smaller than the BMPs?", "a": "BMP is uncompressed; PDF stores images in DCT (JPEG) or Flate format. A 5 MB BMP usually becomes a few hundred KB inside the PDF."},
        {"q": "Will quality degrade?", "a": "By default the conversion is near-lossless using high-quality JPEG. For 100% lossless, convert via PNG first (PNG-to-PDF) — slightly larger output."},
        {"q": "How many BMPs can I convert at once?", "a": "Up to the 500 MB total file limit. Several dozen images is routine."},
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
        {"q": "Does this work on scanned PDFs?", "a": "Only with OCR. Run OCR PDF on both files first so the text layer is present, then compare."},
        {"q": "How accurate is the text diff?", "a": "Word-level diff handles reordering, insertion, deletion, and formatting changes. Diffs based on character runs would be noisier."},
        {"q": "Can I compare more than two files?", "a": "Run Compare twice (A vs B, then B vs C) to chain a multi-revision comparison."},
    ],
    "crop-pdf": [
        {"q": "Difference between Crop and Auto-Crop?", "a": "Crop uses your manual margins (same on every page). Auto-Crop detects each page's actual content bounding box automatically."},
        {"q": "Will the cropped content be deleted from the file?", "a": "No — only the visible region changes. The full page content is still in the file. To permanently remove the cropped data, run Flatten or Sanitize afterwards."},
        {"q": "How do I undo a crop?", "a": "Re-open the PDF in PrivaTools Crop with negative margins to expand the box, or run Flatten which bakes the current crop in."},
    ],
    "delete-annotations": [
        {"q": "Will this remove form fields too?", "a": "Yes — form fields are a type of annotation. To preserve form structure but clear values, use the Fill Form tool with empty values instead."},
        {"q": "Are hyperlinks deleted?", "a": "Yes — hyperlinks are link annotations. Use this to make a PDF completely 'read-only' as a static document."},
        {"q": "Does this remove signatures?", "a": "Yes, signature annotations are removed too — which invalidates the cryptographic signature."},
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
        {"q": "My scans look fine — should I run deskew?", "a": "If the text appears tilted by more than ~0.5°, deskew helps OCR accuracy noticeably. For perfectly straight scans it's a no-op."},
        {"q": "Will deskew add white margins?", "a": "Yes — rotated pages need a slightly larger canvas. PrivaTools fills the margins with the surrounding background color (usually white)."},
        {"q": "Should I deskew before or after OCR?", "a": "Always before. OCR engines are much more accurate on straight-line text."},
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
        {"q": "Will my formulas be visible?", "a": "No — only computed values appear. The formulas themselves are not included (PDF has no formula concept)."},
        {"q": "What about charts and images?", "a": "Charts render as static images. Embedded images are preserved at their original size."},
        {"q": "How does it handle very wide sheets?", "a": "Wide sheets paginate across multiple PDF pages, with column headers repeated on each."},
    ],
    "extract-images": [
        {"q": "Will the images be the original resolution?", "a": "Yes. PDF embeds images at the resolution set when the PDF was created — extraction recovers them unchanged."},
        {"q": "What if the same image appears multiple times?", "a": "Each visual occurrence is extracted, even if it's the same underlying image data. Use deduplication after if needed."},
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
        {"q": "How do I know what the form field names are?", "a": "Use the /api/fill-form/fields endpoint (or paste-then-inspect): PrivaTools returns the list of field names, types, and current values without filling anything."},
        {"q": "Can I flatten the filled form?", "a": "Yes — run the Flatten tool afterwards to bake the values into the page content so they can't be edited."},
        {"q": "Does this work on signed forms?", "a": "Filling a signed form invalidates the signature. Sign last, after filling."},
    ],
    "gif-to-pdf": [
        {"q": "Do animated GIFs animate inside the PDF?", "a": "No — PDF doesn't support animation. Only the first frame is used. To convert animation to PDF, use GIF to MP4 then Video to PDF for keyframes."},
        {"q": "How is transparency handled?", "a": "GIF transparent pixels render against a white page background. Use PNG-to-PDF if you need true alpha."},
        {"q": "Can the GIF stay as a GIF inside the PDF?", "a": "PDF doesn't natively support GIF — the image is re-encoded as JPEG or Flate during embedding."},
    ],
    "grayscale-pdf": [
        {"q": "Will text still be searchable?", "a": "Yes — the text layer is preserved. Only the rendered visuals change to grayscale."},
        {"q": "Why convert to grayscale?", "a": "Cheaper printing on black-and-white printers, smaller file size, accessibility for color-blind readers, archival storage."},
        {"q": "How does this differ from black-and-white?", "a": "Grayscale preserves shading (256 grey levels). True black-and-white (1-bit) is harsher but smaller — not currently offered as a separate option."},
    ],
    "header-footer": [
        {"q": "Will the header/footer overlap existing content?", "a": "It might if your pages have content close to the edges. Use the Crop or Resize tool first to add margin space if needed."},
        {"q": "Can I exclude the cover page?", "a": "Pages-to-affect parameter accepts ranges like '2-' to skip the first page or '2-N-1' to skip first + last."},
        {"q": "Are these editable annotations or baked-in?", "a": "Baked into the page content. They can't be removed without re-editing — use Whiteout to cover them if needed later."},
    ],
    "heic-to-pdf": [
        {"q": "Will the PDF be much larger than the HEIC?", "a": "Yes — HEIC is more efficient than JPEG. The PDF uses JPEG internally and is typically 2-3x the size of the source HEICs."},
        {"q": "Does this preserve image quality?", "a": "Default JPEG quality is 90, which is visually indistinguishable. Lossless would require PNG-to-PDF and produce much larger files."},
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
        {"q": "Is there a limit on image size?", "a": "Very large images are rejected rather than processed, to protect the server's memory; normal photos and scans are far below that limit. Each upload also has the site-wide 500 MB limit."},
        {"q": "Can I make the text in my photographed pages searchable?", "a": "Not in this step — a PDF of photos is just pictures. Run OCR PDF on the result to add a searchable text layer."},
        {"q": "What happens to my images after I upload them?", "a": "It is uploaded over HTTPS and converted on the PrivaTools server in isolated temporary per-request storage, using local libraries rather than a third-party service. Response cleanup removes the images and the PDF and the result after your download is sent, and a background sweep clears anything an interrupted request leaves behind. Nothing is added to an account or file library."},
    ],
    "markdown-to-pdf": [
        {"q": "Are images included?", "a": "Local image references in the Markdown are inlined if they're in the same upload; remote URLs are fetched at render time."},
        {"q": "Can I customize the styling?", "a": "Not at the moment. The PDF uses a fixed, GitHub-inspired style with monospace code blocks, and custom CSS is not supported."},
        {"q": "Does it handle code-block syntax highlighting?", "a": "Yes — fenced code blocks with language hints get tokenized and colored (Python, JS, SQL, Bash, etc.)."},
    ],
    "metadata": [
        {"q": "What metadata does a typical PDF carry?", "a": "At minimum: producer (the software that created it) and creation date. Often also: author name, original filename, software version. Scanned PDFs may carry scanner model + driver."},
        {"q": "Why does this matter for privacy?", "a": "Producer + Creator + Author fields can identify the person or machine that created a document — useful in forensics, problematic for whistleblowers."},
        {"q": "Is XMP metadata shown too?", "a": "Yes — both the Info dictionary (old format) and XMP stream (new format) are inspected."},
    ],
    "nup": [
        {"q": "Why is this called 'N-up'?", "a": "Print-industry terminology: '2-up' = 2 pages per sheet, '4-up' = 4 per sheet, etc. Saves paper and ink for review prints."},
        {"q": "Are page numbers preserved?", "a": "Original page numbers (rendered on the page) shrink with the page. Add new page numbers afterwards if you need them readable."},
        {"q": "What aspect ratio works best?", "a": "2-up and 8-up work well for landscape, 4-up and 9-up for portrait. Mismatches add whitespace around each sub-page."},
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
        {"q": "Can I overlay only some pages?", "a": "By default it applies cycle-wise: if the overlay has 3 pages and the base has 10, the overlay repeats. For one-time overlay, use a base + overlay of equal length."},
        {"q": "Does transparency work?", "a": "Yes — PDF supports transparency and the overlay's alpha is honored. White rectangles still cover what's beneath; transparent regions show base content through."},
    ],
    "page-numbers": [
        {"q": "Can I use Roman numerals or letters?", "a": "No. Page numbers are Arabic digits only; Roman numerals and letters are not supported."},
        {"q": "How is this different from Bates numbering?", "a": "Page numbers are simple sequential digits. Bates numbers have a prefix, configurable padding, and are used in legal contexts."},
        {"q": "Can I start from a specific page?", "a": "Yes — pages-to-affect lets you specify a starting page (e.g. exclude cover + TOC)."},
    ],
    "pdf-to-bmp": [
        {"q": "Why are BMPs so much larger than PNG?", "a": "BMP stores every pixel uncompressed. PNG losslessly compresses to ~20% the size. Use BMP only when you specifically need uncompressed pixel data."},
        {"q": "What's BMP good for?", "a": "Legacy Windows software that doesn't support modern formats; embedded systems; precise pixel manipulation."},
        {"q": "Can I get just one page as BMP?", "a": "Extract that page first with Extract Pages, then convert."},
    ],
    "pdf-to-epub": [
        {"q": "How accurate is the EPUB compared to the PDF?", "a": "Text and basic structure transfer well. Complex multi-column layouts, footnotes, and figure captions may need cleanup in calibre."},
        {"q": "Does it preserve images?", "a": "Yes — embedded images are included as EPUB resources at original resolution."},
        {"q": "Will the table of contents work?", "a": "If the PDF has bookmarks, they become the EPUB's TOC. Without bookmarks, the TOC is built from detected headings."},
    ],
    "pdf-to-gif": [
        {"q": "Will the GIFs look good?", "a": "GIF's 256-color palette quantizes the page. Text remains readable but gradients and photos show banding. Use PNG for higher quality."},
        {"q": "Does this make an animated GIF?", "a": "No — each page is one static GIF. To make a flipbook-style animation, use Video to GIF after converting to images and back."},
        {"q": "How big are the output files?", "a": "Typically 30-100 KB per page at 96 DPI."},
    ],
    "pdf-to-jpg": [
        {"q": "Why JPG instead of PNG?", "a": "JPG is smaller for photos and scanned content (typically 5-10x smaller at quality 85). Use PDF-to-PNG if your PDF has crisp text or graphics where JPEG compression artifacts would show as ringing around letter edges."},
        {"q": "What about transparency?", "a": "JPG doesn't support transparency. White pages render as white; PDF transparent regions become white in JPG. For transparency, use PDF-to-PNG instead."},
        {"q": "How long does it take?", "a": "Roughly 50-100 ms per page at 150 DPI on the server. A 100-page PDF takes ~10 seconds end-to-end. Higher DPI (300+) increases time proportionally."},
        {"q": "What happens to a confidential PDF after I upload it?", "a": "The PDF is uploaded over HTTPS and rendered in isolated temporary per-request storage on the PrivaTools server, using local libraries rather than a third-party API. Response cleanup removes the PDF and the generated JPGs after the result is sent, and a background sweep clears anything left behind by an interrupted request."},
        {"q": "What DPI should I use?", "a": "96 DPI for web preview/thumbnails, 150 DPI for general on-screen viewing (default), 300 DPI for printable copies, 600 DPI for archival. Higher DPI = larger files. For social-media sharing, 150 DPI is typically more than enough."},
        {"q": "Can I convert just specific pages?", "a": "Yes. Enter individual page numbers or ranges (e.g. 1-3, 7, 12-15). Each selected page becomes one JPG. Single-page selections return as a single JPG; multi-page selections come as a ZIP."},
        {"q": "What's the file size limit?", "a": "Up to 500 MB per file on the hosted site. Each page becomes its own JPG, so a very long document produces a large ZIP and can hit the request timeout; split the PDF first if that happens. Fair-use rate limits apply."},
        {"q": "Do the JPGs carry a watermark or need an account?", "a": "No. The images carry no watermark and the tool works without an account. Fair-use rate limits apply to conversions, as on every tool."},
    ],
    "pdf-to-markdown": [
        {"q": "How accurate is the structural detection?", "a": "Headings work well when source fonts are larger. Tables transfer if cells are clearly separated. Code-block detection is a heuristic — manual review recommended."},
        {"q": "What about images?", "a": "Images are extracted to a sibling folder and referenced by Markdown image syntax."},
        {"q": "Will hyperlinks be preserved?", "a": "Yes — PDF hyperlinks become Markdown links."},
    ],
    "pdf-to-png": [
        {"q": "Why PNG instead of JPG?", "a": "PNG is lossless — text and graphics stay crisp. JPG compresses better for photos but introduces compression artifacts on text."},
        {"q": "How big are the PNGs?", "a": "Roughly 200-500 KB per page at 150 DPI for typical text content; up to 2-3 MB at 300 DPI."},
        {"q": "Does this preserve PDF transparency?", "a": "PDF transparency layers flatten during rasterization but the result PNG has alpha if the PDF page had transparent regions over the page background."},
    ],
    "pdf-to-pptx": [
        {"q": "Will the text be editable in PowerPoint?", "a": "The extracted text overlay is editable. The underlying page image stays as a backdrop. For pixel-perfect editing, you may need to remove the backdrop and rebuild from the text."},
        {"q": "What about embedded charts and graphics?", "a": "They appear as part of the page image. Re-creating editable charts requires manual recreation in PowerPoint."},
        {"q": "Can I get one slide per section instead of per page?", "a": "Not directly — use Extract Pages to isolate the sections first, then convert."},
    ],
    "pdf-to-tiff": [
        {"q": "Why TIFF for archival?", "a": "TIFF supports lossless compression (LZW, Deflate) and is the format of choice for long-term preservation in libraries and government archives."},
        {"q": "Single multi-page TIFF or one per page?", "a": "Default is multi-page TIFF for compact archiving. Use the per-page option for compatibility with software that only reads single-page TIFFs."},
        {"q": "Does it preserve text searchability?", "a": "TIFF is raster only — the text layer is lost. Use Sanitize PDF or PDF/A for archive while keeping text searchable."},
    ],
    "pdfa-validator": [
        {"q": "What is PDF/A and why does it matter?", "a": "PDF/A is an ISO standard for long-term archival. It requires self-contained PDFs (all fonts embedded, no external scripts, no encryption) so the document will render identically in 50 years."},
        {"q": "What's the difference between PDF/A-1, A-2, A-3?", "a": "A-1 is the strictest (no transparency, no XFA forms). A-2 adds transparency, JPEG 2000, and PDF attachments. A-3 allows arbitrary file attachments — useful for invoice + machine-readable data bundles."},
        {"q": "If it's not PDF/A, can I convert it?", "a": "Yes — use the PDF to PDF/A tool which fixes the most common issues automatically (font embedding, color profile attachment)."},
    ],
    "png-to-pdf": [
        {"q": "Will the PDF be larger than the PNGs?", "a": "Roughly the same — PNGs are already losslessly compressed, and PDF embeds them with minimal overhead."},
        {"q": "How is transparency handled?", "a": "Transparent PNGs render over a white background. If you need true alpha through, use the Image to PDF generic tool with the keep-alpha option."},
        {"q": "Is there a max number of images?", "a": "Practical limit is around 100 images per conversion before browser upload time becomes inconvenient. Backend limit is 500 MB total."},
    ],
    "pptx-to-pdf-convert": [
        {"q": "Will animations be preserved?", "a": "PDF doesn't support animation. Each slide renders in its initial state. For animation, export to video first."},
        {"q": "How are speaker notes handled?", "a": "Speaker notes are not included in the PDF, and there is no option to add them. Export the notes from your presentation software if you need them."},
        {"q": "What about embedded videos?", "a": "Videos render as a poster frame (the first frame). Use Extract Audio + Video to PDF for video-centric conversion."},
    ],
    "qr-code": [
        {"q": "Can I customize colors?", "a": "No. Codes are generated black on white; custom colours and centre logos are not supported. Plain high-contrast codes are also the most reliable to scan."},
        {"q": "How do I encode a URL with parameters?", "a": "Just paste the full URL. Special characters are encoded automatically inside the QR."},
        {"q": "What's the maximum data I can encode?", "a": "Around 2,500 alphanumeric characters or 4,000 numeric digits at error correction level L. Higher EC levels reduce capacity."},
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
        {"q": "Will my content be cropped if I resize to a smaller page?", "a": "No — content scales proportionally. If you want to crop instead, use the Crop tool."},
        {"q": "Difference between Resize and Crop?", "a": "Resize changes the page dimensions (scales content). Crop changes the visible region without scaling."},
        {"q": "Does this affect text quality?", "a": "Text is vector-based in PDFs, so it scales perfectly. Only embedded raster images can lose quality on extreme upscale."},
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
        {"q": "What about RTF features like fields?", "a": "Calculated fields (page numbers, dates) render as their current values. Form fields aren't converted to PDF form fields — use Form Creator for that."},
        {"q": "Does it preserve fonts?", "a": "Fonts referenced in the RTF are matched to server-installed fonts. Missing fonts fall back to a close visual equivalent."},
        {"q": "How does this differ from DOCX-to-PDF?", "a": "RTF is an older Microsoft format. DOCX is a newer ZIP-based format. Both convert similarly but DOCX preserves more layout fidelity."},
    ],
    "sanitize-pdf": [
        {"q": "What is sanitization protecting against?", "a": "Malicious PDFs that exploit reader vulnerabilities through embedded scripts or auto-launching attachments. Most modern readers are hardened against these, but defense in depth is wise."},
        {"q": "Does this remove form fields?", "a": "No — form fields are kept (just JavaScript actions on them are stripped). Use Flatten or Delete Annotations to remove form structure."},
        {"q": "Are hyperlinks removed?", "a": "Plain http/https links are kept. Links using non-web URI schemes (file:, mailto: with auto-execute, etc.) are stripped."},
    ],
    "set-permissions": [
        {"q": "What's the difference between owner password and user password?", "a": "User password = required to OPEN. Owner password = required to override permissions (print, edit). Use Protect PDF for both; this tool sets only the owner password + permission flags."},
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
        {"q": "Can I apply a stamp to only specific pages?", "a": "Yes — pages parameter accepts page ranges like '1-3' or 'all'."},
        {"q": "How big is the stamp?", "a": "Auto-sized to roughly 60% of page width with the chosen opacity for visibility without obscuring content."},
    ],
    "strip-metadata": [
        {"q": "Why strip metadata?", "a": "Author / producer / original-filename fields can identify who created or owns a document — a privacy concern for whistleblowers, journalists, or before public release."},
        {"q": "What about embedded images' EXIF?", "a": "Image-level EXIF inside PDF embedded images is also stripped. The image pixel data is unchanged."},
        {"q": "Is this the same as Sanitize?", "a": "No — Strip Metadata removes informational fields. Sanitize removes security-risky elements (JavaScript, auto-launch attachments)."},
    ],
    "svg-to-pdf": [
        {"q": "Will my SVG stay as vector inside the PDF?", "a": "Yes — PDF natively supports vector content, so paths, text, and gradients remain editable at any zoom level."},
        {"q": "What about embedded raster images inside SVG?", "a": "Embedded raster images (data URLs, external image refs) are preserved as raster within the PDF."},
        {"q": "Does it handle CSS styles inside SVG?", "a": "Standard SVG CSS (fill, stroke, opacity, transform) is honored. External stylesheet refs are inlined first."},
    ],
    "tiff-to-pdf": [
        {"q": "Will quality be preserved?", "a": "Yes — TIFF is lossless. PDF uses Flate (lossless) or JPEG (near-lossless) when embedding. Default is high-quality JPEG to keep file size reasonable."},
        {"q": "What about CMYK TIFFs (for print)?", "a": "CMYK is preserved through to the PDF. Use this workflow for prepress / professional printing pipelines."},
        {"q": "How are multi-page TIFFs handled?", "a": "Each TIFF page becomes a PDF page in order. Multiple multi-page TIFFs in one upload are concatenated."},
    ],
    "transparent-background": [
        {"q": "Will text be affected?", "a": "Black text is preserved. Light grey or low-contrast text near the threshold may become semi-transparent — lower the threshold (e.g. 220) to be more aggressive about preserving content."},
        {"q": "What's the output format?", "a": "PDF with transparent regions where the background was. Open in a reader to see the underlying canvas show through."},
        {"q": "Can I use this on photos?", "a": "It works best on text/diagram documents with clean backgrounds. Photos with light skies become weirdly transparent — use Remove Background (rembg) for photos."},
    ],
    "verify-signature": [
        {"q": "Does this require uploading my certificates?", "a": "No — verification uses the certificates embedded in the PDF itself, plus the system's trusted CA store."},
        {"q": "What if a signature is invalid?", "a": "The report says exactly why: content modified, certificate expired, untrusted issuer, or signature format unsupported. The PDF itself isn't rejected — just the signature."},
        {"q": "Can I verify multiple signatures?", "a": "Yes — PDFs can have multiple signatures (e.g. one per signing party). All are verified independently."},
    ],
    "webp-to-pdf": [
        {"q": "Will the PDF be much smaller than from JPG?", "a": "Slightly smaller — WebP-derived JPEGs inside PDF are similar to direct JPGs. The main benefit was at upload time (smaller WebP files)."},
        {"q": "What about animated WebP?", "a": "Only the first frame is used. PDF doesn't support animation."},
        {"q": "Does this preserve transparency?", "a": "PDF supports transparency but most readers render text-on-transparency oddly. We default to compositing over white for best compatibility."},
    ],
    "whiteout-pdf": [
        {"q": "Is whiteout the same as redaction?", "a": "No — whiteout covers content visually but the underlying text remains in the file. For permanent redaction (text removed), use Redact PDF or Smart Redact."},
        {"q": "Can I use any color, not just white?", "a": "Yes — color is configurable. Black for blackout style, white for whiteout, any custom hex color for matching background."},
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
        {"q": "Will it preserve folder structure?", "a": "Uploaded files are placed at the root of the archive. To preserve a folder structure, upload them folder-by-folder using the multi-folder option."},
        {"q": "What compression level should I choose?", "a": "Balanced is best for most files. Store is fastest for already-compressed files like JPG, MP4, and PDF. Maximum can shrink text-heavy files more but takes longer."},
    ],
    "csv-json": [
        {"q": "How does CSV escaping work?", "a": "Standard RFC 4180: commas in values must be quoted; quotes inside values are doubled (\"\"). PrivaTools handles both."},
        {"q": "What about nested JSON?", "a": "Nested objects are flattened to dot-notation columns (user.name, user.email) for CSV output. Reverse direction reconstructs the nesting."},
        {"q": "Will my data be uploaded?", "a": "No — pure-browser conversion. No data leaves your machine."},
    ],
    "extract-archive": [
        {"q": "What about password-protected archives?", "a": "Password-protected archives are not supported yet. Extract Archive handles unencrypted ZIP and TAR-family archives."},
        {"q": "Does it support RAR / 7z?", "a": "No. Extract Archive supports ZIP and TAR-family archives (.tar, .tar.gz, .tar.bz2, .tar.xz). RAR and 7z are not supported."},
        {"q": "What if the archive contains many small files?", "a": "Up to 1000 files per archive. For larger, split before zipping."},
    ],
    "extract-audio": [
        {"q": "Will quality be preserved?", "a": "WAV and FLAC store the decoded audio without further loss. MP3, AAC and OGG are re-encoded at the encoders' default settings, about 128 kbps for stereo MP3 and AAC, and there is no bitrate setting here."},
        {"q": "What if the video has multiple audio tracks?", "a": "The first (default) audio track is extracted. Choosing another track, or extracting several at once, is not supported."},
        {"q": "Can I extract just a section of the audio?", "a": "Use Trim Media first to isolate the section, then extract audio from the trimmed video."},
    ],
    "generate-barcode": [
        {"q": "What barcode type for a URL?", "a": "Use QR code — barcodes like Code 128 work for text but are much wider for the same content."},
        {"q": "Will it scan reliably?", "a": "Yes — barcodes are rendered at the standard 2D module size. Printed at 100% on a regular printer, any standard scanner reads them."},
        {"q": "Can I include a check digit?", "a": "EAN-13 and UPC-A auto-calculate the check digit. Code 128 has a built-in checksum. Code 39 supports optional checksums."},
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
        {"q": "What about extensions like tables and code blocks?", "a": "GitHub-flavored Markdown extensions are supported in both directions: tables, fenced code, strikethrough, task lists."},
        {"q": "Will inline CSS be preserved?", "a": "Conversion is opinionated — visible content keeps semantics, but custom CSS is stripped. For a faithful HTML→PDF, use the Markdown-to-PDF tool instead."},
        {"q": "Is the conversion lossless?", "a": "HTML → Markdown can lose nesting fidelity (deeply-nested divs flatten). Markdown → HTML is exact."},
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
        {"q": "What scale should I pick?", "a": "Work out the pixel size you actually need. The default of 2 renders at twice the SVG's own dimensions, which suits high-resolution displays. Raise it for print or large artwork, and drop below 1 when the SVG is already larger than you need."},
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
        {"q": 'Why do I have to type the prefix and digits?', "a": 'So the tool removes stamps and nothing else. A bare search for numerals would happily delete page numbers, figures and dates. Describing the format is what keeps the removal surgical.'},
        {"q": "Does removing Bates numbers change the rest of the page?", "a": "No. Only the matching stamp objects are removed; the remaining text, images and layout are untouched. The result is a new PDF, so the file on your device stays as it was."},
        {"q": 'Can I renumber after removing?', "a": 'Yes. Strip the old stamps here, then use Bates Numbering to apply a fresh sequence with whatever prefix and starting number you need.'},
        {"q": "Is it free and account-free?", "a": "Yes. No account and no watermark, the same as every other tool on the site. Fair-use rate limits apply."},
    ],
    "pdf-to-long-image": [
        {"q": 'Why would I want one tall image instead of a PDF?', "a": 'Because some places will not take a PDF. Chat apps, image-only uploaders, social posts and some ticketing systems accept an image and nothing else. A single tall PNG shows the whole document without asking anyone to download a file.'},
        {"q": 'Should I choose PNG or JPG?', "a": 'PNG for text, screenshots and line art, where it stays sharp and lossless. JPG for scans and photographs, where it produces a far smaller file at quality 90. A long text document saved as JPG will show fringing around the letters.'},
        {"q": 'What resolution are the pages rendered at?', "a": '100 DPI, which keeps a normal page readable while stopping a long document from becoming an unusable image. A 30-page document produces an image roughly 30,000 pixels tall.'},
        {"q": 'What happens if my pages are different sizes?', "a": 'The canvas takes the width of the widest page and every narrower page is centred on it, so a document mixing portrait and landscape stays aligned instead of stepping left and right.'},
        {"q": 'Is there a page limit?', "a": 'No hard limit, but very long documents produce images some software will refuse to open. If you hit that, split the PDF first and stitch each part separately.'},
    ],
    "remove-watermark": [
        {"q": 'What kind of watermarks can this actually remove?', "a": 'Watermarks that exist as objects in the PDF: repeated text like DRAFT or CONFIDENTIAL, and image stamps placed on each page. Those can be identified and deleted cleanly. A watermark flattened into a scanned page is part of the image and this tool will not find it.'},
        {"q": 'Why does it show me candidates instead of removing everything?', "a": 'Because the repeated object on your page might be a logo, a letterhead or a footer you want to keep. The tool finds what behaves like a watermark and lets you decide, rather than silently stripping page furniture.'},
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
        {"q": "Does it keep the original layout?", "a": "No. Text is translated, not typeset: the result is plain text per page, and 'Save as PDF' produces a simple text PDF, not a copy of the original design."},
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
        {"q": "Does MKV to MP4 re-encode the video?", "a": "Yes. Every file is re-encoded to H.264 video (CRF 23) and AAC audio, even when the MKV's streams would already fit in an MP4, so it is not a lossless container swap. Only one audio track is kept, and subtitle tracks are dropped."},
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
