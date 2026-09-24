export interface BlogSource { label: string; url: string; }
export interface BlogPost {
  slug: string;
  title: string;
  description: string;
  publishedAt: string;
  updatedAt?: string;
  reviewedAt?: string;
  readTime: string;
  tags: string[];
  body: string;
  author?: string;
  tldr?: string;
  relatedTools?: string[];
  sources?: BlogSource[];
}

/** Published slugs are stable. Reviews are dated when the content was checked. */
export const blogPosts: BlogPost[] = [
  {
    "slug": "remove-bg-canva-alternative",
    "title": "remove.bg is moving to Canva: choosing your next workflow",
    "description": "A practical guide to assessing a background-removal alternative: processing location, transparent PNG output and a representative image check.",
    "publishedAt": "2026-09-14",
    "updatedAt": "2026-09-24",
    "reviewedAt": "2026-09-24",
    "readTime": "3 min read",
    "author": "PrivaTools",
    "tags": ["Images", "Comparison", "Workflow"],
    "tldr": "Choose around the result you need: a standalone transparent PNG or a cutout inside a larger design workflow. Test a representative image, understand its processing path and keep the original before changing tools.",
    "relatedTools": ["remove-background", "image-converter", "resize-crop-image"],
    "body": "<p>The <a href=\"https://www.remove.bg/faq\">official remove.bg notice</a> says background removal is moving into Canva. When we checked it on 24 September 2026, its FAQ said the standalone website will no longer be available from 1 December 2026 at 9:00am CET, that the self-service API stops accepting requests that day and that unused pay-as-you-go credits expire then. Until that date the <a href=\"https://www.remove.bg/\">remove.bg homepage</a> still offers its background remover, so plan the move before the closure rather than after it.</p>\n<h2>Begin with the job you need to finish</h2>\n<p>A product photograph for a shop, a portrait for a presentation and an image inside a design have different finishing requirements. Write down the output dimensions, file format and application where the cutout will be used. A transparent PNG may be the complete job; in another workflow, it is only the first step.</p>\n<p>If you already design in Canva, assess whether keeping the cutout in that environment is useful. If you need a file to take elsewhere, evaluate a standalone remover. Our <a href=\"/compare/remove-bg\">PrivaTools and remove.bg comparison</a> sets out these choices with the original sources. It is written by PrivaTools, rather than an independent testing organisation.</p>\n<h2>Try a representative image in PrivaTools</h2>\n<ol><li>Open <a href=\"/tools/remove-background\">Background Remover</a>. An account is not required for the interactive file tool.</li><li>Choose an image that resembles your normal work, such as a product with a handle or a portrait with fine hair.</li><li>Read “Where to process” and the selected engine’s disclosure before starting. The server engine uploads the image for processing.</li><li>Run the task, then inspect the actual result before downloading the transparent PNG.</li></ol>\n<p>The current server output preserves the image dimensions. That does not guarantee a perfect outline: fine strands, glass, shadows and colours close to the background can be difficult for a model. Keep the original so you can try a clearer source or another workflow.</p>\n<h2>Check the cutout where it will be used</h2>\n<p>Place the PNG against both a light and a dark background in your destination application. Look for missing details, unwanted patches and halos. Confirm that the subject still looks correct at the size at which people will see it.</p>\n<p>Keep PNG when you need transparency. A later conversion to JPEG makes transparent areas opaque. Use <a href=\"/tools/image-converter\">Image Converter</a> or <a href=\"/tools/resize-crop-image\">Resize &amp; Crop</a> only when your destination needs that change, and inspect the new file again.</p>\n<h2>Choose the data path deliberately</h2>\n<p>Guest access and local processing are separate decisions. Read the <a href=\"/blog/remove-background-without-uploading\">background-removal engine guide</a> and the current workspace disclosure. Model preparation, browser support and available resources can affect which option fits your device; do not assume that installing the PWA makes every operation work offline.</p>\n<p>For a recurring workflow, keep a small set of accepted sample outputs. Recheck those samples when an engine, service or destination requirement changes. The useful alternative is the one that consistently produces a result you can use, with a processing path you understand.</p>",
    "sources": [
      { "label": "remove.bg migration notice", "url": "https://www.remove.bg/faq" },
      { "label": "remove.bg product page", "url": "https://www.remove.bg/" },
      { "label": "PrivaTools Background Remover", "url": "/tools/remove-background" },
      { "label": "PrivaTools background-removal engine guide", "url": "/blog/remove-background-without-uploading" }
    ]
  },
  {
    "slug": "compress-pdf-without-losing-quality",
    "title": "How to compress a PDF while keeping it readable",
    "description": "Choose a PDF compression setting, compare the result with your original, and recognise when a smaller file is the wrong trade-off.",
    "publishedAt": "2026-03-22",
    "readTime": "2 min read",
    "tldr": "Start with a balanced preset, keep the original, and inspect small text, diagrams and scanned pages in the result. Lossy compression changes image data; there is no universal percentage saving or guarantee of identical quality.",
    "relatedTools": [
      "compress-pdf",
      "delete-pages",
      "extract-pages"
    ],
    "tags": [
      "PDF",
      "Compression",
      "How-To"
    ],
    "body": "<p>A smaller PDF is useful only if the person receiving it can still read it. Begin with the actual delivery requirement: an attachment limit, a slower connection, or a document that will be printed. Those goals call for different compromises.</p>\n<h2>Start with a copy and one sensible setting</h2>\n<ol><li>Open <a href=\"/tool/compress-pdf\">Compress PDF</a> and choose your file.</li><li>Read the processing disclosure. This tool sends the PDF to the PrivaTools backend.</li><li>Try the balanced preset before the more aggressive options. Keep the untouched source separately.</li><li>Download the result and compare its size with the original.</li><li>Open both files at the same zoom. Check a dense paragraph, a chart, a photograph and a page with small labels.</li></ol>\n<p>The compressor recompresses supported embedded images and rewrites PDF structures. It cannot promise the same reduction for a photograph-heavy scan and a short, already efficient text document.</p>\n<h2>What quality loss actually means</h2>\n<p>Reducing an image’s dimensions or JPEG quality discards information. A page may look acceptable on a phone and show softer lettering when enlarged. Check the size at which the recipient will read or print it, and choose a gentler setting if the difference matters.</p>\n<p>Text-only PDFs may shrink very little. An output can even grow. That is a reason to keep the original, not to keep applying stronger compression indefinitely.</p>\n<h2>When another step helps more</h2>\n<p>Use <a href=\"/tool/delete-pages\">Delete Pages</a> to remove pages the recipient does not need. Use <a href=\"/tool/extract-pages\">Extract Pages</a> when you only need a section. Neither decision should be made solely to hit a byte target if it would omit necessary information.</p>\n<p>Metadata removal is a separate privacy decision. It is not a substitute for compression, and it can remove a useful document title. Do not flatten forms unless you are ready to lose their editable fields.</p>\n<h2>A note for command-line users</h2>\n<p>Ghostscript is a separate option, not the engine behind this compressor. Its own documentation warns that PDF presets can alter the input and that <code>/prepress</code> does not mean the closest possible match to the original. Read the <a href=\"https://ghostscript.readthedocs.io/en/latest/VectorDevices.html\">Ghostscript device documentation</a> before using a preset in an automated workflow.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Ghostscript high-level device documentation",
        "url": "https://ghostscript.readthedocs.io/en/latest/VectorDevices.html"
      },
      {
        "label": "PrivaTools compression workspace",
        "url": "/tool/compress-pdf"
      }
    ]
  },
  {
    "slug": "merge-pdf-files-online-free",
    "title": "How to merge PDF files in the right order",
    "description": "Combine PDF files, check page order and document structure, and understand the server processing step before you begin.",
    "publishedAt": "2026-03-22",
    "readTime": "2 min read",
    "tldr": "Add the PDFs, put the files in reading order, run the merge, and inspect the first and last pages of each section. Merging in PrivaTools uses its server; an account is not required for the interactive tool.",
    "relatedTools": [
      "merge-pdf",
      "extract-pages",
      "organize-pages"
    ],
    "tags": [
      "PDF",
      "Merge",
      "How-To"
    ],
    "body": "<p>Before merging, write down the order you want the reader to encounter: cover, main document, appendices. Filenames such as <code>01-cover.pdf</code> and <code>02-report.pdf</code> make mistakes easier to spot, but the order shown in the workspace is the order to check.</p>\n<h2>Combine the files</h2>\n<ol><li>Open <a href=\"/tool/merge-pdf\">Merge PDF</a> and add the source PDFs.</li><li>Reorder the file list. Remove accidental duplicates before processing.</li><li>Check the workspace’s current file and size limits rather than assuming an unlimited queue.</li><li>Run the merge and download the resulting PDF.</li><li>Confirm the final page count and the boundaries between documents.</li></ol>\n<p>A merge does not rewrite every page into a uniform design. Different page sizes and orientations can remain in the combined file. That may be exactly what you want for an appendix; it can also make printing awkward.</p>\n<h2>Choose pages before combining</h2>\n<p>If a source contains only a few relevant pages, open <a href=\"/tool/extract-pages\">Extract Pages</a> first and merge the extracted result. When you need to move individual pages rather than whole files, use <a href=\"/tool/organize-pages\">Organize Pages</a>.</p>\n<p>Do not remove a signature page, footnote page or appendix just because it looks repetitive. Review the document’s meaning as well as its page count. Keep any signed original separately, because a rewritten document is a different file.</p>\n<h2>Check an awkward input</h2>\n<p>A password-protected PDF may need to be unlocked with the correct password before another tool can read it. A broken PDF may open in one viewer and still fail to merge. Try a small, non-sensitive file to distinguish a service problem from a problem with one document.</p>\n<h2>Where the files go</h2>\n<p>This is a server operation. The upload and generated result use temporary storage, with response cleanup and a separate sweep for leftover files. A failed or interrupted request can delay cleanup. The <a href=\"/trust\">trust center</a> explains the current processing model; the <a href=\"/status\">status page</a> helps diagnose availability. Downloaded copies remain under your control.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools processing and privacy details",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "best-free-pdf-tools-2026",
    "title": "How to choose a free PDF toolkit in 2026",
    "description": "Compare free PDF tools by the job you need, processing location, output quality and current limits rather than an unsupported ranking.",
    "publishedAt": "2026-03-22",
    "readTime": "2 min read",
    "tldr": "Start with the task and the file’s sensitivity. Then check the current tool page, export restrictions, processing path and output. This is a selection guide, not a claim that we benchmarked every product.",
    "relatedTools": [
      "merge-pdf",
      "compress-pdf",
      "edit-pdf"
    ],
    "tags": [
      "Comparison",
      "PDF"
    ],
    "body": "<p>A toolkit with the most buttons is not automatically the right one for your file. A person combining two handouts has different needs from someone correcting a form or handling a document that cannot be sent to an external service.</p>\n<h2>Write down the one job that matters</h2>\n<p>List the input, the desired output and any requirements: selectable text, an editable form, a size limit, no watermark, or a workflow that can be repeated. This makes a comparison concrete. “Has an editor” is much less useful than “can edit the field I need without flattening the form.”</p>\n<h2>Compare three delivery models</h2>\n<table><thead><tr><th>Model</th><th>Useful question</th></tr></thead><tbody><tr><td>Browser processing</td><td>Does this exact task process locally, including its selected AI mode?</td></tr><tr><td>Cloud processing</td><td>What is uploaded, who processes it, and how is retention explained?</td></tr><tr><td>Desktop or self-hosted</td><td>Can you install, maintain and approve the environment you will use?</td></tr></tbody></table>\n<p>PrivaTools has browser utilities and server-backed file tools. Some AI workspaces can send content to a provider you choose. The <a href=\"/trust\">trust center</a> explains those distinctions rather than treating the whole catalogue as one processing model.</p>\n<h2>Check the current restrictions</h2>\n<p>Inspect the feature you will actually use for file size, page count, queue size, export limitations and account requirements. Product plans change. Do not build a workflow around a price or quota copied from an old comparison table.</p>\n<p>Our <a href=\"/compare\">comparison pages</a> link to current product sources and describe trade-offs. For broader context, read the vendors’ own information, including <a href=\"https://www.ilovepdf.com/help/security\">iLovePDF’s security details</a> and <a href=\"https://smallpdf.com/privacy\">Smallpdf’s privacy notice</a>.</p>\n<h2>Run your own small acceptance check</h2>\n<p>Use a non-sensitive sample with the same layout as the real file. Process it, download it, and inspect the properties that matter to you. That result is more relevant than an invented universal winner. Keep the original and choose the tool that meets your requirements with an acceptable processing path.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "iLovePDF security information",
        "url": "https://www.ilovepdf.com/help/security"
      },
      {
        "label": "Smallpdf privacy notice",
        "url": "https://smallpdf.com/privacy"
      },
      {
        "label": "PrivaTools comparisons",
        "url": "/compare"
      }
    ]
  },
  {
    "slug": "remove-password-from-pdf",
    "title": "How to remove a PDF password you know",
    "description": "Unlock a PDF with its correct password, understand opening versus permission restrictions, and keep the unprotected copy under control.",
    "publishedAt": "2026-03-22",
    "readTime": "2 min read",
    "tldr": "Use Unlock PDF with the correct password and only for a document you are authorised to change. This removes protection from the new output; it does not recover an unknown password or secure the downloaded copy.",
    "relatedTools": [
      "unlock-pdf",
      "protect-pdf"
    ],
    "tags": [
      "PDF",
      "Security",
      "How-To"
    ],
    "body": "<p>An encrypted PDF may ask for a password before opening. A different restriction can limit printing or editing after the document opens. These are different situations, and “unlock” should not be read as a promise to recover an unknown password.</p>\n<h2>Unlock an authorised copy</h2>\n<ol><li>Open <a href=\"/tool/unlock-pdf\">Unlock PDF</a> and add the protected file.</li><li>Enter the password you were given. Check for copied spaces if it is rejected.</li><li>Run the tool and download the new PDF.</li><li>Open the output in a separate viewer to confirm it no longer asks for the password.</li></ol>\n<p>The interactive tool does not require an account. The server receives the PDF and the password needed to process it, so read the disclosure before submitting a sensitive document.</p>\n<h2>What to do when the password fails</h2>\n<p>Ask the sender for the correct password or an authorised unprotected copy. Check that you selected the intended document; similarly named files can use different passwords. Repeatedly guessing in an online tool is not a recovery strategy.</p>\n<p>Permission flags are also not a grant of permission from the document owner. Make sure changing or redistributing the file is appropriate for your situation.</p>\n<h2>The output needs its own care</h2>\n<p>An unlocked download can be opened by anyone who has access to it. Save it in an appropriate folder and review where that folder synchronises. The original may still be protected while the new file is not.</p>\n<p>If you need to share a newly protected copy, use <a href=\"/tool/protect-pdf\">Protect PDF</a> with a fresh password. Send that password through an appropriate separate channel rather than embedding it in the filename.</p>\n<h2>Saved passwords and sign-in are separate</h2>\n<p>PDF passwords saved in <a href=\"/my-stuff/vault\">Vault</a> belong to this browser’s local vault. They are not your PrivaTools sign-in password. Clearing site data can remove local records, and signing in should not be treated as a backup for those records. See <a href=\"/privacy\">the privacy information</a> before relying on local storage for anything irreplaceable.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools processing and privacy details",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "convert-word-to-pdf-free",
    "title": "How to convert Word to PDF and check the layout",
    "description": "Convert a Word document, then check fonts, tables, page breaks and links before sharing the PDF.",
    "publishedAt": "2026-03-22",
    "readTime": "2 min read",
    "tldr": "Convert a copy of your Word document, then inspect the generated PDF. Office conversion runs on the server and can change layout when fonts or document features differ from the source application.",
    "relatedTools": [
      "word-to-pdf",
      "compress-pdf"
    ],
    "tags": [
      "PDF",
      "Convert",
      "How-To"
    ],
    "body": "<p>A PDF is often the easier format to send, but exporting does not guarantee that every recipient will see exactly what you saw in Word. The conversion engine, available fonts and document features all affect the result.</p>\n<h2>Prepare the Word file</h2>\n<p>Finish any comments or tracked-change decisions in your source editor before conversion. Check the paper size and orientation, and give images enough room around page breaks. Keep the editable source; a PDF is not a replacement for it.</p>\n<ol><li>Open <a href=\"/tool/word-to-pdf\">Word to PDF</a>.</li><li>Choose a supported document and read the server-processing notice.</li><li>Convert and download the PDF.</li><li>Compare the first page, the final page, and the busiest table with the source.</li></ol>\n<h2>Look for layout changes</h2>\n<p>Font substitution can change line lengths, which changes page breaks. Tables near the edge of a page can move or split differently. Headers, footers, equation layout and linked objects deserve a separate inspection.</p>\n<p>If exact typesetting is essential, export a PDF from the application and environment where the document was authored. Compare that output with the online conversion rather than assuming either route is always superior.</p>\n<h2>Keep text useful</h2>\n<p>Try selecting a sentence and following a link in the output. A page that looks right can still be awkward to search or copy. If the goal is an accessible document, visual inspection alone is insufficient: reading order, headings and form labels require their own checks.</p>\n<p>Use <a href=\"/tool/compress-pdf\">Compress PDF</a> only after the layout is accepted. Recheck images and fine text after compression rather than evaluating the uncompressed version and sending a different file.</p>\n<h2>Handle a failed conversion</h2>\n<p>Open the source locally to confirm it is intact. Remove unsupported embedded objects from a copy, or save into a supported format. Do not rename a file extension to make it appear compatible. If a simple document also fails, check <a href=\"/status\">service status</a>. The tool’s accepted types and current limits are the practical guide for this deployment.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools processing and privacy details",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "edit-pdf-online-free-no-sign-up",
    "title": "How to edit a PDF without creating an account",
    "description": "Choose the right PDF editor for text overlays, annotations, forms and page changes, then check the downloaded result.",
    "publishedAt": "2026-03-29",
    "readTime": "2 min read",
    "tldr": "Use Edit PDF for visible additions, a form tool for actual fields, and Redact PDF for removing sensitive content. Adding text or a white box is not the same as changing the original text beneath it.",
    "relatedTools": [
      "edit-pdf",
      "annotate-pdf",
      "fill-form",
      "redact-pdf",
      "organize-pages"
    ],
    "tags": [
      "PDF",
      "Edit",
      "How-To"
    ],
    "body": "<p>“Edit a PDF” can mean several different jobs. Writing a note, correcting an underlying paragraph, filling a form and removing confidential text need different approaches. Start by identifying which result you actually need.</p>\n<h2>Choose the matching workspace</h2>\n<ul><li><a href=\"/tool/edit-pdf\">Edit PDF</a> gives you a page canvas for visible additions and adjustments.</li><li><a href=\"/tool/annotate-pdf\">Annotate PDF</a> is useful for review notes and marks.</li><li><a href=\"/tool/fill-form\">Fill PDF Form</a> targets existing form fields.</li><li><a href=\"/tool/redact-pdf\">Redact PDF</a> removes selected content from a new output.</li></ul>\n<p>These interactive workspaces do not require a PrivaTools account. Their processing paths differ, so check the disclosure in the workspace you choose rather than assuming every editor is browser-only.</p>\n<h2>Make one change, then inspect it</h2>\n<ol><li>Open the file and choose the intended page in the page navigation.</li><li>Make a small change with the relevant tool or control.</li><li>Use the page preview to check position, scale and colour.</li><li>Export the result and open it in another PDF viewer.</li></ol>\n<p>When adding a text overlay, zoom in to check the baseline and line breaks. An overlay can look convincing while leaving the original text selectable underneath. It is useful for a note; it is not a confidential deletion.</p>\n<h2>Keep forms and signatures distinct</h2>\n<p>A typed label placed over a blank field does not create an interactive form field. A drawn signature is a visual mark, not proof that a cryptographic certificate validates the document. Preserve the original signed document when those properties matter.</p>\n<h2>Know when to return to the source</h2>\n<p>If you need to reflow paragraphs, change a complex table or rebuild a layout, edit the source document and export a new PDF. That can be more reliable than placing many patches over a fixed page. For simple page moves, <a href=\"/tool/organize-pages\">Organize Pages</a> is the more direct choice.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools processing and privacy details",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "split-pdf-online-free",
    "title": "How to split a PDF into useful sections",
    "description": "Separate a PDF by page ranges, extract selected pages, and check that each output contains the intended content.",
    "publishedAt": "2026-03-29",
    "readTime": "2 min read",
    "tldr": "Use Split PDF to divide a document, or Extract Pages when you need one selection. Check physical page positions against printed page numbers, then inspect each downloaded result.",
    "relatedTools": [
      "split-pdf",
      "extract-pages",
      "delete-pages"
    ],
    "tags": [
      "PDF",
      "Split",
      "How-To"
    ],
    "body": "<p>A PDF’s first physical page may be a cover even when the printed numbering begins later. Before entering a range, check the page navigation. Otherwise “pages 1–3” can produce a different section from the one you intended.</p>\n<h2>Split, extract or delete?</h2>\n<ul><li><a href=\"/tool/split-pdf\">Split PDF</a> divides a source into separate outputs according to the available splitting options.</li><li><a href=\"/tool/extract-pages\">Extract Pages</a> keeps a selected set of pages in a new document.</li><li><a href=\"/tool/delete-pages\">Delete Pages</a> removes a selection and keeps the remaining pages.</li></ul>\n<p>Choose the operation that describes the output you want. It is easier to verify “keep the appendix” than to reason through a long list of pages to discard.</p>\n<h2>Make the selection</h2>\n<ol><li>Open the matching workspace and add your PDF.</li><li>Navigate to the first and last page of the section.</li><li>Choose or enter the page selection, checking that it stays within the document.</li><li>Run the operation and download the result or archive.</li><li>Open each output and verify both its boundaries and its page count.</li></ol>\n<h2>Check more than the thumbnail</h2>\n<p>A nearly blank page may hold a footnote, a signature or intentionally empty space before a new chapter. A page with repeated branding may still contain different text. Inspect the page itself before leaving it out.</p>\n<p>After extraction, links or bookmarks that previously pointed to another part of the original may no longer lead where the reader expects. Test the navigation you plan to rely on.</p>\n<h2>Share the right files</h2>\n<p>Name the outputs clearly and keep them separate from the original. If the tool downloads a ZIP, confirm which PDFs are inside it before sending the archive. Splitting does not remove metadata or confidential content from retained pages.</p>\n<p>These PDF operations use server processing in the current implementation. The <a href=\"/trust\">processing disclosure</a> explains temporary files and cleanup; it does not cover copies you retain in Downloads, email or a synced folder.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools processing and privacy details",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "redact-pdf-free-guide",
    "title": "How to redact sensitive information from a PDF",
    "description": "Select the correct page and region, apply a real redaction, and inspect the exported document before sharing it.",
    "publishedAt": "2026-03-29",
    "readTime": "2 min read",
    "tldr": "Use the redaction tool, apply the selected regions, and verify the downloaded output. A black rectangle added by a drawing or annotation tool can leave the original content underneath.",
    "relatedTools": [
      "redact-pdf",
      "smart-redact",
      "strip-metadata"
    ],
    "tags": [
      "PDF",
      "Security",
      "Redaction",
      "How-To"
    ],
    "body": "<p>Redaction is a removal task. A coloured rectangle is only a visual addition unless a tool explicitly applies redaction to the underlying content. Start with a copy of the original and a list of what must be removed.</p>\n<h2>Mark the right regions</h2>\n<ol><li>Open <a href=\"/tool/redact-pdf\">Redact PDF</a> and select the document.</li><li>Navigate to the intended page, paying attention to physical page order.</li><li>Draw a region around the sensitive material. Include enough margin to cover every visible character.</li><li>Review the selected regions before applying them.</li><li>Run the operation and save the new file separately.</li></ol>\n<p>The apply step uses the server. A local page preview does not mean the final operation stays on your device. The backend uses redaction operations rather than simply painting over the page; <a href=\"https://pymupdf.readthedocs.io/en/latest/page.html#Page.apply_redactions\">PyMuPDF documents the behaviour and options of applied redactions</a>.</p>\n<h2>Verify the exported PDF</h2>\n<p>Reopen the download. Search for the removed words, try selecting text across the region, and inspect a text export. Look at nearby content too: a region that is too wide can remove information you intended to keep.</p>\n<p>These checks can reveal common mistakes, but they are not a guarantee that every sensitive reference anywhere in the file has been found. Attachments, metadata, comments and repeated information elsewhere need separate review.</p>\n<h2>Work through a whole document</h2>\n<p>Keep a list of names, identifiers and other items you intend to remove. Search for variations and inspect images that may contain the same information. Automatic suggestions are useful candidates to review, not a final approval.</p>\n<h2>Keep the original out of the delivery folder</h2>\n<p>Give the redacted output a distinct filename. Open the exact file you are about to send, not an earlier preview. If you need a more thorough verification routine, continue with <a href=\"/blog/redact-pdf-permanently-guide\">the redaction review checklist</a>.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PyMuPDF applied redactions",
        "url": "https://pymupdf.readthedocs.io/en/latest/page.html#Page.apply_redactions"
      },
      {
        "label": "PrivaTools redaction workspace",
        "url": "/tool/redact-pdf"
      }
    ]
  },
  {
    "slug": "best-free-online-pdf-editors-2026",
    "title": "Choosing a free PDF editor: what to test before committing",
    "description": "Evaluate a PDF editor with a small sample that covers text additions, forms, redaction and the final export.",
    "publishedAt": "2026-03-29",
    "readTime": "2 min read",
    "tldr": "Choose by the kind of edit, not a “best editor” badge. Test a representative page and its download, especially when form fields, underlying text, accessibility or signed documents matter.",
    "relatedTools": [
      "edit-pdf",
      "fill-form",
      "redact-pdf"
    ],
    "tags": [
      "Comparison",
      "PDF"
    ],
    "body": "<p>There is no meaningful editor comparison without specifying the edit. A tool can be excellent at annotation and unsuitable for changing a paragraph. A clean-looking signature stamp also says nothing about cryptographic signing.</p>\n<h2>Separate four common needs</h2>\n<ul><li><strong>Visible additions:</strong> a note, label, drawing or image placed on a page.</li><li><strong>Underlying content edits:</strong> changing the text or layout already in the file.</li><li><strong>Interactive forms:</strong> creating or filling actual fields.</li><li><strong>Removal:</strong> redacting content rather than covering it.</li></ul>\n<p>In PrivaTools these needs have separate workspaces, including <a href=\"/tool/edit-pdf\">Edit PDF</a>, <a href=\"/tool/fill-form\">Fill PDF Form</a> and <a href=\"/tool/redact-pdf\">Redact PDF</a>. Do not infer one capability from another.</p>\n<h2>Build a useful sample</h2>\n<p>Use a document with the page size, text density and features that matter to your task. Add one change near a margin, one in the middle, and one on a later page. Export it and inspect the result in another viewer.</p>\n<p>Check whether added text remains positioned correctly, whether form fields still work and whether the final file includes an unwanted watermark. Those observations are specific to your sample; they should not become a blanket claim about every file the product can process.</p>\n<h2>Inspect the processing and account requirements</h2>\n<p>Read the current workspace disclosure and vendor policy. Browser previews can accompany a server export, and AI features can have a separate destination. <a href=\"https://www.sejda.com/privacy\">Sejda’s policy</a>, for example, distinguishes file processing, other service information and shared files rather than describing everything with one retention sentence.</p>\n<h2>Choose a reversible starting point</h2>\n<p>Keep an untouched copy, make the smallest useful edit and confirm the output. If the changes require extensive reflow, return to the source document. Our <a href=\"/compare\">source-linked comparisons</a> can help you shortlist options; they are not a substitute for checking the exact work you will send.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Sejda privacy policy",
        "url": "https://www.sejda.com/privacy"
      },
      {
        "label": "PrivaTools editor workspace",
        "url": "/tool/edit-pdf"
      }
    ]
  },
  {
    "slug": "ai-pdf-summarizer-browser-2026",
    "title": "How to summarise a PDF with an on-device or provider model",
    "description": "Choose a PDF summarisation engine, understand where text goes, and check the summary against the source.",
    "publishedAt": "2026-05-15",
    "readTime": "2 min read",
    "author": "PrivaTools",
    "tldr": "PrivaTools offers an on-device summariser and a BYOK provider mode. The local mode downloads model files and computes in the browser; provider mode sends extracted text to your selected provider. Neither mode guarantees a complete or accurate summary.",
    "relatedTools": [
      "summarize-pdf",
      "ocr-pdf"
    ],
    "tags": [
      "AI",
      "PDF",
      "How-To"
    ],
    "body": "<p>A summary is useful for orientation, but it is a new piece of generated text. It can omit a qualification, confuse a number or overstate a conclusion. Keep the PDF open while you evaluate the result.</p>\n<h2>Choose the processing engine first</h2>\n<p>In <a href=\"/tool/summarize-pdf\">Summarize PDF</a>, on-device mode extracts text and runs a downloaded model in your browser. The first run needs model files, compatible browser features, storage and enough memory. The <a href=\"https://huggingface.co/docs/transformers.js/index\">Transformers.js documentation</a> describes this browser inference approach.</p>\n<p>BYOK mode instead sends extracted content to the provider you select. Your provider’s billing, usage limits and data terms apply. A personal API key does not make a remote model local.</p>\n<h2>Check that there is text to summarise</h2>\n<p>Try selecting text in the PDF. A scan may need <a href=\"/tool/ocr-pdf\">OCR</a> first. OCR introduces its own possible errors, so inspect the recognised text before asking a model to summarise it. A blank or misleading text extraction cannot produce a dependable summary.</p>\n<h2>Run a representative section</h2>\n<ol><li>Add the PDF and review the selected engine.</li><li>Choose the available summary length.</li><li>Run the summariser and watch the actual loading and processing states.</li><li>Read the result alongside the source.</li></ol>\n<p>Long documents may be chunked or limited by the engine’s context. Do not assume that every page contributed equally to the answer, and do not rely on a claimed universal processing time.</p>\n<h2>Verify before relying on the result</h2>\n<p>Check names, dates, amounts, exceptions and the document’s conclusion. If a summary is intended for another person, label it as a summary and include a route back to the source. For information where an error would matter, the source document remains the reference.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Transformers.js browser inference",
        "url": "https://huggingface.co/docs/transformers.js/index"
      },
      {
        "label": "PrivaTools summariser",
        "url": "/tool/summarize-pdf"
      }
    ]
  },
  {
    "slug": "ilovepdf-alternatives-2026",
    "title": "Looking for an iLovePDF alternative? Start with the task",
    "description": "Choose an alternative by the specific PDF operation, required workflow and acceptable processing location.",
    "publishedAt": "2026-05-15",
    "readTime": "2 min read",
    "author": "PrivaTools",
    "tldr": "Identify what you want to change: a task restriction, an output capability, a processing path or the interface. Then compare that exact requirement with current product information and a sample file.",
    "relatedTools": [
      "merge-pdf",
      "compress-pdf",
      "markdown-html"
    ],
    "tags": [
      "Comparison",
      "PDF"
    ],
    "body": "<p>You do not need to replace an entire PDF toolkit because one task did not fit. It may be enough to use a different editor, a browser utility for a small job, or a desktop workflow for files that must stay within an approved environment.</p>\n<h2>Name the problem before the alternative</h2>\n<p>Write a short requirement such as “extract two pages without creating an account” or “fill existing form fields and keep them editable.” Avoid requirements like “more powerful,” which are difficult to test and easy for marketing copy to satisfy.</p>\n<h2>Compare the same workflow</h2>\n<p>Check the starting file type, the operation and the final output. A tool that accepts a PDF and produces a flattened picture is not equivalent to one that preserves selectable text. A browser-local feature and a cloud feature may also solve different privacy requirements.</p>\n<p>Read <a href=\"https://www.ilovepdf.com/help/security\">iLovePDF’s own security information</a> for its processing description. Use the <a href=\"/compare/ilovepdf\">PrivaTools and iLovePDF comparison</a> for a source-linked overview. This guide does not claim a comparative benchmark or repeat a fixed plan quota.</p>\n<h2>When PrivaTools is worth trying</h2>\n<p>PrivaTools combines PDF workspaces with image, text and developer tools. Its interactive file tools are available without an account, while account features and API credentials have their own sign-in requirements. It uses a mixture of browser and server processing, disclosed per tool.</p>\n<p>Start with <a href=\"/tool/merge-pdf\">Merge PDF</a> for a document bundle, <a href=\"/tool/compress-pdf\">Compress PDF</a> for a smaller copy, or <a href=\"/tools/markdown-html\">Markdown Editor &amp; HTML</a> for local text work.</p>\n<h2>Keep the final decision evidence-based</h2>\n<p>Run a small non-sensitive sample through the candidate workflow. Check layout, output properties and the current limits. If an existing product already fits the task and your privacy requirements, changing tools may add work without improving the outcome.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "iLovePDF security information",
        "url": "https://www.ilovepdf.com/help/security"
      },
      {
        "label": "PrivaTools versus iLovePDF",
        "url": "/compare/ilovepdf"
      }
    ]
  },
  {
    "slug": "redact-pdf-permanently-guide",
    "title": "A practical checklist for checking PDF redactions",
    "description": "Review redacted output for underlying text, repeated information, metadata and attachments before sending the final copy.",
    "publishedAt": "2026-05-15",
    "readTime": "2 min read",
    "author": "PrivaTools",
    "tldr": "Inspect the exported file, not just the editor preview. Check visible regions, text extraction, repeated references and other document content; a successful apply message does not certify that every sensitive detail was found.",
    "relatedTools": [
      "redact-pdf",
      "smart-redact",
      "pdf-to-text",
      "strip-metadata"
    ],
    "tags": [
      "PDF",
      "Privacy",
      "Redaction",
      "Security"
    ],
    "body": "<p>The first guide in a redaction workflow is about selecting regions. This one is about reviewing what leaves your hands. Treat the downloaded PDF as a new document and verify it independently from the editing screen.</p>\n<h2>Check the visible result</h2>\n<p>Open the final file in another viewer. Inspect every changed page at a useful zoom. Look for a missed character at the edge of a region and for an overly large region that removes a neighbouring label. Confirm that the page order and other required content remain intact.</p>\n<h2>Check the text behind the appearance</h2>\n<p>Search for the sensitive value and common variations. Try copying text around the redacted area. Use <a href=\"/tool/pdf-to-text\">PDF to Text</a> to inspect the extracted text, remembering that this is itself a server-processing operation.</p>\n<p>A scan can contain visible text in an image and a separate OCR text layer. A drawing tool’s rectangle can conceal the image while leaving text searchable. <a href=\"https://pymupdf.readthedocs.io/en/latest/page.html#Page.apply_redactions\">Applied redactions have separate considerations for text, images and graphics</a>; that is why the removal tool and the output review both matter.</p>\n<h2>Check places outside the selected page</h2>\n<ul><li>Repeated names or identifiers in headers, footers and later pages.</li><li>Document properties such as title, author and subject.</li><li>Comments, annotations, form values and bookmarks.</li><li>Embedded attachments and earlier copies included in the delivery folder.</li></ul>\n<p><a href=\"/tool/strip-metadata\">Strip PDF Metadata</a> can help with document properties. It is a separate step and does not remove visible sensitive text. Use it deliberately rather than assuming any one tool is a complete disclosure review.</p>\n<h2>Separate detection from approval</h2>\n<p><a href=\"/tool/smart-redact\">Smart Redact</a> can help propose candidates. Read the selected engine’s disclosure, inspect its suggestions and approve only the intended regions. Language, layout and unusual identifiers can affect detection, so absence from a suggestion list is not evidence of absence from the document.</p>\n<h2>Deliver the reviewed version</h2>\n<p>Download the final output after all changes, reopen that exact copy and use a clear filename. Keep the unredacted original in an appropriate separate location. For work with mandatory disclosure rules, use the review process required by your organisation.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PyMuPDF redaction behaviour",
        "url": "https://pymupdf.readthedocs.io/en/latest/page.html#Page.apply_redactions"
      }
    ]
  },
  {
    "slug": "online-pdf-tools-tracking-you",
    "title": "How to evaluate privacy claims in online PDF tools",
    "description": "Separate file processing, analytics, account information and AI provider calls when judging an online tool’s privacy.",
    "publishedAt": "2026-05-15",
    "readTime": "2 min read",
    "author": "PrivaTools",
    "tldr": "Ask specific questions about file contents and other service data. Uploading a file is not automatically tracking, and a no-upload tool can still make ordinary network requests. Read the feature’s disclosure rather than inferring motives.",
    "relatedTools": [],
    "tags": [
      "Privacy",
      "PDF",
      "Security",
      "Tracking"
    ],
    "body": "<p>A file tool can process a document on a server, keep local preferences in your browser and use an identity provider for sign-in. Those are different data flows. Describing all of them as “tracking” obscures the choice you actually need to make.</p>\n<h2>Separate content from service information</h2>\n<p>The PDF itself, extracted text and audio are content. Account identifiers, request status and saved settings are other categories. Ask what is collected in each category, why it is needed and how it is retained.</p>\n<p>Do not infer from vague wording that a document is definitely used for model training. Find the relevant policy clause or ask the provider. Likewise, do not assume a privacy badge proves a specific processing path.</p>\n<h2>Check the selected operation</h2>\n<p>A local preview can be followed by a server export. A browser AI interface can send document text to a model provider. Some on-device models download software before processing local content. Each case has a different answer to “what leaves this device?”</p>\n<h2>What PrivaTools discloses</h2>\n<p>PrivaTools uses browser computation, backend file processing and direct chosen-provider AI calls. These distinctions appear in tool workspaces and the <a href=\"/trust\">trust center</a>. Its server cleanup handles temporary processing files; it does not erase downloaded output or make all service information disappear.</p>\n<p>The <a href=\"/privacy\">privacy information</a> covers account and browser data separately. My Stuff and Vault should not be assumed to synchronise merely because you have signed in.</p>\n<h2>Make a decision you can explain</h2>\n<p>For an ordinary public document, convenient server processing may fit your needs. For restricted material, an approved local or controlled environment may be required. The right conclusion depends on the document and your obligations, not a sweeping claim that every online tool has the same motives.</p>\n<p>Use <a href=\"/blog/reading-privacy-policies\">the five-question policy checklist</a> to compare the statements that matter.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools privacy information",
        "url": "/privacy"
      },
      {
        "label": "PrivaTools processing information",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "heic-conversion-guide-2026",
    "title": "How to convert HEIC photos to JPG, PNG or PDF",
    "description": "Choose a compatible format for HEIC photos and check orientation, colour, transparency and page layout after conversion.",
    "publishedAt": "2026-05-15",
    "readTime": "2 min read",
    "author": "PrivaTools",
    "tldr": "Use JPG for a widely compatible photo, PNG when you need its image characteristics, and PDF to package an image as a document. Keep the original HEIC file and inspect the converted result.",
    "relatedTools": [
      "image-converter",
      "heic-to-pdf"
    ],
    "tags": [
      "HEIC",
      "Image",
      "Conversion",
      "How-To"
    ],
    "body": "<p>A HEIC photograph may open easily on the device that created it and fail in a form, an older image editor or a recipient’s workflow. Converting a copy solves a compatibility problem without throwing away the original.</p>\n<h2>Choose the output for the job</h2>\n<ul><li><strong>JPG:</strong> a practical choice for ordinary photographs and upload forms that ask for JPEG.</li><li><strong>PNG:</strong> useful when that exact format is required, but it can make a photo much larger.</li><li><strong>PDF:</strong> useful for an image that belongs in a document bundle or printable page.</li></ul>\n<p>Apple explains HEIF/HEVC compatibility and export behaviour in its <a href=\"https://support.apple.com/en-us/116944\">format support guide</a>. A format conversion should still be checked in the application that will consume the result.</p>\n<h2>Convert and inspect</h2>\n<ol><li>Open <a href=\"/tools/image-converter\">Image Format Converter</a> for JPG or PNG, or <a href=\"/tool/heic-to-pdf\">HEIC to PDF</a> for a document.</li><li>Add the HEIC file and read the current server-processing notice.</li><li>Choose the supported output settings and run the conversion.</li><li>Open the result and inspect orientation, colours and edges.</li></ol>\n<h2>A PDF needs a layout decision</h2>\n<p>An image file has pixel dimensions; a PDF page also has a physical size. Fit, margins and orientation determine how the photo sits on the page. A long receipt and a landscape photograph will not benefit from the same layout.</p>\n<p>Check whether the chosen setting crops the image or fits all of it inside the page. For a receipt, keep every line legible and visible rather than using a visually tidy crop.</p>\n<h2>Keep expectations realistic</h2>\n<p>Converting a blurry photo does not restore detail that was never captured. Converting a compressed image to PNG does not undo earlier compression. Metadata, colour profiles and other format features may not survive the conversion unchanged, so retain the source if those properties matter.</p>\n<p>For several photographs, test one representative file before processing the full group. That catches a wrong orientation or unsuitable format early.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Apple HEIF and HEVC support",
        "url": "https://support.apple.com/en-us/116944"
      },
      {
        "label": "PrivaTools image converter",
        "url": "/tools/image-converter"
      }
    ]
  },
  {
    "slug": "decode-jwt-tokens-safely-guide",
    "title": "How to decode a JWT without mistaking it for verification",
    "description": "Read a JWT’s visible fields safely, understand what decoding proves, and avoid treating unverified claims as trusted identity.",
    "publishedAt": "2026-05-15",
    "readTime": "2 min read",
    "author": "PrivaTools",
    "tldr": "Decoding a signed JWT shows its header and payload; it does not prove who issued it. Signature, algorithm, issuer, audience and time checks belong in a trusted verifier. Avoid using real production tokens as examples.",
    "relatedTools": [
      "jwt-decoder"
    ],
    "tags": [
      "JWT",
      "Developer",
      "Security",
      "How-To"
    ],
    "body": "<p>A JWT can look cryptic while containing information anyone holding it can read. The <a href=\"/tools/jwt-decoder\">JWT Decoder</a> is useful for inspecting a sample token, but its decoded output is not an authentication decision.</p>\n<h2>What the parts mean</h2>\n<p>A commonly encountered signed JWT uses three dot-separated parts: a header, a payload and a signature. The header describes signing information and the payload contains claims. The format can also represent encrypted tokens; do not assume every JWT is the same three-part structure. See <a href=\"https://www.rfc-editor.org/rfc/rfc7519.html\">RFC 7519</a> for the definition.</p>\n<h2>Use a sample, then read the fields</h2>\n<ol><li>Prefer a deliberately generated test token with no real account access.</li><li>Paste it into the decoder and inspect the displayed header and payload.</li><li>Check names such as <code>iss</code>, <code>aud</code>, <code>sub</code>, <code>exp</code> and <code>nbf</code> against what your own application expects.</li><li>Treat every displayed value as untrusted until a verifier accepts the token.</li></ol>\n<p>This decoder works in the browser. That does not make sharing a production token harmless: clipboard history, screen recordings, browser extensions and messages can all create extra copies.</p>\n<h2>What verification adds</h2>\n<p>A verifier needs the expected issuer’s trusted key material and a deliberately configured algorithm policy. It must also validate the claims relevant to the application. The token’s own header is not an instruction to trust an arbitrary key or algorithm. The <a href=\"https://www.rfc-editor.org/rfc/rfc8725.html\">JWT best current practices</a> explain these concerns.</p>\n<h2>Debug without spreading credentials</h2>\n<p>When reporting an authentication issue, share the error, the expected claim names and a synthetic example. Do not paste a live bearer token into an issue tracker. If a live credential has been exposed, use the issuer’s revocation or session-management process and investigate where copies may have gone.</p>\n<p>A clear decoder helps you understand a token. A correctly configured authentication library decides whether your application should accept it.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "RFC 7519: JSON Web Token",
        "url": "https://www.rfc-editor.org/rfc/rfc7519.html"
      },
      {
        "label": "RFC 8725: JWT best current practices",
        "url": "https://www.rfc-editor.org/rfc/rfc8725.html"
      }
    ]
  },
  {
    "slug": "how-local-first-works",
    "title": "What browser-local file processing does—and does not—mean",
    "description": "Understand local utilities, server tasks and AI provider calls so you can choose a processing path deliberately.",
    "publishedAt": "2026-08-14",
    "readTime": "2 min read",
    "tldr": "Browser-local processing means the selected operation computes on your device. It does not describe every tool on the website. PrivaTools uses browser, server and chosen-provider processing depending on the task and mode.",
    "relatedTools": [
      "markdown-html",
      "merge-pdf",
      "summarize-pdf"
    ],
    "tags": [
      "Engineering",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>A browser can read a file you select and compute a result without sending that file to a server. The <a href=\"https://developer.mozilla.org/en-US/docs/Web/API/File_API\">File API</a> provides access to files selected or supplied by the user. What the application does next determines whether content stays local.</p>\n<h2>Three paths exist in PrivaTools</h2>\n<ul><li><strong>Browser tools:</strong> utilities such as <a href=\"/tools/markdown-html\">Markdown Editor &amp; HTML</a> work on text in the current browser.</li><li><strong>Server tools:</strong> operations such as <a href=\"/tool/merge-pdf\">Merge PDF</a> send inputs to the backend and return an output.</li><li><strong>Provider AI:</strong> a BYOK feature sends the relevant content from the browser to the selected provider.</li></ul>\n<p>A local preview is not enough to classify the whole workflow. The final export or apply action can use a different path.</p>\n<h2>Models can need a download first</h2>\n<p>Some on-device AI features need model files before computation can begin. Downloading a model is different from uploading your document. It still needs network access, storage and compatible hardware. <a href=\"https://huggingface.co/docs/transformers.js/index\">Transformers.js documentation</a> describes browser inference and supported tasks.</p>\n<h2>Local does not mean permanently saved</h2>\n<p>A draft in a page can disappear when the tab reloads or closes. Browser caches and site data are separate from downloaded output and can be cleared or evicted. Download results you need to keep and understand what My Stuff or Vault actually stores.</p>\n<h2>Check before running</h2>\n<p>Read the workspace disclosure and, when present, the engine selector. If a task must stay inside a particular environment, use only a mode whose documented processing path meets that requirement. Do not interpret a website-wide privacy slogan as an approval for every operation.</p>\n<p>The <a href=\"/trust\">trust center</a> and <a href=\"/blog/where-your-files-go\">file processing guide</a> explain the current model in more detail.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "MDN File API",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/File_API"
      },
      {
        "label": "Transformers.js documentation",
        "url": "https://huggingface.co/docs/transformers.js/index"
      }
    ]
  },
  {
    "slug": "what-deleted-means",
    "title": "What deletion means for a server-processed file",
    "description": "Understand temporary files, response cleanup, leftover-file sweeps and the copies that a website cannot erase for you.",
    "publishedAt": "2026-07-02",
    "readTime": "2 min read",
    "tldr": "PrivaTools server tasks use temporary files and cleanup after the response, with a janitor for leftovers. Cleanup is an implementation behaviour, not a guarantee of instantaneous erasure after every failure or deletion of copies on your own device.",
    "relatedTools": [],
    "tags": [
      "Trust",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>Deleting a temporary processing file is different from deleting every trace of a website visit. It is also different from deleting the copy you downloaded. A useful explanation names the data and the lifecycle rather than using one absolute promise.</p>\n<h2>The normal server workflow</h2>\n<ol><li>The selected file is uploaded for a server-backed operation.</li><li>The service reads the input and creates the output using temporary storage.</li><li>The response returns the result to your browser.</li><li>Response cleanup removes the temporary files associated with that operation.</li></ol>\n<p>The implementation also includes a background sweep for files left behind by interrupted requests, worker failures or cleanup errors. Its timing is configurable. This is why “deleted instantly, without exception” would be an inaccurate description.</p>\n<h2>What the cleanup does not remove</h2>\n<p>Your downloaded output, original file, clipboard contents and copies in synced folders are controlled separately. A result saved to Downloads is not erased by a server cleanup. An account record or operational request log also has a different purpose and retention model from a temporary PDF.</p>\n<p>Read <a href=\"/privacy\">the privacy information</a> for those categories, and <a href=\"/my-stuff\">My Stuff</a> for browser-local choices. Deleting an account is not a way to erase every local file you have saved.</p>\n<h2>How to interpret status evidence</h2>\n<p>The <a href=\"/trust\">trust center</a> can explain the cleanup model and report available service information. Aggregate counters help describe operation; they are not a forensic certificate for a particular document or proof that an individual file was overwritten on every storage layer.</p>\n<h2>Choose the processing path first</h2>\n<p>If a document must not be uploaded, use a suitable local tool or an approved environment. A server deletion policy cannot turn an upload into a local operation. When server processing is acceptable, keep only the copies you need and check the output before sharing it.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools cleanup implementation",
        "url": "https://github.com/ethereaglehq/privatools/blob/main/backend/app/utils/cleanup.py"
      },
      {
        "label": "PrivaTools privacy information",
        "url": "/privacy"
      }
    ]
  },
  {
    "slug": "reading-privacy-policies",
    "title": "Five questions to ask a file tool’s privacy policy",
    "description": "Find out what is processed, who receives it, how long it is kept and which settings change the answer.",
    "publishedAt": "2026-05-21",
    "readTime": "2 min read",
    "tldr": "Look for the processing destination, retention, third-party providers, account data and optional storage. Read the clauses that apply to the feature you use; a short headline cannot stand in for the full workflow.",
    "relatedTools": [],
    "tags": [
      "Guides",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>You do not need to interpret every clause to identify the questions that matter for a file job. Start with the exact operation and the type of content it will receive.</p>\n<h2>What leaves the device?</h2>\n<p>Look for whether the tool sends the original file, extracted text, an image, audio or a prompt. A service can keep the original file local while transmitting its contents in another form. This is especially relevant to AI features.</p>\n<h2>Who receives it?</h2>\n<p>Distinguish the website’s own server from a separate model provider or integration. Ask whether changing the mode or connecting your own key changes the recipient. “Your key” describes credentials; it does not mean “your device does all the work.”</p>\n<h2>How long is each kind of data kept?</h2>\n<p>Temporary input files, outputs, account details, logs and support attachments are different categories. Look for exceptions involving interrupted jobs, shared links or files deliberately sent to support. Do not assume that a deletion rule for ordinary processing also covers an account or a shared document.</p>\n<h2>What choices change the behaviour?</h2>\n<p>Check optional key persistence, local model downloads, browser storage, cloud sharing and third-party connections. A default, an optional feature and an action you explicitly request can have different effects.</p>\n<h2>Does the explanation match the workspace?</h2>\n<p>In PrivaTools, read the <a href=\"/trust\">processing disclosure</a>, the current tool’s mode selector and <a href=\"/privacy\">privacy information</a> together. If something is unclear, ask about the specific operation before submitting a file that carries requirements you must meet.</p>\n<p>This checklist helps you locate relevant information. It does not certify a service for a regulated or contractual use. For that, use your organisation’s approval process and the actual terms applicable to your work.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools privacy information",
        "url": "/privacy"
      },
      {
        "label": "PrivaTools processing information",
        "url": "/trust"
      }
    ]
  },
  {
    "slug": "privatools-vs-ilovepdf",
    "title": "PrivaTools and iLovePDF: compare the workflow, not the headline",
    "description": "A decision guide for choosing between PrivaTools and iLovePDF, with processing and output checks before you move your files.",
    "publishedAt": "2026-08-20",
    "updatedAt": "2026-09-14",
    "readTime": "2 min read",
    "tldr": "Compare the exact operation, output and processing path. PrivaTools uses both browser and server tools; iLovePDF documents its own file-handling model. Current product sources belong ahead of old pricing or quota claims.",
    "relatedTools": [
      "merge-pdf",
      "compress-pdf"
    ],
    "tags": [
      "Comparison",
      "PDF"
    ],
    "author": "PrivaTools",
    "body": "<p>The useful comparison is the one that changes a decision. If both products merge your sample correctly, the next questions are where the files go, whether the workflow fits your device, and which restrictions apply to your actual job.</p>\n<h2>Begin with an input and a required output</h2>\n<p>Record the file type, page count and any properties you need to preserve. For a form, test its fields. For a report, inspect links and layout. For scanned pages, check fine lettering after any compression. A brand-level feature list cannot answer those questions.</p>\n<h2>Read processing claims literally</h2>\n<p>PrivaTools does not process every PDF locally. Many PDF operations use the backend, and some AI modes send document content to a chosen provider. Its <a href=\"/trust\">trust center</a> describes the available paths.</p>\n<p>Read <a href=\"https://www.ilovepdf.com/help/security\">iLovePDF’s security information</a> for its own description. Distinguish the web workflow from any other product or integration you use. A statement about one feature should not be stretched into a promise about every feature.</p>\n<h2>Check restrictions when you need the tool</h2>\n<p>Plans, export options and usage limits can change. Review the current feature before adding a large collection of files. PrivaTools also applies operational limits; “free to use” is not “unlimited infrastructure.”</p>\n<h2>Make a small, reversible switch</h2>\n<p>Try one non-sensitive representative document, retain the source, and inspect the output. If you regularly use multiple steps, also test how the file moves between them. A saved click is less valuable than an output that requires manual repair.</p>\n<p>The <a href=\"/compare/ilovepdf\">dedicated comparison page</a> collects current sources and a feature overview. Use this checklist alongside it to make a choice grounded in your document rather than an unsupported claim that one service is best for everyone.</p>",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "iLovePDF security information",
        "url": "https://www.ilovepdf.com/help/security"
      },
      {
        "label": "Current comparison",
        "url": "/compare/ilovepdf"
      }
    ]
  },
  {
    "slug": "privatools-vs-smallpdf",
    "title": "PrivaTools and Smallpdf: choosing for everyday file work",
    "description": "Compare an everyday PDF workflow by its output, account requirements, processing details and current plan information.",
    "publishedAt": "2026-08-24",
    "updatedAt": "2026-09-14",
    "readTime": "2 min read",
    "tldr": "Try the precise operation you need and inspect its download. Check current Smallpdf information and PrivaTools disclosures; neither visual polish nor a “free” label settles file privacy or output suitability.",
    "relatedTools": [
      "compress-pdf",
      "pdf-to-word",
      "merge-pdf"
    ],
    "tags": [
      "Comparison",
      "PDF"
    ],
    "author": "PrivaTools",
    "body": "<p>For an occasional file job, the best choice may be the one that makes the result easiest to understand. For a repeated job, a predictable workflow matters more. Start by deciding which situation you are in.</p>\n<h2>Check the complete path</h2>\n<p>Look beyond the first upload screen. Can you reach the required export? Does it preserve the structure you need? Are there extra steps between conversion, compression and download? Run the full sequence with a small sample before relying on it.</p>\n<h2>Separate an interface preference from a privacy decision</h2>\n<p>Air and Play are PrivaTools appearance choices. They use the same tool controllers and do not change a server tool into a local one. The processing label and selected engine are the relevant controls.</p>\n<p><a href=\"https://smallpdf.com/privacy\">Smallpdf’s privacy notice</a> is the primary source for its data-handling statements. PrivaTools explains its own mixed browser, server and provider routes in the <a href=\"/trust\">trust center</a>. Read the text that applies to the feature you use.</p>\n<h2>Ask what an account actually adds</h2>\n<p>PrivaTools interactive tools do not require an account. An account supports account-specific features such as API credential management; it should not be confused with a backup of browser-local data. Check the current sign-in and export requirements of any alternative instead of relying on an old comparison.</p>\n<h2>Test an output you can judge</h2>\n<p>Use a sample containing an image, a table and small text if those appear in your regular documents. Inspect the converted result at normal reading size and at a closer zoom. Check copied text or form fields when relevant.</p>\n<p>Use the <a href=\"/compare/smallpdf\">current Smallpdf comparison</a> to identify features and sources, then choose the workflow that fits your document and constraints. This guide makes no claim that the products were ranked in a shared performance test.</p>",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Smallpdf privacy notice",
        "url": "https://smallpdf.com/privacy"
      },
      {
        "label": "Current comparison",
        "url": "/compare/smallpdf"
      }
    ]
  },
  {
    "slug": "privatools-vs-sejda",
    "title": "PrivaTools and Sejda: a guide to choosing a PDF editor",
    "description": "Decide whether you need page tools, visible additions, form handling or more involved editing before comparing PDF products.",
    "publishedAt": "2026-08-27",
    "updatedAt": "2026-09-14",
    "readTime": "2 min read",
    "tldr": "Choose by the edit you need and the properties the export must preserve. Read the current Sejda sources and PrivaTools processing disclosure, then test a representative document rather than relying on an old task quota.",
    "relatedTools": [
      "edit-pdf",
      "fill-form",
      "organize-pages"
    ],
    "tags": [
      "Comparison",
      "PDF"
    ],
    "author": "PrivaTools",
    "body": "<p>An editor comparison becomes much clearer when you replace “edit this PDF” with a specific action. Adding a note, filling an existing field and reflowing a paragraph are different jobs.</p>\n<h2>Describe the edit precisely</h2>\n<p>List what should change and what must remain. Do you need a typed annotation, editable form values, page order changes or a new document layout? PrivaTools exposes separate workspaces for <a href=\"/tool/edit-pdf\">editing</a>, <a href=\"/tool/fill-form\">form filling</a> and <a href=\"/tool/organize-pages\">page organisation</a>.</p>\n<h2>Inspect the exported file</h2>\n<p>Make a small change on a non-sensitive sample, download it and open it elsewhere. Check positioning, text selection and form behaviour. If you are replacing a source-editing workflow, include a difficult paragraph or table in your sample rather than choosing the easiest possible page.</p>\n<h2>Read the right privacy section</h2>\n<p><a href=\"https://www.sejda.com/privacy\">Sejda’s privacy policy</a> distinguishes uploaded files, shared files, remembered browser data and other service information. Check the section matching your workflow. A general retention sentence is not the whole story when sharing or AI features are involved.</p>\n<p>PrivaTools also needs a task-specific reading: a page preview can be local while an apply operation uses the server. Account settings and local saved data are separate from file-processing output.</p>\n<h2>Check today’s limits</h2>\n<p>A frequently repeated quota from an old article may not describe your selected product or feature today. Read the current limits before planning a larger job, including any page, size or usage restriction.</p>\n<p>The <a href=\"/compare/sejda\">dedicated comparison</a> links to current sources. Use it to narrow the choice, then let your own output check decide whether the editing workflow meets the need.</p>",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Sejda privacy policy",
        "url": "https://www.sejda.com/privacy"
      },
      {
        "label": "Current comparison",
        "url": "/compare/sejda"
      }
    ]
  },
  {
    "slug": "privatools-vs-ihatepdf",
    "title": "PrivaTools and ihatepdf: check what “local” means for each tool",
    "description": "Compare browser processing and AI content transfer without assuming that a raw PDF staying local means no information is transmitted.",
    "publishedAt": "2026-08-30",
    "updatedAt": "2026-09-14",
    "readTime": "2 min read",
    "tldr": "A raw file can stay in the browser while extracted text is sent to an AI provider. Compare each selected tool and mode: ihatepdf documents this distinction for PDF chat, and PrivaTools BYOK chat also sends document text to the chosen provider.",
    "relatedTools": [
      "chat-with-pdf",
      "summarize-pdf",
      "merge-pdf"
    ],
    "tags": [
      "Comparison",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>“Local” is useful only when it tells you what happens to the information you care about. Keeping a PDF container on your laptop is different from keeping every word inside that PDF on your laptop.</p>\n<h2>Ask about the content, not just the file</h2>\n<p>ihatepdf’s <a href=\"https://www.ihatepdf.cv/chat-with-pdf\">PDF chat page</a> states that it extracts text locally and sends the extracted content to Google Gemini. The raw PDF and the text therefore have different processing paths. This is a concrete example of why a broad no-upload headline needs a feature-level reading.</p>\n<p>PrivaTools <a href=\"/tool/chat-with-pdf\">PDF chat</a> follows a similar distinction with a chosen BYOK provider: text extraction happens in the browser, then document text and questions go to that provider. It is not an on-device chat model.</p>\n<h2>Compare ordinary tools separately</h2>\n<p>A browser-based merge or formatting tool does not imply that every AI feature is local. Conversely, an AI feature that sends text does not mean all ordinary tools send files. Check the exact workspace you are about to run.</p>\n<p>PrivaTools has many backend PDF operations as well as local utilities. Its <a href=\"/trust\">processing information</a> separates those paths, and its mode selectors can change the destination of content in supported AI tools.</p>\n<h2>Choose a meaningful sample</h2>\n<p>Use non-sensitive content with a structure similar to your real document. Check the output and the selected processing mode. If your requirement is that document content must not reach a remote provider, exclude remote AI modes even if they do not upload the original file.</p>\n<h2>Use the comparison as a starting point</h2>\n<p>The <a href=\"/compare/ihatepdf\">current comparison page</a> links to the product sources. Keep those details separate from personal preferences such as layout, number of clicks or theme. Both kinds of consideration matter, but they answer different questions.</p>",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "ihatepdf PDF chat processing disclosure",
        "url": "https://www.ihatepdf.cv/chat-with-pdf"
      },
      {
        "label": "Current comparison",
        "url": "/compare/ihatepdf"
      }
    ]
  },
  {
    "slug": "chat-with-pdf-free-private",
    "title": "How PDF chat handles your document text",
    "description": "Use PDF chat with your own provider key, inspect extracted text, and understand what is sent with a question.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "PrivaTools PDF chat extracts text in the browser, then sends document text and your question directly to the BYOK provider. The raw file does not pass through PrivaTools, but the content is transmitted to the selected provider.",
    "relatedTools": [
      "chat-with-pdf",
      "summarize-pdf",
      "ocr-pdf"
    ],
    "tags": [
      "AI",
      "PDF",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>PDF chat is helpful for asking a focused question about a document you are reading. It is also a data-transfer decision: an AI answer requires the chosen model to receive the relevant content.</p>\n<h2>Understand the current chat mode</h2>\n<p><a href=\"/tool/chat-with-pdf\">Chat with PDF</a> uses a provider connected through your own key. It is not the same as the separate on-device summariser. The PDF is read locally, but extracted text and conversation content go to the selected endpoint.</p>\n<p>Review the provider, endpoint, model and data policy before using confidential material. A self-hosted endpoint is controlled by whoever operates that endpoint; it is not automatically on the same device as the browser.</p>\n<h2>Inspect the extracted text</h2>\n<p>Add a PDF and expand the extracted-text review. Check that headings, numbers and relevant paragraphs are present. Scanned pages can need OCR, and unusual layouts can produce a different reading order from the visual page.</p>\n<h2>Ask a question you can verify</h2>\n<p>Start with a bounded request: “List the deadlines in the document” or “Explain the difference between these two sections.” Then compare the answer with the source. Model responses are not proof of the facts they assert, and a confident answer can still be wrong.</p>\n<p>Very long text may exceed context limits or be truncated. If the relevant section is not in the supplied text, reframe the input or review it directly rather than treating the answer as a complete search of the original.</p>\n<h2>Keep the useful result</h2>\n<p>Copy an answer you want to retain and record which document it came from. Do not treat the conversation as a synced account archive. If your requirement is that content must stay on-device, choose an appropriate local feature, such as <a href=\"/tool/summarize-pdf\">the on-device summariser</a>, rather than the provider chat mode.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools PDF chat disclosure",
        "url": "/tool/chat-with-pdf"
      },
      {
        "label": "AI connection settings",
        "url": "/ai"
      }
    ]
  },
  {
    "slug": "ai-pdf-tools-no-upload-byok",
    "title": "On-device AI and BYOK: two different processing choices",
    "description": "Understand the difference between downloading a model to your browser and sending document content to a provider using your own key.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "On-device AI computes in your browser after loading its model. BYOK calls your selected provider with your content. Both give you a choice, but only the on-device mode keeps that computation local.",
    "relatedTools": [
      "summarize-pdf",
      "translate-pdf",
      "transcribe-audio"
    ],
    "tags": [
      "AI",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>“Bring your own key” and “run on your device” solve different problems. The first gives you control of provider credentials. The second describes where computation happens.</p>\n<h2>What an on-device model needs</h2>\n<p>A local AI feature downloads model files and runs inference using browser capabilities. That can require substantial storage and memory, and supported tasks depend on the model. A model being available in a catalogue is not a guarantee that every device can run it well.</p>\n<p>PrivaTools includes local options in selected features such as summarisation, translation and transcription. Check the actual engine selector. <a href=\"https://huggingface.co/docs/transformers.js/index\">Transformers.js</a> is one of the technologies used for browser inference.</p>\n<h2>What a provider receives</h2>\n<p>A BYOK request sends the task input to the configured endpoint: document text for a text model, or audio for a supported transcription provider. Provider terms, billing and rate limits apply. Sending extracted text instead of the PDF container still sends the document’s content.</p>\n<h2>Choose per task</h2>\n<ul><li>Use a supported local mode when keeping content on-device is a requirement and your device can run the model.</li><li>Use a provider mode when that transfer is acceptable and the model fits the task.</li><li>Use a non-AI tool when a deterministic operation, such as text extraction, already answers the need.</li></ul>\n<h2>Inspect the connection before running</h2>\n<p>In <a href=\"/ai\">AI Studio</a>, check the provider and any custom endpoint. Start with non-sensitive sample content, and do not publish your key in screenshots or shared settings. A successful connection is not evidence that generated answers are correct.</p>\n<p>For both modes, verify output against the source. Changing the computation location changes the data path; it does not eliminate model mistakes.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Transformers.js documentation",
        "url": "https://huggingface.co/docs/transformers.js/index"
      },
      {
        "label": "PrivaTools AI Studio",
        "url": "/ai"
      }
    ]
  },
  {
    "slug": "remove-background-without-uploading",
    "title": "How to remove an image background on your device",
    "description": "Select the on-device background remover deliberately, then inspect the cutout and transparency before downloading.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "Background Remover supports server and on-device engines. Select “On this device” before running if you want local processing; the current default is the server engine. The local model needs an initial download.",
    "relatedTools": [
      "remove-background",
      "image-converter",
      "resize-crop-image"
    ],
    "tags": [
      "Images",
      "Privacy",
      "How-To"
    ],
    "author": "PrivaTools",
    "body": "<p>Removing a background is a model-based cutout, not a simple colour deletion. Hair, transparent objects, shadows and edges that blend into the scene can all need close inspection.</p>\n<h2>Select the engine before processing</h2>\n<p>Open <a href=\"/tools/remove-background\">Background Remover</a> and inspect “Where to process.” The current default uses the server. Switch to “On this device” for local model processing before you run the task.</p>\n<p>The local engine needs model files the first time it runs. A download or model-startup delay is different from an upload of the selected photograph. It still depends on browser support, memory and available storage.</p>\n<h2>Start with one representative photograph</h2>\n<ol><li>Choose a supported image with the kind of subject you plan to process.</li><li>Run the selected engine and wait for the actual result.</li><li>Inspect the outline around hair, hands, straps and small gaps.</li><li>Download the cutout and view it against a contrasting background.</li></ol>\n<p>A cutout can look clean on a checkerboard and show a halo on a dark background. Review it in the context where you plan to use it.</p>\n<h2>Choose an output that preserves what you need</h2>\n<p>If the result uses transparency, keep a format that supports it. Converting the cutout to JPEG requires a background because JPEG does not preserve an alpha channel. Do not assume a white area in an image viewer is necessarily an opaque white background.</p>\n<h2>When the model misses the subject</h2>\n<p>Try a clearer source or a tighter crop that still includes all of the subject. More pixels are not always more useful when the scene remains ambiguous. Keep the source image, and do not describe a failed or partly correct cutout as a completed result.</p>\n<p>For a batch, accept the result from a representative image before applying the same workflow to the full collection.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Background Remover engine selector",
        "url": "/tools/remove-background"
      }
    ]
  },
  {
    "slug": "transcribe-audio-free-no-upload",
    "title": "How to transcribe audio with a local or provider engine",
    "description": "Choose the transcription engine, check what is uploaded, and review the resulting words before using a transcript.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "Local transcription uses a downloaded model on your device. BYOK transcription sends audio to a supported provider endpoint. In either case, verify names, numbers and unclear speech against the recording.",
    "relatedTools": [
      "transcribe-audio"
    ],
    "tags": [
      "AI",
      "Audio",
      "How-To"
    ],
    "author": "PrivaTools",
    "body": "<p>A transcript makes a recording easier to search and review. It can also introduce plausible words where the speaker was unclear. Treat the first output as a draft that needs listening checks.</p>\n<h2>Choose where the audio is processed</h2>\n<p><a href=\"/tools/transcribe-audio\">Transcribe Audio</a> offers an on-device engine and a BYOK provider engine. The local option downloads a model and computes in the browser. The provider option sends the recording to the supported endpoint you choose.</p>\n<p>Not every text-model provider supports audio transcription. The workspace identifies supported choices. Check the provider’s terms and usage charges before sending a real recording.</p>\n<h2>Prepare a useful sample</h2>\n<p>Begin with a short section containing typical speech and background noise. Confirm that the file plays correctly. Choose the right language setting where available, and avoid assuming that a multilingual conversation will be handled consistently without review.</p>\n<h2>Run and review</h2>\n<ol><li>Select the engine and add the audio file.</li><li>Start transcription and wait through any model preparation.</li><li>Read the output while replaying the source.</li><li>Correct names, abbreviations, numbers and misunderstood phrases.</li><li>Download or copy the version you want to keep.</li></ol>\n<p>Processing time depends on the recording, model and device. A short successful sample does not guarantee the same experience with a long recording.</p>\n<h2>Know what the text represents</h2>\n<p>A generated transcript is not a certified record. Check whether the selected output actually includes timings or speaker labels rather than assuming these are present. If the recording contains sensitive information about other people, use the processing environment appropriate for that material.</p>\n<p>Keep the original audio until the transcript has been accepted. A transcript is useful because it is easier to navigate, but the recording remains the reference for what was said.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools transcription workspace",
        "url": "/tools/transcribe-audio"
      },
      {
        "label": "Transformers.js supported tasks",
        "url": "https://huggingface.co/docs/transformers.js/index"
      }
    ]
  },
  {
    "slug": "ocr-scanned-pdf-free-three-ways",
    "title": "OCR a scanned PDF: choose the right engine and output",
    "description": "Understand server, on-device and provider OCR options, then check recognised text and searchable output.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "OCR recognises text in page images. Choose an engine based on the output you need and an acceptable processing path; do not assume every engine returns the same searchable PDF, layout or accuracy.",
    "relatedTools": [
      "ocr-pdf",
      "pdf-to-text"
    ],
    "tags": [
      "PDF",
      "OCR",
      "How-To"
    ],
    "author": "PrivaTools",
    "body": "<p>A PDF can display readable words while containing no selectable text. OCR attempts to recognise those words. Its output can be plain text, a text layer or a recreated document, depending on the selected tool and mode.</p>\n<h2>Check whether OCR is necessary</h2>\n<p>Try selecting a sentence in the source. If it copies correctly, ordinary <a href=\"/tool/pdf-to-text\">text extraction</a> may be enough. If it selects nothing, or produces broken text, inspect the source and consider <a href=\"/tool/ocr-pdf\">OCR PDF</a>.</p>\n<h2>Choose an engine deliberately</h2>\n<p>The OCR workspace exposes server, local and BYOK options. The server receives the PDF for its OCR workflow. Local recognition uses browser-loaded resources. Provider mode sends the relevant page content to the chosen provider. Read the output description for the selected mode before you rely on a searchable PDF being produced.</p>\n<h2>Improve the source before recognition</h2>\n<p>Rotation, skew, low resolution and a noisy background can reduce recognition quality. Correct the obvious problems in a copy and test a representative page. The <a href=\"https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html\">Tesseract quality guide</a> explains how input quality and page segmentation affect recognition.</p>\n<h2>Verify a difficult page</h2>\n<p>Check a page containing small text, columns, a table or numbers. Compare the recognised output with the visible source. A correct paragraph does not mean a nearby account number, decimal point or name was recognised correctly.</p>\n<p>If the output is a PDF with a text layer, search for a known phrase and copy it. If it is text, inspect the reading order and missing sections. Preserve the original scan alongside any accepted transcription.</p>\n<h2>Use OCR as preparation, not proof</h2>\n<p>Summarisation, search and translation can all depend on OCR text. Correcting a recognition error early prevents it from being repeated or amplified later in the workflow.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "Tesseract input-quality guidance",
        "url": "https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html"
      },
      {
        "label": "PrivaTools OCR engine choices",
        "url": "/tool/ocr-pdf"
      }
    ]
  },
  {
    "slug": "translate-pdf-free-private",
    "title": "How to translate PDF text and choose its processing path",
    "description": "Extract readable text, select an on-device or provider translation engine, and review meaning and missing content.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "PrivaTools translation has local and BYOK modes. Local models support specific language pairs; a provider mode sends extracted text to the chosen endpoint. The result is a translation of extracted text, not a promise to preserve the original PDF layout.",
    "relatedTools": [
      "translate-pdf",
      "ocr-pdf",
      "pdf-to-text"
    ],
    "tags": [
      "AI",
      "PDF",
      "How-To"
    ],
    "author": "PrivaTools",
    "body": "<p>Translating a document has two separate challenges: extracting the right text and expressing its meaning in another language. A page can be visually clear while producing a poor text extraction, especially when it contains columns, scans or tables.</p>\n<h2>Start with the source text</h2>\n<p>Open <a href=\"/tool/translate-pdf\">Translate PDF</a> and add the document. Check that the relevant text can be read. Scanned pages may need OCR first; inspect that output before treating it as an accurate source for translation.</p>\n<h2>Choose the engine and languages</h2>\n<p>The local option uses downloaded models for the supported language pairs. The BYOK option sends extracted text to the provider and model you select. Available pairs, quality and context limits differ, so check the controls in the current workspace.</p>\n<p>A provider request still transmits content even if the PDF container was read on your device. Review the selected endpoint and its terms before processing sensitive text.</p>\n<h2>Review meaning, not just fluency</h2>\n<p>A fluent paragraph can contain a wrong negation, date, product name or instruction. Compare important passages with the original, and use a qualified reviewer when your use requires a reliable translation.</p>\n<p>Keep tables, formulas and specialised terminology on a separate review list. Missing text in extraction cannot be restored simply by selecting a larger language model.</p>\n<h2>Expect a text-oriented result</h2>\n<p>This workflow translates extracted content. It is not a general layout-preserving replacement for a document-production tool. Inspect the available output and rebuild the layout in an appropriate source editor if page structure matters.</p>\n<h2>Keep a traceable pair</h2>\n<p>Save the source and the reviewed translation with clear names. Record which language and engine you used so another person can understand how the draft was made. Do not label an unreviewed generated output as a certified translation.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools translation workspace",
        "url": "/tool/translate-pdf"
      }
    ]
  },
  {
    "slug": "bring-your-own-ai-key-guide",
    "title": "Bring your own AI key: a careful setup guide",
    "description": "Connect a supported AI provider, choose key persistence deliberately, and understand what the provider receives.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "Add a supported provider key in AI Studio, verify the endpoint and model, and try non-sensitive sample input. BYOK sends content to that provider; its billing and data policy apply. Save the key in this browser only if that suits your device.",
    "relatedTools": [
      "chat-with-pdf",
      "summarize-pdf",
      "transcribe-audio"
    ],
    "tags": [
      "AI",
      "Developer",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>A provider key authorises requests to your AI account. Treat it as a credential. Do not paste it into a public issue, commit it to a repository or include it in screenshots of your settings.</p>\n<h2>Start at the provider</h2>\n<p>Create an appropriate credential using the provider’s own account controls. Check the usage budget and available permissions there. A PrivaTools account and an AI provider account are separate; signing into one does not grant access to the other.</p>\n<h2>Configure the connection</h2>\n<ol><li>Open <a href=\"/ai\">AI Studio</a> or the connection panel in an AI workspace.</li><li>Select the supported provider and enter the key.</li><li>If using a custom endpoint, verify its address and who operates it.</li><li>Choose whether the browser should remember the credential where that option is offered.</li><li>Run a small task with non-sensitive sample content.</li></ol>\n<h2>Understand persistence</h2>\n<p>A session-only key and a key remembered in browser storage have different lifetimes. Read the choice shown in the connection panel. Remembering a credential on a shared device is a different decision from using it briefly on a private one.</p>\n<p>Removing a saved copy in the interface does not revoke the credential at the provider. Use the provider’s own controls if a key was exposed or should no longer be valid.</p>\n<h2>Know what each task sends</h2>\n<p>PDF chat sends extracted document text and questions. Supported transcription providers receive audio. Other modes have their own inputs. A personal key gives control over the provider account; it does not eliminate transmission or provider-side processing.</p>\n<h2>Diagnose without exposing the key</h2>\n<p>Check the provider, model identifier, endpoint and task support. A text endpoint may not support audio. Record the error and approximate request time when asking for help, but redact credentials and private content. The <a href=\"/support\">support page</a> explains how to report a problem without attaching the original file unnecessarily.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools AI connection controls",
        "url": "/ai"
      },
      {
        "label": "PrivaTools support",
        "url": "/support"
      }
    ]
  },
  {
    "slug": "batch-process-files-free",
    "title": "How to batch-process files without losing track of results",
    "description": "Run one supported task across several files, review partial failures and keep a clear record of the outputs.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "Batch repeats the same supported operation across a set of files. Test one file first, use the current queue limits, and check each result. A partly completed batch should not be treated as a complete delivery.",
    "relatedTools": [
      "compress-pdf",
      "image-converter"
    ],
    "tags": [
      "Workflow",
      "How-To"
    ],
    "author": "PrivaTools",
    "body": "<p>Batch processing saves repeated setup, but it also repeats a bad setting quickly. The most useful preparation is to accept one representative output before adding the rest of the collection.</p>\n<h2>Use Batch for one repeated operation</h2>\n<p>Open <a href=\"/batch\">Batch</a> when several compatible files need the same supported task. Use <a href=\"/pipeline\">Pipeline</a> when one document needs a sequence of compatible steps. The two workspaces solve different problems.</p>\n<h2>Prepare the queue</h2>\n<ol><li>Group files that need the same operation and settings.</li><li>Check their names and remove duplicate inputs.</li><li>Confirm that their formats match the selected task.</li><li>Read the current file-count and upload limits.</li><li>Run a small sample before the full queue.</li></ol>\n<p>Interactive tools are free to use, but the service still has operational limits, processing capacity and failure states. Do not interpret a free interface as a promise of unlimited jobs.</p>\n<h2>Review individual outcomes</h2>\n<p>Watch the per-file status as well as the overall progress. A failure in one input can leave a mixture of completed and incomplete results. Download successful outputs and retry the intended failed items rather than blindly creating a second set of every file.</p>\n<h2>Check the delivered collection</h2>\n<p>Count the outputs and open a representative sample, including any unusual input. A ZIP is a container; it does not prove that every requested conversion succeeded. Keep a simple list of source names and expected results if the job matters.</p>\n<h2>Repeat only an accepted setup</h2>\n<p>Save or reuse settings only after checking the output. If a later collection has different page sizes, image dimensions or language, test again. Continue with <a href=\"/blog/batch-or-pipeline-how-to-choose\">the Batch versus Pipeline guide</a> for choosing the right workflow.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools Batch workspace",
        "url": "/batch"
      },
      {
        "label": "PrivaTools Pipeline workspace",
        "url": "/pipeline"
      }
    ]
  },
  {
    "slug": "chatpdf-alternatives-private",
    "title": "Choosing a PDF chat alternative by its data path",
    "description": "Evaluate PDF chat by extraction quality, provider destination, context limits and answer verification.",
    "publishedAt": "2026-09-01",
    "readTime": "2 min read",
    "tldr": "Ask where document text goes, which provider receives it and what is retained. A raw PDF staying local does not make provider chat an on-device operation. Test extraction and answers with a non-sensitive sample.",
    "relatedTools": [
      "chat-with-pdf",
      "summarize-pdf"
    ],
    "tags": [
      "AI",
      "Comparison",
      "Privacy"
    ],
    "author": "PrivaTools",
    "body": "<p>A PDF chat interface combines document reading, text selection and a language model. A different product may change one of those pieces without changing the others. Compare the data path before assuming it improves privacy.</p>\n<h2>Ask four concrete questions</h2>\n<ul><li>Is the original file uploaded, or is text extracted on the device?</li><li>Where does that extracted text go when a question is sent?</li><li>Which service’s retention and usage terms apply?</li><li>Does the answer cover the full document or only the text supplied to the model?</li></ul>\n<h2>Understand the PrivaTools option</h2>\n<p><a href=\"/tool/chat-with-pdf\">PrivaTools PDF chat</a> extracts text in the browser and uses your selected BYOK provider. Document text and questions are sent to that endpoint. It is not a guarantee of zero transmission, provider retention or cost.</p>\n<p>The separate <a href=\"/tool/summarize-pdf\">summarisation workspace</a> offers an on-device mode for a different task. Summarising a document and having an open-ended provider conversation are not interchangeable features.</p>\n<h2>Test the reading step</h2>\n<p>Use a sample with a table, a heading and a later section. Inspect the extracted text before asking questions. If the reading order is wrong or a scan has no recognised words, the model is being asked to work from an incomplete source.</p>\n<h2>Test the answer</h2>\n<p>Ask for a specific detail you already know is in the document. Check the response against the source. A correct sample answer is a useful check, but it is not a performance guarantee for other documents or questions.</p>\n<h2>Make the trade-off explicit</h2>\n<p>A hosted product may offer a convenient account history or document workflow; a BYOK interface exposes more of the connection choices. Choose according to the content and features you need, and review current provider policies directly. Our <a href=\"/blog/bring-your-own-ai-key-guide\">BYOK setup guide</a> explains the PrivaTools connection choices.</p>",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools PDF chat workspace",
        "url": "/tool/chat-with-pdf"
      },
      {
        "label": "PrivaTools AI Studio",
        "url": "/ai"
      }
    ]
  },
  {
    "slug": "markdown-editor-to-html-guide",
    "publishedAt": "2026-09-14",
    "title": "From a Markdown file to a clean HTML document",
    "description": "Open an existing .md file, edit with a live preview, and export Markdown or HTML without sending the text for processing.",
    "tldr": "Open your .md file from home or in Markdown Editor & HTML, review the live preview, and save the format you need. This editor works in the browser. Its supported Markdown subset is deliberately smaller than a full publishing system.",
    "body": "<p>You may already have the right starting point: meeting notes in a <code>.md</code> file, a project readme or a short guide written in plain text. You can turn that into readable HTML without rebuilding the document in a visual editor.</p>\n<h2>Open the file you already have</h2>\n<p>On the PrivaTools home page, choose <strong>Start with a file</strong> and select a Markdown file. Choose <strong>Markdown Editor &amp; HTML</strong> from the suggested tasks. The selected file is handed to the editor, where you can read and change it before exporting.</p>\n<p>You can also open <a href=\"/tools/markdown-html\">the editor directly</a> and choose <strong>Open .md</strong>. It accepts supported Markdown and plain-text files up to the limit shown by the tool. It does not automatically turn a file selection into a server-processing request.</p>\n<h2>Give the document a simple structure</h2>\n<p>Use one main heading to name the document, then second-level headings to divide it into useful sections. Write paragraphs with blank lines between them. Use a list when the items are genuinely parallel or sequential, rather than turning every sentence into a bullet.</p>\n<pre><code># A useful project note\n\nA short explanation of what this document helps someone do.\n\n## Before you start\n\n- Keep the original file\n- Check the required output\n\n## Next step\n\nRead the **preview**, then save your work.</code></pre>\n<p>The <a href=\"https://commonmark.org/help/\">CommonMark reference</a> explains the basic heading, emphasis, list and code notation. The PrivaTools editor supports common blocks and inline formatting, but it does not claim full CommonMark conformance or support for every Markdown extension.</p>\n<h2>Use the preview as a check</h2>\n<p>The writing pane and preview stay together in the split view. Use the formatting controls for a heading, emphasis, a list, code or a link. Then check the result. A missing space after a heading marker or an unmatched formatting marker can make a document look different from what you intended.</p>\n<p>The preview treats raw HTML as text and runs inside a restricted frame. It cannot load remote content or run scripts. This makes it suitable for reviewing the supported text formatting; it is not a preview of an arbitrary website with its own JavaScript, remote images or custom styles.</p>\n<h2>Choose the right export</h2>\n<ul><li><strong>Save Markdown</strong> keeps the editable plain-text source. Use it when you want to continue writing later.</li><li><strong>Download .html</strong> saves an HTML document containing the generated content.</li><li><strong>Copy HTML</strong> is useful when you want the generated markup for another editor or publishing workflow.</li></ul>\n<p>Check the exported HTML in its destination. The receiving website’s styles can change typography and spacing. A Markdown preview is not a promise that every publishing platform will render the same layout.</p>\n<h2>Keep a copy before leaving</h2>\n<p>Air, Play and the light/dark controls change the workspace’s appearance while keeping the current editor mounted. Reloading or closing the tab is a different action: do not treat an unsaved draft as a durable backup. Save the Markdown file you want to keep.</p>\n<p>If you need a fixed-page document instead, use <a href=\"/tool/markdown-to-pdf\">Markdown to PDF</a>. That is a separate server-backed conversion. Our <a href=\"/blog/markdown-to-pdf-layout-checklist\">PDF layout checklist</a> explains what to review after that export.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "CommonMark syntax reference",
        "url": "https://commonmark.org/help/"
      },
      {
        "label": "PrivaTools Markdown editor",
        "url": "/tools/markdown-html"
      }
    ],
    "relatedTools": [
      "markdown-html",
      "markdown-to-pdf"
    ],
    "tags": [
      "Markdown",
      "How-To",
      "Documents"
    ],
    "readTime": "3 min read"
  },
  {
    "slug": "markdown-to-pdf-layout-checklist",
    "publishedAt": "2026-09-14",
    "title": "Turn Markdown into a PDF you can actually share",
    "description": "Prepare a Markdown document for fixed pages, convert it, and review headings, code, links and page breaks before sending it.",
    "tldr": "Keep the Markdown source, convert a copy with Markdown to PDF, then review the downloaded pages. The editor’s local HTML preview and the server-generated PDF are different outputs with different layout and privacy considerations.",
    "body": "<p>A Markdown document is organised by meaning: headings, paragraphs, lists and code. A PDF adds pages with fixed boundaries. A note that reads well in a scrolling preview can still split a heading from its paragraph or place a long code line outside a comfortable reading width.</p>\n<h2>Prepare the source</h2>\n<p>Open the file in <a href=\"/tools/markdown-html\">Markdown Editor &amp; HTML</a> or your usual text editor. Check the title, heading order and the spelling of links. Remove any internal notes or placeholder values that should not appear in the shared version.</p>\n<p>Save the edited <code>.md</code> file before converting. The Markdown remains the best place to make later changes; editing the exported PDF can become a patchwork that is harder to maintain.</p>\n<h2>Choose the PDF conversion deliberately</h2>\n<p>Open <a href=\"/tool/markdown-to-pdf\">Markdown to PDF</a>, or choose it from the home page’s suggestions after selecting the file. Read the server-processing disclosure, add the supported Markdown file and run the conversion.</p>\n<p>This is different from the browser-only Markdown editor. A local editor session does not make the subsequent PDF conversion local. If your document cannot be uploaded, use an approved local export workflow instead.</p>\n<h2>Inspect the pages, not just the first screen</h2>\n<ol><li>Check that the title and opening paragraph appear as intended.</li><li>Inspect headings close to the bottom of a page.</li><li>Look at long list items, URLs and code lines.</li><li>Confirm that the final paragraph and any appendix are present.</li><li>Try selecting text and following the links you expect to work.</li></ol>\n<p>Markdown implementations differ. Features such as complex tables, embedded HTML and custom extensions may not carry over as expected. Start with a small sample of those features rather than discovering a mismatch after converting the whole document.</p>\n<h2>Make targeted corrections</h2>\n<p>If a code block is too wide, shorten the example or split a long line in the source when that preserves its meaning. If a list becomes difficult to scan, reorganise it into smaller sections. Do not remove necessary information merely to make the page look tidy.</p>\n<p>For a document that needs detailed page design, use an authoring application that gives you the required layout controls. Markdown is convenient for structured writing; it is not always the best source for a highly art-directed form or brochure.</p>\n<h2>Share a complete pair when useful</h2>\n<p>Send the PDF to someone who needs a stable reading copy. Keep or share the Markdown source with someone who needs to maintain the document, provided its contents are appropriate to share. Give both files related names so the connection is clear.</p>\n<p>Only compress the accepted PDF if its size creates a real delivery problem, and inspect it again after compression. The <a href=\"/blog/compress-pdf-without-losing-quality\">compression guide</a> explains why a smaller result is not automatically a better one.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools Markdown-to-PDF workspace",
        "url": "/tool/markdown-to-pdf"
      },
      {
        "label": "CommonMark reference",
        "url": "https://commonmark.org/help/"
      }
    ],
    "relatedTools": [
      "markdown-to-pdf",
      "markdown-html",
      "compress-pdf"
    ],
    "tags": [
      "Markdown",
      "PDF",
      "How-To"
    ],
    "readTime": "2 min read"
  },
  {
    "slug": "passkeys-and-optional-accounts",
    "publishedAt": "2026-09-14",
    "title": "Use PrivaTools with—or without—an account",
    "description": "Understand which features need sign-in, how passkeys work, and why account access is separate from browser-local files and settings.",
    "tldr": "You can use interactive file tools without signing in. An account supports account-specific features such as API key management. Passkeys are an optional sign-in method when enabled, and signing in does not turn local drafts or Vault data into a cloud backup.",
    "body": "<p>An account should have a clear job. If you only want to merge a PDF or edit a Markdown note, PrivaTools lets you start with the task. Sign-in becomes relevant when you want an account-specific capability, such as creating or revoking your API credentials.</p>\n<h2>Separate three kinds of state</h2>\n<table><thead><tr><th>What you are using</th><th>What to remember</th></tr></thead><tbody><tr><td>A file tool</td><td>Check its processing disclosure. Being signed in does not change where that operation runs.</td></tr><tr><td>An account</td><td>It manages identity and account features, including API credentials.</td></tr><tr><td>Browser-local data</td><td>Preferences, drafts and locally saved items are not automatically a synced account archive.</td></tr></tbody></table>\n<p>Air and Play are appearance choices. Changing them keeps the active tool state, while closing a tab, clearing site data or switching devices has different consequences. Download results you need to retain.</p>\n<h2>Choose a sign-in method that fits</h2>\n<p>The sign-in page shows the methods enabled for this deployment, such as a provider, email and password, or an existing passkey. An optional username can be used where supported; it must satisfy the current account rules and be available when saved.</p>\n<p>If your account was created through a provider and has no password, settings shows an email setup/recovery route rather than asking for a current password that does not exist. Use the method actually associated with your account.</p>\n<h2>What a passkey does</h2>\n<p>A passkey uses public-key authentication through the browser. Your device or password manager may ask for a screen lock, a security key or biometric confirmation. The website checks the resulting authentication proof; it does not receive your fingerprint or face scan. <a href=\"https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API\">MDN’s WebAuthn documentation</a> explains the mechanism and secure-context requirement.</p>\n<p>Passkeys can have device and domain restrictions. Having one for another website does not mean it can sign you into PrivaTools. A browser prompt that offers no matching credential is not proof that your account has been deleted.</p>\n<h2>Add and manage a passkey</h2>\n<ol><li>Sign into your account using an available method.</li><li>Open <a href=\"/account/settings\">Account settings</a> and find saved passkeys.</li><li>Choose <strong>Add a passkey</strong> and follow the browser’s actual prompt.</li><li>Give the saved key a name you can recognise.</li><li>Keep another usable sign-in method available before removing a key.</li></ol>\n<p>PrivaTools uses Clerk’s account passkey APIs for enrollment and management. <a href=\"https://clerk.com/docs/guides/development/custom-flows/authentication/passkeys\">Clerk’s documentation</a> covers creation, sign-in, rename and removal. Availability depends on the deployment and browser; cancelling the prompt does not create a passkey.</p>\n<h2>Know what removal affects</h2>\n<p>Removing a passkey from the account prevents that credential from signing in there. A copy saved in a device or password manager can need separate removal. Neither action deletes PDFs in your Downloads folder or a browser-local Vault.</p>\n<p>Visit <a href=\"/my-stuff\">My Stuff</a> for local data controls and <a href=\"/account/keys\">API keys</a> for account access credentials. Keeping these boundaries clear makes it easier to choose an account only when it adds something you need.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "MDN Web Authentication API",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API"
      },
      {
        "label": "Clerk passkey flows",
        "url": "https://clerk.com/docs/guides/development/custom-flows/authentication/passkeys"
      },
      {
        "label": "PrivaTools account settings",
        "url": "/account/settings"
      }
    ],
    "relatedTools": [],
    "tags": [
      "Accounts",
      "Privacy",
      "How-To"
    ],
    "readTime": "2 min read"
  },
  {
    "slug": "where-your-files-go",
    "publishedAt": "2026-09-14",
    "title": "Where your files go when you run a tool",
    "description": "A practical map of browser processing, server jobs and AI provider calls, plus the difference between selected, uploaded and saved.",
    "tldr": "Selecting a file is not the same as uploading it. The tool and selected mode determine the next step: browser computation, a PrivaTools server job, or a direct AI provider request. Read that disclosure before you run the task.",
    "body": "<p>The same website can offer several processing paths. That is why the most useful privacy information sits beside the task you are about to run, not only in a general promise at the bottom of the page.</p>\n<h2>Selection gives the page access to the chosen file</h2>\n<p>When you use a file picker, the browser gives the page access to the file you selected. The <a href=\"https://developer.mozilla.org/en-US/docs/Web/API/File_API\">File API documentation</a> describes this local file access. A file picker by itself does not tell you whether the application will later send the file somewhere.</p>\n<p>On the PrivaTools home page, selecting a file shows suitable tasks. Choosing one hands that file to the workspace; it does not automatically run every suggested task. Review the workspace before starting processing.</p>\n<h2>Follow the path for the selected operation</h2>\n<table><thead><tr><th>Processing path</th><th>Example</th><th>What happens to content</th></tr></thead><tbody><tr><td>In the browser</td><td>Markdown Editor &amp; HTML</td><td>Text is edited and converted on the device.</td></tr><tr><td>PrivaTools server</td><td>Merge PDF or Markdown to PDF</td><td>Input is uploaded for the operation; an output is returned.</td></tr><tr><td>Your AI provider</td><td>PDF chat using BYOK</td><td>Extracted text and questions go to the selected endpoint.</td></tr></tbody></table>\n<p>Some tools offer more than one engine. Background removal, for example, has server and on-device choices. A statement about one mode does not describe the other. The <a href=\"/trust\">trust center</a> provides the wider explanation.</p>\n<h2>A local preview can precede an upload</h2>\n<p>A PDF canvas helps you choose a page or region in the browser. The apply action may still use the server. Likewise, a document can be read locally and its extracted text sent to an AI model. Looking only for an upload of the original filename misses that second kind of transfer.</p>\n<p>For on-device AI, the first run may need model downloads. The application is receiving software in that step, rather than necessarily sending your document. It still needs compatible hardware, storage and a network connection for missing resources.</p>\n<h2>Understand the server lifecycle</h2>\n<p>Server-backed tasks use temporary inputs and outputs. Response cleanup removes files after the response, while a background sweep handles leftovers from failures and interruptions. That design should not be described as instantaneous erasure under every condition. See <a href=\"/blog/what-deleted-means\">the deletion guide</a> for the distinction.</p>\n<h2>Remember the copies you control</h2>\n<p>The result you download is a separate copy. Browser preferences, locally saved credentials or Vault items are different again. A site’s server cleanup cannot remove a file you saved to a synced folder, and signing in does not automatically back up a local draft.</p>\n<h2>Make a choice before sending content</h2>\n<p>If the file must stay within an approved environment, choose a matching local tool or approved deployment. If a server or provider workflow fits your requirements, inspect its current disclosure, run a small representative test and keep the accepted output. The aim is to make the data path a deliberate choice.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "MDN File API",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/File_API"
      },
      {
        "label": "PrivaTools trust center",
        "url": "/trust"
      },
      {
        "label": "PrivaTools privacy information",
        "url": "/privacy"
      }
    ],
    "relatedTools": [
      "markdown-html",
      "markdown-to-pdf",
      "merge-pdf",
      "chat-with-pdf"
    ],
    "tags": [
      "Privacy",
      "How-To"
    ],
    "readTime": "2 min read"
  },
  {
    "slug": "batch-or-pipeline-how-to-choose",
    "publishedAt": "2026-09-14",
    "title": "Batch or Pipeline? Choose the shape of your task",
    "description": "Decide between repeating one operation across files and chaining several supported steps for a document.",
    "tldr": "Batch applies one supported operation to multiple inputs. Pipeline chains compatible steps so one output becomes the next input. Start with one accepted sample, and inspect partial failures or intermediate choices before scaling up.",
    "body": "<p>The difference is easier to see with two real jobs. “Resize these photographs to the same width” repeats one operation. “Rotate this PDF, remove its metadata, then compress it” applies several operations in sequence. They need different workspaces.</p>\n<h2>Use Batch for repetition</h2>\n<p><a href=\"/batch\">Batch</a> is useful when the selected task and settings make sense for each input. Group files by the output they need. Do not put a screenshot that needs crisp text and a photograph that needs aggressive compression into the same group merely because both are images.</p>\n<p>A batch still has individual outcomes. Some files can succeed while another fails. Read the result list, count completed outputs and retry only the intended items. The download container does not certify that every input completed successfully.</p>\n<h2>Use Pipeline for a sequence</h2>\n<p><a href=\"/pipeline\">Pipeline</a> offers a supported set of steps with compatible inputs and outputs. Each step uses the preceding result. A pipeline is not a way to connect any arbitrary pair of tools from the catalogue.</p>\n<p>Order matters. Rotating a page before choosing a region is different from rotating it afterward. A final compression step can also change the quality of an output you previously accepted. Read the selected settings and inspect the final result of the whole sequence.</p>\n<h2>Write an acceptance check before running</h2>\n<p>For a PDF sequence, the check might be: “All pages upright, author metadata removed, text still selectable, small labels readable.” For a batch of images it might be: “Every output is the requested format and dimensions, with the whole subject visible.”</p>\n<p>Choose checks that describe the result, not merely the absence of an error message. This gives you a reason to stop or adjust the workflow before processing more files.</p>\n<h2>Start small</h2>\n<ol><li>Keep the original inputs in a separate location.</li><li>Choose a non-sensitive representative sample.</li><li>Select the task or supported sequence and inspect its processing disclosure.</li><li>Run the sample and open the downloaded output.</li><li>Apply the acceptance checks before adding a larger collection.</li></ol>\n<p>Use the current file-count, size and service limits shown by the workspace. Free interactive access does not mean that every combination, file or queue size is supported.</p>\n<h2>Know what reuse actually saves</h2>\n<p>A saved setup can preserve choices; it should not be treated as a backup of source documents or proof that future inputs are compatible. If the next collection has different page sizes, orientation or image content, test the setup again.</p>\n<p>For an ongoing routine, keep a short note of the input requirements, sequence and final checks. Our <a href=\"/blog/repeatable-document-workflow\">repeatable workflow guide</a> shows how to turn that note into a practical review process.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools Batch workspace",
        "url": "/batch"
      },
      {
        "label": "PrivaTools Pipeline workspace",
        "url": "/pipeline"
      }
    ],
    "relatedTools": [
      "compress-pdf",
      "image-converter"
    ],
    "tags": [
      "Workflow",
      "How-To"
    ],
    "readTime": "2 min read"
  },
  {
    "slug": "repeatable-document-workflow",
    "publishedAt": "2026-09-14",
    "title": "Build a document workflow you can trust twice",
    "description": "Create a repeatable file-processing routine with clear inputs, reversible preparation, accepted output and a useful failure log.",
    "tldr": "Keep originals, define the output, test a small sample, and record the settings that produced an accepted result. Reusing a workflow saves setup; it does not remove the need to check each new collection.",
    "body": "<p>A repeatable workflow is more than a sequence of buttons. It explains which inputs are suitable, what will change, what must remain and how you know the output is ready. That is useful whether you process a monthly report or a folder of scanned receipts.</p>\n<h2>Define the result in plain language</h2>\n<p>Start with one sentence: “A readable PDF containing the approved pages in the right order,” for example. Then list the properties you will check: page count, orientation, selectable text, image legibility and the required filename.</p>\n<p>Do not add steps without a reason. Flattening, metadata removal, rasterisation and compression can each change useful properties. A shorter workflow can be easier to review than a longer one that quietly removes things.</p>\n<h2>Protect the starting point</h2>\n<p>Keep the original files in a separate folder. Use clear working names and distinguish drafts from accepted output. This makes it easier to compare results and prevents a revised file from being mistaken for an unchanged original.</p>\n<p>Check the processing path for each step. A browser editor followed by a server converter is a mixed workflow. If the content has restrictions, approve the whole path rather than only the first screen.</p>\n<h2>Choose a small representative sample</h2>\n<p>Include the awkward cases: a rotated page, small type, a dense table, a photograph or a scan. A successful blank page is not a useful test for a complex report. Run the steps manually first so you understand what each one changes.</p>\n<p>For example, use <a href=\"/tool/organize-pages\">Organize Pages</a> to prepare the intended order, then a supported optimisation step if the output is too large. If the exact sequence is supported by <a href=\"/pipeline\">Pipeline</a>, you can reuse it there after accepting the result. Use <a href=\"/batch\">Batch</a> when the same independent task fits several inputs.</p>\n<h2>Record the choices that matter</h2>\n<ul><li>The accepted input formats and any preparation they need.</li><li>The task or supported step order.</li><li>The settings that materially affect output.</li><li>The processing location and any chosen AI provider.</li><li>The final acceptance checks.</li></ul>\n<p>A short Markdown note is a convenient record. Keep it with the project and edit it using <a href=\"/tools/markdown-html\">Markdown Editor &amp; HTML</a>. Avoid including passwords, API keys or confidential document text in a shared recipe.</p>\n<h2>Handle failure without starting over blindly</h2>\n<p>Record which input failed and the error shown. Check that file locally, then retry the relevant operation after correcting the cause. Do not assume a partly completed batch is complete, and do not multiply outputs by rerunning successful items without a reason.</p>\n<p>If you need support, share the tool name, format, approximate size, selected settings and error message. Use a synthetic reproducer when possible. A useful failure report should not require publishing the original sensitive file.</p>\n<h2>Accept the final output</h2>\n<p>Open the file you will actually deliver after the final step. Check the properties you wrote down, retain the accepted result and update the recipe if the requirements change. Repeatability makes a process easier to inspect; it is not a substitute for inspecting it.</p>",
    "author": "PrivaTools",
    "updatedAt": "2026-09-14",
    "reviewedAt": "2026-09-14",
    "sources": [
      {
        "label": "PrivaTools Pipeline workspace",
        "url": "/pipeline"
      },
      {
        "label": "PrivaTools Batch workspace",
        "url": "/batch"
      },
      {
        "label": "PrivaTools support",
        "url": "/support"
      }
    ],
    "relatedTools": [
      "organize-pages",
      "compress-pdf",
      "markdown-html"
    ],
    "tags": [
      "Workflow",
      "Documents",
      "How-To"
    ],
    "readTime": "2 min read"
  }
];

export function getBlogPost(slug: string): BlogPost | undefined {
  return blogPosts.find(post => post.slug === slug);
}

export function postsForTool(slug: string, limit = 4): BlogPost[] {
  return blogPosts.filter(post => post.relatedTools?.includes(slug))
    .sort((a, b) => b.publishedAt.localeCompare(a.publishedAt)).slice(0, limit);
}
