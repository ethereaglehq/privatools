/**
 * Editorial comparisons checked against the linked primary product pages.
 * Keep the array and its content literal: the build exports these same fields
 * for server-rendered comparison content. A review date is not a benchmark.
 *
 * Rules that keep these pages worth indexing (ComparePage.test.tsx and
 * backend/tests/test_compare_page_parity.py enforce the mechanical ones):
 * - A competitor fact comes only from that product's own official pages, and
 *   its row links the page. `reviewedAt` is the day every competitor fact was
 *   checked; move it only after re-checking them all. Leave out what an
 *   official page does not state.
 * - PrivaTools facts come from the current code and registries, never from
 *   older copy. Never write the tool total as a number.
 * - Each page is its own: a sentence of twelve or more words may appear on
 *   one comparison only.
 * - `title` starts "PrivaTools vs <name>", at most 60 characters; the
 *   `description` is 120–160 characters and ends with a period. Both unique.
 */
export interface ComparisonFact {
  label: string;
  privatools: string;
  competitor: string;
  /** The official page that states the competitor fact; listed in `sources`. */
  sourceUrl: string;
}

export interface ProductComparison {
  slug: string;
  name: string;
  title: string;
  description: string;
  summary: string;
  category: string;
  /** Two or three short points that set this comparison apart on /compare. */
  highlights: string[];
  /** What the product is, in the terms its official pages use. */
  overview: string[];
  features: ComparisonFact[];
  /** Product-specific discussion: plans in practice, data path, editing depth. */
  sections: { heading: string; body: string[] }[];
  choosePrivaTools: string[];
  chooseCompetitor: string[];
  tradeoffs: string[];
  sources: { label: string; url: string }[];
  relatedLinks?: { label: string; url: string }[];
  reviewedAt: string;
}

/** The /compare document title. backend/app/seo_meta.py serves the same one. */
export const COMPARE_DIRECTORY_TITLE = "PrivaTools vs iLovePDF, Smallpdf & Adobe — Compared";

export const comparisons: ProductComparison[] = [
  {
    slug: "remove-bg", name: "remove.bg",
    title: "PrivaTools vs remove.bg: what changes on 1 December 2026",
    description: "remove.bg's website closes on 1 December 2026 as background removal moves to Canva. Its credits, limits and API compared with PrivaTools' free remover.",
    summary: "remove.bg says its standalone website will no longer be available from 1 December 2026 at 9:00am CET. Background removal is moving to Canva, self-service API access to Leonardo.ai, and unused pay-as-you-go credits expire on 1 December. Until then, website previews are free up to 0.25 megapixels and full resolution costs credits. PrivaTools' Background Remover is free at the image's original size, with a server engine or an on-device model.",
    category: "Images & design",
    highlights: ["remove.bg's website and accounts close on 1 December 2026.", "Full resolution costs a credit per image there; PrivaTools is free at full size.", "PrivaTools can run the model on your device; remove.bg's desktop app uses its API."],
    overview: [
      "remove.bg removes image backgrounds with AI through its website, an API, desktop apps for Windows, macOS and Linux, an Android app and plugins such as one for Photoshop. Its FAQ says the standalone website and accounts will no longer be available from 1 December 2026 at 9:00am CET and that the self-service API stops accepting requests from 1 December 2026, with API access moving to Leonardo.ai. Enterprise API contracts are not affected.",
      "Until then, website previews are free up to 0.25 megapixels for personal use, and each full-resolution image costs one credit, bought in pay-as-you-go packs or a subscription that renews monthly or yearly. Uploads can be JPG, PNG or WebP files of up to 22 MB and 50 megapixels. Its help centre says the uploaded image and the result are deleted about an hour after upload at the latest, and API images right after the call.",
    ],
    features: [
      { label: "Price", privatools: "Free at the image's original size, with no credits to buy.", competitor: "Website previews are free; each full-resolution image costs 1 credit, from packs or a subscription.", sourceUrl: "https://www.remove.bg/pricing" },
      { label: "Use of results", privatools: "The terms leave all rights to your files and outputs with you.", competitor: "Subscription and pay-as-you-go plans allow commercial use; free and no-account use is non-commercial only.", sourceUrl: "https://www.remove.bg/help/a/can-i-use-remove-bg-for-commercial-purposes" },
      { label: "File types and size", privatools: "JPG, PNG, WebP or BMP; the server engine takes files of about 250 MB.", competitor: "JPG, PNG or WebP files of up to 22 MB.", sourceUrl: "https://www.remove.bg/help/a/what-image-formats-are-supported" },
      { label: "Resolution", privatools: "The browser engine takes up to 40 megapixels; the server engine refuses images over 300 megapixels.", competitor: "Up to 50 megapixels in and out, with larger images resized; website previews are capped at 0.25 megapixels.", sourceUrl: "https://www.remove.bg/help/a/what-is-the-maximum-image-resolution-file-size" },
      { label: "Where images are processed", privatools: "On PrivaTools' server by default, or in your browser with the downloaded U-2-Net model.", competitor: "Its desktop app processes images through the remove.bg API, which needs an internet connection.", sourceUrl: "https://www.remove.bg/a/background-remover-windows-mac-linux" },
      { label: "Retention", privatools: "Temporary files are removed after the response, and a sweep clears leftovers older than ten minutes.", competitor: "Upload and result are deleted about an hour after upload at the latest; API images right after the call.", sourceUrl: "https://www.remove.bg/help/a/are-my-images-safe" },
      { label: "Account", privatools: "Not needed for the tool or its batch download.", competitor: "Generating an API key requires an account.", sourceUrl: "https://www.remove.bg/help/a/how-do-i-generate-my-api-key" },
      { label: "API", privatools: "A free key covers 500 processing units and 250 MiB of uploads a day; each background removal costs 5 units.", competitor: "50 free previews a month for the desktop app or the API; higher resolutions and commercial use are paid.", sourceUrl: "https://www.remove.bg/help/a/is-remove-bg-free-" },
      { label: "What happens next", privatools: "The tool is part of PrivaTools' open-source code and can also be self-hosted.", competitor: "Website and accounts close on 1 December 2026; the self-service API, plugins and unused pay-as-you-go credits end that day.", sourceUrl: "https://www.remove.bg/faq" },
    ],
    sections: [
      { heading: "What 1 December 2026 changes", body: [
        "remove.bg's FAQ sets out the closure. The website and your account data remain available until 1 December 2026 at 9:00am CET, and the FAQ asks you to export your credit usage report and invoices before then. From 1 December the self-service API stops accepting requests, unused pay-as-you-go credits expire, and the Photoshop plugin and other integrations are discontinued. Enterprise API contracts continue as normal.",
        "Subscriptions keep working until 1 December 2026 at 9:00am CET and then end automatically. On a monthly plan, any final renewal on or after 1 November is free; an annual plan with unused time left gets a pro-rata refund to the original payment method. The FAQ says Canva's background remover uses the same background-removal technology, and it points self-service API users to Leonardo.ai.",
      ] },
      { heading: "Replacing it with PrivaTools", body: [
        "PrivaTools' Background Remover returns a transparent PNG at the original dimensions, without an account, credits or a personal-use restriction. Its default server engine runs the compact U-2-Net model, u2netp, on the PrivaTools server and accepts about five runs a minute from one visitor. The in-browser engine downloads the same model, about 4.4 MB plus its runtime, and then processes images on your device, so they are not uploaded for that path.",
        "remove.bg's home page highlights bulk editing of up to 500 images a minute and an AI background generator, and its desktop app page says its algorithms are trained to handle difficult elements such as hair. PrivaTools only produces the cut-out, and u2netp is a small model: hair, fur, glass and motion blur can come out rough. We have not compared the two services, so test your hardest images before you move a product catalogue.",
      ] },
    ],
    chooseCompetitor: ["You have remove.bg credits or a subscription to use before 1 December 2026.", "You design in Canva, which is where remove.bg says its background removal is going.", "You want its AI background generator or bulk editing before the website closes.", "You have an Enterprise API contract, which remove.bg says continues as normal."],
    choosePrivaTools: ["You need transparent PNGs from a standalone tool after 1 December 2026.", "You want full-size cut-outs without buying credits or accepting a non-commercial limit.", "You want the choice to keep images on your device with the in-browser engine.", "You want background removal from your own scripts through a free API key, within its daily allowance."],
    tradeoffs: ["remove.bg's help centre says uploaded images are not used to train its AI; its privacy policy says account content may be analysed to train its models. Read both if that matters to you.", "PrivaTools' model is compact, which suits quick cut-outs; inspect edges on dark and light backgrounds before relying on a result.", "Neither service's output quality was benchmarked for this page."],
    sources: [
      { label: "remove.bg is moving to Canva (FAQ)", url: "https://www.remove.bg/faq" },
      { label: "remove.bg pricing and credits", url: "https://www.remove.bg/pricing" },
      { label: "Is remove.bg free?", url: "https://www.remove.bg/help/a/is-remove-bg-free-" },
      { label: "remove.bg maximum resolution and file size", url: "https://www.remove.bg/help/a/what-is-the-maximum-image-resolution-file-size" },
      { label: "remove.bg supported image formats", url: "https://www.remove.bg/help/a/what-image-formats-are-supported" },
      { label: "remove.bg image safety and deletion", url: "https://www.remove.bg/help/a/are-my-images-safe" },
      { label: "remove.bg commercial use", url: "https://www.remove.bg/help/a/can-i-use-remove-bg-for-commercial-purposes" },
      { label: "remove.bg API key and account", url: "https://www.remove.bg/help/a/how-do-i-generate-my-api-key" },
      { label: "remove.bg desktop app", url: "https://www.remove.bg/a/background-remover-windows-mac-linux" },
      { label: "remove.bg Android app", url: "https://www.remove.bg/a/free-background-remover-app-android" },
      { label: "remove.bg home page", url: "https://www.remove.bg/" },
      { label: "Does remove.bg use images to train its AI?", url: "https://www.remove.bg/help/a/do-you-use-my-images-to-train-the-ai" },
      { label: "remove.bg privacy policy", url: "https://www.remove.bg/privacy" },
    ],
    relatedLinks: [{ label: "Try Background Remover", url: "/tools/remove-background" }, { label: "Plan a background-removal workflow", url: "/blog/remove-bg-canva-alternative" }, { label: "Choose the processing engine", url: "/blog/remove-background-without-uploading" }, { label: "Resize or crop the cut-out", url: "/tools/resize-crop-image" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "ilovepdf", name: "iLovePDF",
    title: "PrivaTools vs iLovePDF: free limits, apps and file handling",
    description: "iLovePDF's free Basic plan limits files per task and file size, and Premium adds desktop tools and mobile access; PrivaTools is free with open code.",
    summary: "iLovePDF is a broad PDF suite on the web, Windows, macOS, iOS and Android, and its plans also include iLoveIMG image tools. Its free Basic plan works without an account but limits files per task and file size; Premium adds all tools, access across web, mobile and desktop, workflows, digital signatures and much larger files. PrivaTools has no paid plan, also covers audio, video and developer formats and publishes its code, but it has no native apps.",
    category: "Everyday PDF",
    highlights: ["Per-tool limits on the free Basic plan, lifted by Premium; PrivaTools has one free tier.", "Premium desktop tools process files on your computer; nearly all of PrivaTools' PDF tools upload to its server.", "Files deleted within two hours there, or sooner by hand; PrivaTools cleans up after each response."],
    overview: [
      "iLovePDF, from ILOVEPDF S.L. in Barcelona, offers PDF tools on the web, iOS and Android apps, a Chrome extension and iLovePDF Desktop for Windows and macOS, which is free as a PDF reader. Its free Basic plan covers the essential tools with limited processing and needs no account, although its AI tools require one. Premium, for up to 25 users, adds every tool, unlimited processing, access across web, mobile and desktop, workflows, digital signatures, an ad-free experience and 2,000 AI credits a month.",
      "Files processed on iLovePDF's servers are deleted automatically within two hours, and its security page says you can also delete them yourself from the download screen. Premium and Business users can choose the region where files are processed, and the Desktop tools process files on your computer. Its developer product, iLoveAPI, gives 2,500 free credits a month on registration, with paid credit plans in US dollars.",
    ],
    features: [
      { label: "Price", privatools: "Every tool is free; there is no Premium tier to unlock.", competitor: "Basic is free; Premium is billed monthly or yearly for up to 25 users; Business pricing is quoted.", sourceUrl: "https://www.ilovepdf.com/pricing" },
      { label: "Free-plan limits", privatools: "No daily task count; heavy tools such as OCR take about five runs a minute from one visitor.", competitor: "Basic processes a limited number of documents, and tools such as OCR to Word and PDF/A are Premium only.", sourceUrl: "https://www.ilovepdf.com/pricing" },
      { label: "Files and size", privatools: "Merge takes up to 100 PDFs in one 500 MB upload but stops waiting after 60 seconds; most single-file pages take about 250 MB.", competitor: "Basic merges 25 files up to 100 MB and Premium 500 files up to 4 GB; Basic Office conversion and OCR take one 15 MB file.", sourceUrl: "https://www.ilovepdf.com/pricing" },
      { label: "Where files are processed", privatools: "Most PDF tools run on the PrivaTools server in temporary per-request storage; most text and developer tools run in your browser.", competitor: "On its servers; Premium and Business users can choose the region where files are processed.", sourceUrl: "https://www.ilovepdf.com/pricing" },
      { label: "Retention", privatools: "Response cleanup removes each job's files; a sweep clears leftovers after ten minutes.", competitor: "Deleted automatically within two hours of processing, and you can delete files from the download screen.", sourceUrl: "https://www.ilovepdf.com/help/security" },
      { label: "Account", privatools: "Not needed for any tool; an optional account issues API keys.", competitor: "Not needed for the free web tools; its AI tools require a user account.", sourceUrl: "https://www.ilovepdf.com/help/terms" },
      { label: "Platforms", privatools: "Any modern browser, installable as a web app; no native apps.", competitor: "Web, Windows 10 or later, macOS 12 or later, iOS and Android apps.", sourceUrl: "https://www.ilovepdf.com/business" },
      { label: "API", privatools: "A free key: 500 processing units and 250 MiB of uploads a day, with heavy operations at 5 units.", competitor: "iLoveAPI gives 2,500 free credits a month on registration, with paid credit plans in US dollars.", sourceUrl: "https://www.iloveapi.com/pricing" },
    ],
    sections: [
      { heading: "Reading the Basic plan", body: [
        "iLovePDF's pricing page says the free plan processes a limited number of documents, and its plan table lists limits per tool. On Basic, merging takes up to 25 files and 100 MB, compression two files up to 200 MB, and Office conversion and OCR one file of 15 MB; editing and splitting take one file on every plan. Tools including OCR conversion to Word or Excel and PDF/A are marked as not included in Basic, and Premium raises most per-task limits to 4 GB.",
        "PrivaTools applies the same limits to everyone. An upload request can be 500 MB, which is about 250 MB for one file on most pages because the page sends the file twice. Standard tool pages queue up to 25 files, but heavy tools accept about five runs a minute from one visitor, so in a long queue some files are marked failed and need a retry. Merge, PDF to Word, OCR and Protect stop waiting after 60 seconds, upload included, so a large file on a slow connection can fail. There is no paid tier to lift any of this.",
      ] },
      { heading: "Apps, regions and signatures", body: [
        "iLovePDF Desktop is free as a PDF reader, and Premium adds its desktop tools, which process files on your computer. Premium users can pick among seven processing regions and Business users among eleven. Its Premium digital signature embeds a certified hash and a qualified timestamp, and its security page says signed documents are kept for up to five years to meet legal requirements.",
        "PrivaTools has no native apps and no region choice on the public site; if location or offline processing matters, you can run it on your own hardware. Its Sign PDF and E-Sign PDF place a visible signature image and do not create certificate-based or certified signatures, although Verify Digital Signature can check whether an existing signature still matches its file.",
      ] },
    ],
    chooseCompetitor: ["You want desktop tools that process files on your computer, alongside mobile and web access.", "You send documents for signature and want its Premium digital signatures with a qualified timestamp.", "You need files processed in a specific region, or files far larger than PrivaTools accepts.", "Your files live in Google Drive or Dropbox, which it integrates with."],
    choosePrivaTools: ["You want every tool free, with the same limits for everyone and no plan to upgrade.", "You want source code you can inspect and a copy you can host.", "You also work with audio, video, archives or developer formats."],
    tradeoffs: ["iLovePDF showed us its prices in Indian rupees, based on our location, so this page quotes no figure; check the pricing page from where you are.", "PrivaTools' 60-second wait on its heavier pages can cut off a large upload on a slow connection.", "We did not benchmark conversion quality or speed for either product."],
    sources: [
      { label: "iLovePDF pricing and plan limits", url: "https://www.ilovepdf.com/pricing" },
      { label: "iLovePDF terms", url: "https://www.ilovepdf.com/help/terms" },
      { label: "iLovePDF security", url: "https://www.ilovepdf.com/help/security" },
      { label: "iLovePDF Desktop", url: "https://www.ilovepdf.com/desktop" },
      { label: "iLovePDF for business and system requirements", url: "https://www.ilovepdf.com/business" },
      { label: "iLovePDF signatures", url: "https://www.ilovepdf.com/sign-pdf" },
      { label: "iLovePDF features and integrations", url: "https://www.ilovepdf.com/features" },
      { label: "iLovePDF Chrome extension announcement", url: "https://www.ilovepdf.com/blog/ilovepdf-iloveimg-chrome-extensions-update" },
      { label: "iLoveAPI pricing", url: "https://www.iloveapi.com/pricing" },
    ],
    relatedLinks: [{ label: "Merge PDF", url: "/tool/merge-pdf" }, { label: "Compress PDF", url: "/tool/compress-pdf" }, { label: "PrivaTools and iLovePDF: compare the workflow", url: "/blog/privatools-vs-ilovepdf" }, { label: "Looking for an iLovePDF alternative?", url: "/blog/ilovepdf-alternatives-2026" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "smallpdf", name: "Smallpdf",
    title: "PrivaTools vs Smallpdf: free downloads, Pro and Sign.com",
    description: "Smallpdf's free plan limits daily downloads and AI use, and Pro bundles Sign.com and a Windows app. PrivaTools is free with open code. Plans and data compared.",
    summary: "Smallpdf offers PDF tools on the web, a Windows desktop app, free iOS and Android apps with more for Pro users, and a Chrome extension and apps for Google Workspace and Dropbox. Its free plan lets you try most tools without signing up but limits downloads, compression strength and AI use; Pro lifts those limits and includes Sign.com e-signatures, and first-time subscribers can take a 7-day trial that asks for payment details. PrivaTools is free throughout and open source, with no native apps.",
    category: "Everyday PDF",
    highlights: ["Daily download limits on Smallpdf's free plan; PrivaTools has no daily count.", "Pro includes Sign.com signature requests; PrivaTools only places signature images.", "Temporary processing on Hetzner servers in the EU; PrivaTools can also be self-hosted."],
    overview: [
      "Smallpdf's pricing page lists Free, Pro, Team and Business plans. The free plan offers limited document downloads, limited mobile app access and a Sign.com account limited to two documents a month. Pro adds unlimited downloads, text editing, OCR to Word, Excel and PowerPoint, strong compression, unlimited AI tools and unlimited mobile access. Its download page offers apps for Windows, iOS and Android, and marks its macOS app as unsupported since 1 October 2021.",
      "Uploaded files are processed on Hetzner servers in the European Union; the privacy notice says they may be stored there temporarily and that this does not involve permanent storage. The support page says files are removed an hour after processing for most tools. AI features use OpenAI. Smallpdf's AI terms treat what you give its AI tools and what they return as your Customer Data, which Smallpdf does not use, or let others use, to train the models behind those tools; usage data is not shared with OpenAI for training and is deleted from Smallpdf's own database after 90 days. It states that it is ISO/IEC 27001 certified.",
    ],
    features: [
      { label: "Price", privatools: "Free throughout; nothing to subscribe to.", competitor: "Free plan; Pro billed monthly or yearly; Team and Business plans; a 7-day Pro trial.", sourceUrl: "https://smallpdf.com/pricing" },
      { label: "Free-plan limits", privatools: "No daily count; about five runs a minute per visitor on heavy tools.", competitor: "Most tools carry a daily download limit, PDF OCR included; AI tools allow up to 4 documents a day.", sourceUrl: "https://smallpdf.com/pricing" },
      { label: "File size", privatools: "500 MB per upload request, about 250 MB per file on most pages, and some heavy pages wait 60 seconds at most.", competitor: "The free file size is marked Limited without a number, paid plans Unlimited; AI files up to 50 MB.", sourceUrl: "https://smallpdf.com/pricing" },
      { label: "Where files are processed", privatools: "In your browser or in PrivaTools' temporary server storage, as each tool states.", competitor: "Temporarily on Hetzner servers in the European Union, without permanent storage.", sourceUrl: "https://smallpdf.com/privacy" },
      { label: "Retention", privatools: "Cleaned after the response, with a sweep for leftovers older than ten minutes.", competitor: "For most tools, files are removed from its servers an hour after processing.", sourceUrl: "https://smallpdf.com/support" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "Most tools can be tried without signing up, with some limitations.", sourceUrl: "https://smallpdf.com/education" },
      { label: "Platforms", privatools: "Browser on any operating system; installable as a web app.", competitor: "Web, Windows, iOS and Android apps, and a Chrome extension; its macOS app is marked unsupported.", sourceUrl: "https://smallpdf.com/download" },
      { label: "Signatures", privatools: "Sign PDF places a drawn or uploaded signature image; E-Sign PDF can also set a typed name.", competitor: "Sign.com can request signatures, track activity, add digital seals and issue a certificate of completion.", sourceUrl: "https://smallpdf.com/sign-pdf" },
    ],
    sections: [
      { heading: "What the free plan leaves out", body: [
        "Smallpdf meters its free plan by day. Most tools, including PDF OCR and conversion to and from Word, carry a daily download limit, and the mobile apps a daily task limit. Strong compression, batch processing, OCR that outputs Word, Excel or PowerPoint, text editing and image extraction are Pro features. Its support page says free users can process up to two conversions a day.",
        "PrivaTools does not count use by day. Its strongest compression preset, OCR and PDF to Word are available without an account, but heavy tools accept about five runs a minute from one visitor, so a long batch partly fails and needs retries, and the OCR and PDF to Word pages stop waiting after 60 seconds, upload included. It cannot edit existing PDF text on any plan: Edit PDF adds new content on top of the page.",
      ] },
      { heading: "Signing and AI", body: [
        "Pro bundles Sign.com, so one subscription covers editing and signature requests with tracking and a certificate of completion. Smallpdf's AI tools, including chat with PDF, summaries and translation, are part of its plans. PrivaTools' document AI tools, such as chat, summaries and translation, run an on-device model or use your own provider key, and its signature tools place an image rather than running a signing workflow.",
        "If most of your work is sending contracts for signature, Smallpdf with Sign.com covers more of it. If you mostly compress, convert and tidy documents, PrivaTools covers that without a plan.",
      ] },
    ],
    chooseCompetitor: ["You want mobile apps and a Windows app alongside the website under one subscription.", "You collect signatures from other people and need tracking and a certificate of completion.", "You want AI chat, summaries and translation included without supplying your own AI key.", "Your documents already live in Google Workspace or Dropbox."],
    choosePrivaTools: ["You need more than a few downloads a day without paying.", "You want the strongest compression preset and multi-file runs without a subscription.", "You prefer open code, or to host the service yourself."],
    tradeoffs: ["Its privacy notice gives different deletion rules for signed-in and signed-out use; check which applies before uploading sensitive files.", "PrivaTools' free runs have their own ceiling: heavy tools take about five a minute from one visitor.", "We did not benchmark output quality or speed."],
    sources: [
      { label: "Smallpdf pricing and plan comparison", url: "https://smallpdf.com/pricing" },
      { label: "Smallpdf help", url: "https://smallpdf.com/support" },
      { label: "Smallpdf privacy notice", url: "https://smallpdf.com/privacy" },
      { label: "Smallpdf downloads", url: "https://smallpdf.com/download" },
      { label: "Smallpdf mobile apps", url: "https://smallpdf.com/pdf-scanner" },
      { label: "Smallpdf without signing up", url: "https://smallpdf.com/education" },
      { label: "Smallpdf Sign PDF and Sign.com", url: "https://smallpdf.com/sign-pdf" },
      { label: "Smallpdf AI supplementary terms", url: "https://smallpdf.com/ai-products-supplementary-terms" },
    ],
    relatedLinks: [{ label: "Compress PDF", url: "/tool/compress-pdf" }, { label: "E-Sign PDF", url: "/tool/esign-pdf" }, { label: "PDF to Word", url: "/tool/pdf-to-word" }, { label: "PrivaTools and Smallpdf for everyday work", url: "/blog/privatools-vs-smallpdf" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "adobe-acrobat", name: "Adobe Acrobat",
    title: "PrivaTools vs Adobe Acrobat: plans, free tools and editing",
    description: "Most Adobe Acrobat online tools allow one free transaction without signing in, and editing existing text needs a paid plan; PrivaTools is free with no account.",
    summary: "Adobe Acrobat spans free Acrobat Reader, free online tools with limits on free use, and paid Acrobat Express, Standard, Pro and Studio plans that add, depending on the plan, AI Assistant, editing of existing text, signature requests, redaction and comparison. PrivaTools is free without an account for any tool and covers media and developer tasks too, but it cannot edit existing PDF text or run signature workflows, and it has no desktop app.",
    category: "Desktop & teams",
    highlights: ["Most free online tools allow one free transaction without signing in; PrivaTools has no transaction count, only a limit of about five runs a minute on heavy tools.", "Existing-text editing on paid plans, which PrivaTools does not offer.", "Certificate signatures and signature requests; PrivaTools places signature images only."],
    overview: [
      "Adobe Acrobat comes as free Acrobat Reader, free online tools and subscription plans: Acrobat Express, Standard, Pro and Studio. Editing text and images requires Standard or Pro, not Reader. Standard adds signature requests with tracking; Pro adds version comparison, redaction, bulk e-signature requests, OCR and web forms. Acrobat Express combines AI Assistant, PDF Spaces and Adobe Express Premium, and Studio includes everything in Pro plus those three. Adobe also sells Acrobat Pro 2024 as a one-time purchase that gives three years of access to the desktop app.",
      "Acrobat is available on desktop, web and mobile, plus browser extensions; the desktop apps need 64-bit Windows 10 or 11, or macOS 13 or later. Acrobat's online services upload files to Adobe cloud storage, which runs in data centres in North America, EMEA and Japan, and protect them with AES-256 encryption and TLS 1.2. If you don't sign in, Adobe soon deletes the file from its servers even after you download it, and Adobe says it does not use your documents or data to train AI models.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no subscription, trial or licence.", competitor: "In the US, Express US$9.99, Standard US$14.99, Pro US$19.99 and Studio US$24.99 a month, annual plan billed monthly.", sourceUrl: "https://www.adobe.com/acrobat/plans.html" },
      { label: "Free online limits", privatools: "No task count, though heavy tools are limited to about five runs a minute.", competitor: "Without signing in, most tools allow one free transaction and one download; signed in, one premium-tool transaction every 30 days.", sourceUrl: "https://helpx.adobe.com/document-cloud/faq/try-acrobat-online-services.html" },
      { label: "File limits", privatools: "About 250 MB per file on most pages, 100 PDFs per merge, and a 60-second wait on several heavy pages.", competitor: "PDFs up to 100 MB; PDF to Word and PowerPoint 200 MB, Split 1 GB, Compress 2 GB; Merge up to 100 files.", sourceUrl: "https://helpx.adobe.com/document-cloud/faq/try-acrobat-online-services.html" },
      { label: "Where files are processed", privatools: "No cloud library: server tools work on temporary copies, and browser-only tools process on your device.", competitor: "Online tools upload to Adobe cloud storage; if you don't sign in, Adobe soon deletes the file from its servers, even after you download it.", sourceUrl: "https://helpx.adobe.com/document-cloud/faq/try-acrobat-online-services.html" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "A few online tools need sign-in, and saving or sharing a result needs an Adobe ID.", sourceUrl: "https://helpx.adobe.com/document-cloud/faq/try-acrobat-online-services.html" },
      { label: "Editing existing text", privatools: "Not available: Edit PDF adds text, drawings, images and whiteout on top of the page.", competitor: "The free online editor adds text boxes, comments and drawings but cannot edit existing body text.", sourceUrl: "https://www.adobe.com/acrobat/online/pdf-editor.html" },
      { label: "Signatures", privatools: "Places visible signature images and checks existing signatures against the file, but cannot sign with a certificate.", competitor: "Acrobat and Acrobat Reader sign PDFs with certificate signatures and validate signed files.", sourceUrl: "https://helpx.adobe.com/acrobat/kb/certificate-signatures.html" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "Licensed, not sold; the terms forbid attempts to discover the source code.", sourceUrl: "https://www.adobe.com/legal/terms.html" },
      { label: "Platforms", privatools: "Any modern browser, including on Linux; installable as a web app.", competitor: "Available on desktop, web and mobile, plus browser extensions.", sourceUrl: "https://www.adobe.com/acrobat.html" },
    ],
    sections: [
      { heading: "Free online tools and their limits", body: [
        "Adobe's free online tools come with limits on free use. Without an Adobe ID, most tools let you complete one free transaction and download the result once; signed in, you can share, fill, sign and comment on PDFs for free and make one free transaction with a premium tool every 30 days. Removing a password needs a subscription or the seven-day Acrobat Pro trial, and a password added with the free Protect PDF tool cannot then be removed with it. Page tools such as rotate and extract handle up to 1,500 pages.",
        "PrivaTools has no trial logic. Protect PDF, Unlock PDF, compression, conversion, OCR and redaction are free on every run and need no sign-in, within the 500 MB upload cap, a limit of about five runs a minute on heavy tools and a 60-second wait on pages such as Protect, OCR and PDF to Word.",
      ] },
      { heading: "Where Acrobat does more", body: [
        "Acrobat edits existing text and images and adjusts the formatting, compares versions, creates web forms and reusable e-sign templates, repairs accessibility tagging in Pro and saves PDF/A, PDF/X and PDF/E files in Pro. It signs with certificates and validates signed files, and Standard and above request signatures and track responses. Its AI Assistant, included in Acrobat Express and Studio or added to other plans, sends content extracted from your documents to Microsoft Azure OpenAI split and encrypted, and Adobe says the documents themselves are not stored there.",
        "PrivaTools covers parts of this with separate free tools: Compare PDF shows visual or text differences, Form Creator adds fillable fields, the Accessibility Checker audits tagging without changing the file, Redact PDF removes the content under each box, and Verify Digital Signature checks whether each signature still matches the file, without checking the certificate against a trust list. It cannot edit existing text or sign with a certificate, and its document AI tools use on-device models or your own provider key.",
      ] },
    ],
    chooseCompetitor: ["You edit existing text and images in PDFs as part of daily work.", "You need certificate-based signatures, or signature requests with tracking.", "You produce PDF/A files or repair accessibility tagging with Acrobat Pro.", "Your team needs licences managed centrally in an admin console."],
    choosePrivaTools: ["You need more than one task done in a browser without an Adobe ID or a trial.", "You protect, unlock, compress, convert, OCR or redact files often and want that free.", "You want open code you can host yourself, on any operating system."],
    tradeoffs: ["The online-tool limits here come from an Adobe help article last updated in June 2025, the newest we found.", "A very large file can outlast PrivaTools' 60-second wait on its Protect, OCR and PDF to Word pages.", "We did not benchmark either product's output."],
    sources: [
      { label: "Adobe Acrobat plans and prices (US)", url: "https://www.adobe.com/acrobat/plans.html" },
      { label: "Adobe Acrobat overview", url: "https://www.adobe.com/acrobat.html" },
      { label: "Adobe Acrobat Express", url: "https://www.adobe.com/acrobat/acrobat-express.html" },
      { label: "Acrobat Pro free trial and AI Assistant Plus", url: "https://www.adobe.com/acrobat/free-trial-download.html" },
      { label: "Acrobat online services: free use and limits", url: "https://helpx.adobe.com/document-cloud/faq/try-acrobat-online-services.html" },
      { label: "Adobe's free online PDF editor", url: "https://www.adobe.com/acrobat/online/pdf-editor.html" },
      { label: "Adobe Acrobat Reader", url: "https://www.adobe.com/acrobat/pdf-reader.html" },
      { label: "Adobe certificate signatures", url: "https://helpx.adobe.com/acrobat/kb/certificate-signatures.html" },
      { label: "Acrobat system requirements", url: "https://helpx.adobe.com/acrobat/desktop/get-started/learn-the-basics/tech-requirements.html" },
      { label: "Adobe cloud storage data centres and AI processing", url: "https://helpx.adobe.com/acrobat/web/manage-cloud-storage/manage-adobe-cloud-files/cloud-storage-data-centers.html" },
      { label: "Adobe General Terms of Use", url: "https://www.adobe.com/legal/terms.html" },
      { label: "Creating accessible PDFs (Acrobat Pro)", url: "https://helpx.adobe.com/acrobat/using/creating-accessible-pdfs.html" },
      { label: "PDF/A, PDF/X and PDF/E files (Acrobat Pro)", url: "https://helpx.adobe.com/acrobat/using/pdf-x-pdf-a-pdf.html" },
    ],
    relatedLinks: [{ label: "Edit PDF", url: "/tool/edit-pdf" }, { label: "Compare PDF", url: "/tool/compare-pdf" }, { label: "Redact PDF", url: "/tool/redact-pdf" }, { label: "Choosing a free PDF editor", url: "/blog/best-free-online-pdf-editors-2026" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "sejda", name: "Sejda PDF",
    title: "PrivaTools vs Sejda PDF: free limits, pricing and Desktop",
    description: "Sejda PDF limits free use to three tasks an hour and sells Web and Desktop passes; PrivaTools has no task quota. Limits, data paths and tools compared.",
    summary: "Sejda PDF is a mature PDF toolset with a web version and a desktop app for Windows, macOS and Linux. Its free tier is capped per document and per hour, and paid passes remove those caps. PrivaTools has no task quota or paid tier and adds image, media and developer tools, but its editor adds content on top of pages rather than editing the existing text, which Sejda offers.",
    category: "Everyday PDF",
    highlights: ["Three free tasks an hour on Sejda Web, against no task quota.", "Editing existing PDF text, which PrivaTools does not offer.", "A local desktop app, against a browser app you can self-host."],
    overview: [
      "Sejda offers online PDF tools, Sejda Web, and a desktop application, Sejda Desktop, for Windows, macOS and Linux, with a Chromebook route through the Linux environment. Its press page says Sejda started in 2010 as an open-source project; the Desktop licence agreement now states that the software is not open source.",
      "Sejda Web uploads documents and processes them on Sejda's servers, and its tool pages say files are deleted automatically after two hours. Sejda Desktop processes files on your computer. Free use needs no signup and is limited per document, per task and per hour; a Week Pass, a Monthly plan and an Annual Desktop+Web plan lift those limits.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no passes or subscriptions.", competitor: "Web Week Pass $5 for 7 days; Web Monthly $7.50 per user a month; Desktop+Web Annual $63 per user a year.", sourceUrl: "https://www.sejda.com/pricing" },
      { label: "Free-use limits", privatools: "No hourly allowance; OCR and heavy conversions such as PDF to Word are limited to about five runs a minute.", competitor: "Most free web tools: documents up to 200 pages or 50 MB, and 3 tasks per hour.", sourceUrl: "https://www.sejda.com/pdf-editor" },
      { label: "Paid limits", privatools: "The same limits for everyone: 500 MB per request, about 250 MB per file on most pages.", competitor: "No page or hourly limits, files up to 500 MB each, OCR up to 100 pages, up to 21 minutes per task.", sourceUrl: "https://www.sejda.com/pricing" },
      { label: "Where files are processed", privatools: "Most PDF tools run on PrivaTools' server, or on your own if you self-host; there is no desktop app.", competitor: "Sejda Desktop processes files on your computer rather than uploading them; Sejda Web uses its servers.", sourceUrl: "https://www.sejda.com/en/desktop" },
      { label: "Retention", privatools: "Removed after the response, with a sweep for leftovers older than ten minutes.", competitor: "Tool pages say files are deleted automatically after 2 hours.", sourceUrl: "https://www.sejda.com/compress-pdf" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "The Desktop licence agreement says the software is not open source.", sourceUrl: "https://www.sejda.com/eula" },
      { label: "Platforms", privatools: "Any modern browser; installable as a web app.", competitor: "Desktop for Mac (Intel and Apple silicon), Windows and Linux (.deb and .rpm), plus Chromebooks via Linux.", sourceUrl: "https://www.sejda.com/en/desktop" },
      { label: "Editing", privatools: "Edit PDF adds text, drawings, images and whiteout over the page.", competitor: "Its tool menu lists editing existing PDF text.", sourceUrl: "https://www.sejda.com/" },
    ],
    sections: [
      { heading: "How the free limits work", body: [
        "Sejda's tool pages state its free web limits. Most accept documents up to 200 pages or 50 MB, Merge up to 50 pages or 50 MB, compression up to 100 MB and OCR up to 10 pages, each with three tasks per hour. The free Desktop tier allows three tasks per day. A Week Pass lifts the web limits for seven days as a one-time charge that does not renew, and prices are in US dollars with tax calculated at checkout.",
        "PrivaTools has no task allowance to spend. Its limits are technical instead: 500 MB per upload request, about 250 MB per file on most tool pages, about five runs a minute from one visitor on heavy jobs such as OCR and PDF to Word, and a 60-second wait on several of those pages, upload included. With nothing to buy, there is also no paid route past those limits on the public site.",
      ] },
      { heading: "Editing, splitting and scans", body: [
        "If you need to change words that are already in a PDF, Sejda lists existing-text editing; PrivaTools' Edit PDF places new text, shapes, images and whiteout on top of the page instead. Both split by bookmarks, by size and by text, and both straighten skewed scans and run OCR. Sejda also lists workflows, Bates numbering and a forms tool that can detect the fields in a static PDF form and make them fillable; PrivaTools has Bates numbering, a pipeline that chains PDF steps and a form creator where you place the fields yourself.",
      ] },
    ],
    chooseCompetitor: ["You need to edit the existing text of a PDF, not only add to it.", "You want a desktop app that processes documents on your computer, on Windows, macOS or Linux.", "Three tasks an hour are enough, or a short paid pass fits an occasional project.", "You want a form tool that finds the fields in a static PDF for you."],
    choosePrivaTools: ["You run more than a few jobs an hour and would rather not buy a pass.", "You want the code open, and the option to run the service yourself.", "Your files include images, audio or video as well as PDFs."],
    tradeoffs: ["Its licence agreement says Sejda Desktop contacts Sejda's servers to download OCR language data.", "Long PrivaTools OCR or PDF to Word jobs must finish within a 60-second wait; Sejda's paid plans allow up to 21 minutes per task.", "We did not benchmark either product's output."],
    sources: [
      { label: "Sejda pricing and plans", url: "https://www.sejda.com/pricing" },
      { label: "Sejda PDF editor and free limits", url: "https://www.sejda.com/pdf-editor" },
      { label: "Sejda merge tool limits", url: "https://www.sejda.com/merge-pdf" },
      { label: "Sejda compress tool and file deletion", url: "https://www.sejda.com/compress-pdf" },
      { label: "Sejda OCR limits", url: "https://www.sejda.com/ocr-pdf" },
      { label: "Sejda PDF forms", url: "https://www.sejda.com/pdf-forms" },
      { label: "Sejda Desktop", url: "https://www.sejda.com/en/desktop" },
      { label: "Sejda Desktop licence agreement", url: "https://www.sejda.com/eula" },
      { label: "Sejda tools", url: "https://www.sejda.com/" },
      { label: "Sejda press page", url: "https://www.sejda.com/press" },
    ],
    relatedLinks: [{ label: "Edit PDF", url: "/tool/edit-pdf" }, { label: "Split by Bookmarks", url: "/tool/split-by-bookmarks" }, { label: "Split by Text", url: "/tool/split-by-text" }, { label: "PrivaTools and Sejda: choosing a PDF editor", url: "/blog/privatools-vs-sejda" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "pdf24", name: "PDF24",
    title: "PrivaTools vs PDF24: free tools, EU servers and Creator",
    description: "PDF24 is free and funded by advertising, with online tools on EU servers and an offline Windows app; PrivaTools is open source. Costs and data paths compared.",
    summary: "Both are free. PDF24 pays for its online tools with advertising, processes uploads on servers in the EU and offers PDF24 Creator, a free Windows program that works offline and adds a virtual PDF printer. PrivaTools shows no advertising, runs some tools in your browser and the rest on its server, covers media and developer tasks as well as PDFs, and its own code is open source and self-hostable.",
    category: "Desktop & teams",
    highlights: ["Advertising-funded free tools, against free tools without ads.", "A free offline Windows app, against a browser app you can self-host.", "Files deleted within an hour on PDF24's servers, against cleanup after each response."],
    overview: [
      "PDF24, from Geek Software GmbH, offers PDF24 Online Tools in the browser, which can also be installed as an app, and PDF24 Creator, an application for Windows. Its FAQ says the tools are free for everyone, including companies, and are financed by discreet advertising on its websites. The terms for its online services, which do not apply to PDF24 Creator or PDF24 Fax, allow commercial use when document processing is not itself the core of your business, rule out automated scripts, and note that free provision is not guaranteed in future.",
      "The online tools process files on PDF24's servers. Its FAQ says those servers are in EU data centres and that files are deleted automatically within one hour of processing, and a data processing agreement is available on request. PDF24 Creator works offline and keeps files on your PC, adding a virtual PDF printer, scanner and camera import, and screen capture.",
    ],
    features: [
      { label: "Price", privatools: "Free, without advertising or a paid tier.", competitor: "Free for everyone, including companies, and financed by advertising on its websites.", sourceUrl: "https://tools.pdf24.org/en/faq" },
      { label: "Terms of use", privatools: "Fair-use rate limits; the terms allow reasonable API use with a free key.", competitor: "For the online services: commercial use only if processing documents is not your core business, and no automated scripts.", sourceUrl: "https://www.pdf24.org/en/terms-of-use" },
      { label: "Limits", privatools: "Server requests are capped at 500 MB, which means about 250 MB per file on most tool pages.", competitor: "Its tools page says PDF24 has no artificial limits.", sourceUrl: "https://tools.pdf24.org/en/" },
      { label: "Where files are processed", privatools: "In your browser or on PrivaTools' server with temporary storage, depending on the tool.", competitor: "Online Tools use PDF24 servers in EU data centres; Creator works offline on your PC.", sourceUrl: "https://tools.pdf24.org/en/faq" },
      { label: "Retention", privatools: "Temporary files go when the response is sent; a background sweep removes anything older than ten minutes.", competitor: "Deleted automatically within one hour after processing, or manually straight away.", sourceUrl: "https://tools.pdf24.org/en/faq" },
      { label: "Account", privatools: "Not needed.", competitor: "No registration required.", sourceUrl: "https://tools.pdf24.org/en/merge-pdf" },
      { label: "Platforms", privatools: "Any modern browser; installable as a web app.", competitor: "The online tools install as an app on phones, tablets and computers; the offline PDF24 Creator is for Windows.", sourceUrl: "https://tools.pdf24.org/en/install-app" },
    ],
    sections: [
      { heading: "Offline work on Windows", body: [
        "PDF24 Creator is the main difference. It installs on Windows, brings the PDF24 tools as an offline version, and adds features a website cannot: virtual PDF printers that turn anything you can print into a PDF, import from a scanner or camera, screen capture and an entry in File Explorer's context menu. Its manual also documents a command line for processing files in scripts.",
        "PrivaTools has no desktop program. It runs in the browser on any operating system and installs as a web app; browser-only tools you have opened can keep working offline, but PDF conversions and OCR on the server need a connection. To keep everything on your own machine, you can run the Docker Compose project yourself.",
      ] },
      { heading: "Where uploads go", body: [
        "PDF24's online tools send files to its processing servers, which its FAQ places in EU data centres, and delete them within an hour; its privacy policy allows longer storage when processing takes longer than that. PrivaTools' server tools write uploads and results to temporary per-request files, remove them when the response has been sent, and sweep up leftovers older than ten minutes. If you need to control where processing happens, you can host PrivaTools on your own infrastructure.",
      ] },
    ],
    chooseCompetitor: ["You work on Windows and want a free offline PDF program with a virtual printer.", "You scan or photograph paper documents straight into a PDF on your PC.", "You want uploads handled in EU data centres, with a data processing agreement on request."],
    choosePrivaTools: ["You would rather use a free service that shows no advertising.", "You want to automate jobs through a documented API with a free key.", "You want to read or change the code, or run the service on your own server.", "You need image, audio, video or developer tools alongside PDF work."],
    tradeoffs: ["PDF24's Creator manual documents a setting that stops Creator from using the online converter when no local converter is available; check it if files must stay on the PC.", "PrivaTools' heavy tools take about five runs a minute from one visitor, and several of their pages stop waiting after 60 seconds.", "We did not benchmark output quality for either product."],
    sources: [
      { label: "PDF24 FAQ", url: "https://tools.pdf24.org/en/faq" },
      { label: "PDF24 Creator", url: "https://tools.pdf24.org/en/creator" },
      { label: "PDF24 terms of use for online services", url: "https://www.pdf24.org/en/terms-of-use" },
      { label: "PDF24 privacy policy", url: "https://www.pdf24.org/en/privacy-policy" },
      { label: "PDF24 Online Tools", url: "https://tools.pdf24.org/en/" },
      { label: "Install PDF24 Tools as an app", url: "https://tools.pdf24.org/en/install-app" },
      { label: "PDF24 merge tool", url: "https://tools.pdf24.org/en/merge-pdf" },
      { label: "PDF24 Creator manual", url: "https://creator.pdf24.org/manual/11/" },
    ],
    relatedLinks: [{ label: "Office to PDF", url: "/tool/office-to-pdf" }, { label: "OCR PDF", url: "/tool/ocr-pdf" }, { label: "Compress PDF", url: "/tool/compress-pdf" }, { label: "Where your files go when you run a tool", url: "/blog/where-your-files-go" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "foxit", name: "Foxit PDF Editor",
    title: "PrivaTools vs Foxit PDF Editor: plans, AI credits and apps",
    description: "Foxit PDF Editor costs from $129.99 a year, with a perpetual option and free online converters; PrivaTools is free and open source. Editing and AI compared.",
    summary: "Foxit sells PDF Editor and PDF Editor+ subscriptions and a perpetual licence, with desktop apps for Windows and macOS, a web version and, on Editor+, mobile apps. It edits existing text with reflow, runs OCR, compares versions and handles certificate signatures, and every Foxit account gets monthly AI credits. Its free online converters need no account. PrivaTools needs no account either, but it does not edit existing text or collect signatures, and it has no desktop app.",
    category: "Desktop & teams",
    highlights: ["Paid editing from $129.99 a year or a $209.99 perpetual licence, against free.", "Local AI in Foxit's desktop apps; PrivaTools offers on-device models in the browser.", "Signature requests on PDF Editor+, which PrivaTools does not offer."],
    overview: [
      "Foxit's pricing page lists Foxit PDF Editor at $129.99 per user a year and PDF Editor+ at $159.99, with monthly billing from $10.99, and a perpetual licence, Foxit PDF Editor 14, for a one-time $209.99. The perpetual version leaves out AI Assistant, Workspace, Smart Redact, its document management system and cloud features. Every plan starts with a 14-day free trial without a credit card, and Foxit PDF Reader is free.",
      "Foxit's online converters need no account and run on its cloud servers; its privacy policy says uploads are deleted once processing is complete and outputs typically within a day. Every Foxit account includes 300 AI credits a month, and a release on 1 September 2026 added support for Local AI, which runs on the device in the Windows and macOS apps. Foxit says uploaded PDFs are encrypted with TLS in transit and AES-256 at rest.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no subscription or licence to buy.", competitor: "PDF Editor $129.99 and PDF Editor+ $159.99 per user a year; perpetual PDF Editor 14 for $209.99.", sourceUrl: "https://www.foxit.com/pdf-editor/pricing/" },
      { label: "Free options", privatools: "Every tool is free without an account.", competitor: "PDF Reader is free, and a 14-day PDF Editor+ trial needs no credit card.", sourceUrl: "https://www.foxit.com/pdf-editor/free-pdf/" },
      { label: "Online file limits", privatools: "About 250 MB per file on most pages, but PDF to Word and OCR stop waiting after 60 seconds.", competitor: "The online PDF to Word converter takes files up to 15 MB; Foxit says its desktop version handles higher limits.", sourceUrl: "https://www.foxit.com/pdf-to-word/" },
      { label: "Where files are processed", privatools: "On PrivaTools' server for PDF conversion and OCR, or in your browser for tools labelled as local.", competitor: "Online tools run on Foxit's cloud; uploads are deleted after processing, outputs typically within a day.", sourceUrl: "https://www.foxit.com/company/privacy-policy/" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "The online converters need no installation or account.", sourceUrl: "https://www.foxit.com/pdf-converter/" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "Licensed, not sold; the EULA calls its source code a trade secret.", sourceUrl: "https://www.foxit.com/pdf-editor/eula/" },
      { label: "Platforms", privatools: "Any modern browser; installable as a web app.", competitor: "PDF Editor on Windows, macOS and the web; PDF Editor+ adds iOS and Android.", sourceUrl: "https://www.foxit.com/pdf-editor/" },
      { label: "AI", privatools: "On-device models for summaries, translation and transcription, or your own provider key; Background Remover also runs on PrivaTools' server.", competitor: "300 AI credits a month with any Foxit account, and Local AI that runs on the device in its desktop apps.", sourceUrl: "https://www.foxit.com/ai/" },
      { label: "Editing", privatools: "Adds content over the page; existing text is not edited.", competitor: "Edits text and images with full-page paragraph reflow; OCR, comparison and certificate signatures.", sourceUrl: "https://www.foxit.com/pdf-editor/pricing/" },
    ],
    sections: [
      { heading: "Editing and document work", body: [
        "Foxit PDF Editor is a full editor. Its plans list editing text and images with paragraph reflow, OCR that makes scans searchable and editable, version comparison, fillable form creation, accessibility validation, PDF/A conversion and validation, and certificate signatures. PDF Editor+ adds Smart Redact and signature requests with tracking, and the product page lists 150 e-signature envelopes a year on Editor+. It integrates with Microsoft 365, SharePoint, Google Drive, Box, OneDrive and Salesforce.",
        "PrivaTools keeps these jobs separate and free: Compare PDF, Form Creator, OCR PDF, Redact PDF and the Accessibility Checker. It cannot edit existing text or apply certificate signatures, and its PDF to PDF/A tool labels a file as PDF/A-2b without validating it.",
      ] },
      { heading: "Online tools and AI", body: [
        "Foxit's free online converters run on its servers, and each sets its own size cap: PDF to Word and OCR take 15 MB, merging 20 MB per file and compression 150 MB. Its cloud AI features use Microsoft Azure: the privacy policy says Document Intelligence and OCR data is deleted within 24 hours and data sent to Azure AI Language is kept for up to 48 hours, while Local AI in the desktop apps works without an internet connection.",
        "PrivaTools' AI either runs in your browser with downloaded models, for summaries, translation, transcription and detecting personal data, or goes from your browser to a provider you choose, with your own key; Background Remover's default engine runs on PrivaTools' own server. There are no credits to buy.",
      ] },
    ],
    chooseCompetitor: ["You edit existing PDF text and images daily and want a desktop editor for Windows or macOS.", "You prefer a one-time perpetual licence to a subscription.", "You need signature requests, Smart Redact or integrations with SharePoint or Salesforce.", "You want AI that runs on your computer inside a desktop editor."],
    choosePrivaTools: ["You need redaction or page editing without a licence or trial.", "Your files exceed the caps of Foxit's free online converters and you do not want the desktop editor.", "You want image, audio, video and developer tools, and code you can host."],
    tradeoffs: ["The prices here are Foxit's published US list rates; local prices and taxes can differ.", "PrivaTools' PDF to Word and OCR pages give up after 60 seconds, upload included, so a large file on a slow connection can fail.", "We did not benchmark editing quality or OCR accuracy."],
    sources: [
      { label: "Foxit PDF Editor pricing", url: "https://www.foxit.com/pdf-editor/pricing/" },
      { label: "Foxit PDF Editor", url: "https://www.foxit.com/pdf-editor/" },
      { label: "Foxit free trial and PDF Reader", url: "https://www.foxit.com/pdf-editor/free-pdf/" },
      { label: "Foxit online PDF converter", url: "https://www.foxit.com/pdf-converter/" },
      { label: "Foxit PDF to Word", url: "https://www.foxit.com/pdf-to-word/" },
      { label: "Foxit OCR PDF", url: "https://www.foxit.com/ocr-pdf/" },
      { label: "Foxit compress PDF", url: "https://www.foxit.com/compress-pdf/" },
      { label: "Foxit merge PDF", url: "https://www.foxit.com/merge-pdf/" },
      { label: "Foxit AI", url: "https://www.foxit.com/ai/" },
      { label: "Foxit PDF Editor version history", url: "https://www.foxit.com/pdf-editor/version-history.html" },
      { label: "Foxit privacy policy", url: "https://www.foxit.com/company/privacy-policy/" },
      { label: "Foxit PDF Editor licence agreement", url: "https://www.foxit.com/pdf-editor/eula/" },
    ],
    relatedLinks: [{ label: "OCR PDF", url: "/tool/ocr-pdf" }, { label: "Compare PDF", url: "/tool/compare-pdf" }, { label: "Accessibility Checker", url: "/tool/accessibility-check" }, { label: "Form Creator", url: "/tool/form-creator" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "lightpdf", name: "LightPDF",
    title: "PrivaTools vs LightPDF: AI credits, free limits and apps",
    description: "LightPDF pairs PDF tools with AI paid for in credits, and its free plan starts with sign-up; PrivaTools' document AI uses your own key or on-device models.",
    summary: "LightPDF combines PDF editing and conversion with AI features, including an AI agent, document chat and a document generator, across the web, Windows, Mac, Android and iOS. Its free web plan starts with sign-up and caps files at 10 MB and AI use at a few requests a day; paid plans remove the file-size cap and include AI credits, 1,000 a month on monthly and yearly plans or 40,000 on the lifetime plan. PrivaTools needs no account and brings document AI through on-device models or your own provider key.",
    category: "Document AI",
    highlights: ["AI paid for in credits, against your own provider key or on-device models.", "A free plan that starts with sign-up and caps files at 10 MB; PrivaTools needs no account.", "Apps for Windows, Mac and mobile, against a browser app."],
    overview: [
      "LightPDF, a registered trademark of Wangxu Technology in Shenzhen, offers online PDF tools with desktop and mobile apps; its pricing page says one premium account works across Windows, Mac, Android, iOS and the web. Its AI features include an AI agent that carries out document tasks from instructions, ChatPDF for questions about documents, translation and an AI PDF generator.",
      "Payment terms that took effect in January 2026 introduced credits, which pay for conversion tools and AI features. Monthly and yearly plans include 1,000 credits a month that expire, and the lifetime plan includes 40,000 credits, valid until used. The free plan is web only and starts with sign-up, while its ChatPDF page describes free use without signing in; LightPDF's licence agreement describes its software as a proprietary product.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no credits to buy.", competitor: "A free web plan; monthly, yearly and lifetime plans; team plans priced by the number of users.", sourceUrl: "https://lightpdf.com/pricing" },
      { label: "Free-plan limits", privatools: "No account or daily count; each heavy tool allows about five runs a minute.", competitor: "Free: files up to 10 MB, AI agent 3 questions a day, ChatPDF 1 file a day, no batch processing; paid plans lift the size cap.", sourceUrl: "https://lightpdf.com/pricing" },
      { label: "AI", privatools: "Your own key with a provider you choose, such as Anthropic, OpenAI or Gemini, or a local server; or on-device models.", competitor: "AI agent, ChatPDF, translation and a document generator, paid in credits: 1,000 a month, or 40,000 on the lifetime plan.", sourceUrl: "https://lightpdf.com/pricing" },
      { label: "Where files are processed", privatools: "Chat with PDF extracts text in your browser; PDF conversions run on PrivaTools' server in temporary storage.", competitor: "Its user guide says processed files are stored temporarily on its servers and deleted regularly.", sourceUrl: "https://lightpdf.com/help-documentation.html" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "The free plan starts with sign-up.", sourceUrl: "https://lightpdf.com/pricing" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "Its licence agreement calls the software a proprietary product of LightPDF.", sourceUrl: "https://lightpdf.com/license-agreement" },
      { label: "Platforms", privatools: "Any modern browser; installable as a web app.", competitor: "One premium account across Windows, Mac, Android, iOS and the web; the free plan is web only.", sourceUrl: "https://lightpdf.com/pricing" },
      { label: "Signatures", privatools: "Visible signature images you place yourself; no certificate signing.", competitor: "Web e-sign sends signature requests but is not a certificate-based signature service.", sourceUrl: "https://lightpdf.com/esign-pdf" },
    ],
    sections: [
      { heading: "AI in the plan or on your own key", body: [
        "LightPDF includes AI in its plans and meters it in credits: its pricing page lists 20 credits per ChatPDF chat, 5 per AI chat with the AI agent, whose other tasks vary in cost, and 5 a page for translation, or 40 a page for scanned PDFs, with extra credits for sale. Free users get three AI agent questions a day and one ChatPDF file a day of up to 100 pages.",
        "PrivaTools does not resell AI. Chat with PDF, and the provider modes of Summarize, Translate and Transcribe, send requests from your browser straight to the provider whose key you add, and that provider bills you. Summarize, Translate and Transcribe can also run on-device models after a one-time download, with nothing sent to a provider.",
      ] },
      { heading: "Where documents are kept", body: [
        "LightPDF describes retention per tool. Its user guide says processed files are stored temporarily and deleted regularly; its online editor page says operations are handled in your browser and that files are encrypted on its cloud servers for 24 hours; its merge page says each uploaded file is deleted instantly after the changes are done; and ChatPDF keeps documents in encrypted cloud storage until you delete them. The free plan includes cloud storage of five files for a year.",
        "PrivaTools has no cloud storage. Server tools write inputs and results to temporary per-request files that are removed after the response, with a background sweep for leftovers older than ten minutes; only API background jobs keep a result, for up to an hour. The copies that remain are the ones you download.",
      ] },
    ],
    chooseCompetitor: ["You want AI features included in a plan, without managing a provider key.", "You want one account across Windows, Mac, Android, iOS and the web.", "You want an AI agent that runs a chain of PDF tasks from one instruction."],
    choosePrivaTools: ["You want to use every tool without creating an account.", "You already pay an AI provider, or want on-device models, and prefer not to buy credits.", "You want open code and the option to self-host."],
    tradeoffs: ["PrivaTools' Chat with PDF needs your own provider key, and that provider's terms and charges apply.", "PrivaTools' conversions cost nothing but are rate-limited, at about five runs a minute on heavy tools.", "AI answers from either product need checking against the document; we did not test their accuracy."],
    sources: [
      { label: "LightPDF pricing and plan limits", url: "https://lightpdf.com/pricing" },
      { label: "LightPDF web user guide", url: "https://lightpdf.com/help-documentation.html" },
      { label: "LightPDF ChatPDF", url: "https://lightpdf.com/chatdoc" },
      { label: "LightPDF AI agent", url: "https://lightpdf.com/pdf-ai-agent" },
      { label: "LightPDF e-sign", url: "https://lightpdf.com/esign-pdf" },
      { label: "LightPDF online editor", url: "https://lightpdf.com/edit-pdf" },
      { label: "LightPDF merge PDF", url: "https://lightpdf.com/merge-pdf" },
      { label: "LightPDF licence agreement", url: "https://lightpdf.com/license-agreement" },
      { label: "LightPDF payment terms", url: "https://lightpdf.com/vip-agreement" },
      { label: "LightPDF terms", url: "https://lightpdf.com/terms" },
    ],
    relatedLinks: [{ label: "Chat with PDF", url: "/tool/chat-with-pdf" }, { label: "Summarize PDF", url: "/tool/summarize-pdf" }, { label: "Translate PDF", url: "/tool/translate-pdf" }, { label: "Bring your own AI key", url: "/blog/bring-your-own-ai-key-guide" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "stirling-pdf", name: "Stirling PDF",
    title: "PrivaTools vs Stirling PDF: two self-hostable toolkits",
    description: "Stirling PDF is an open-core PDF editor with desktop apps and paid Team plans; PrivaTools is a web toolbox whose own code is MIT-licensed. Plans compared.",
    summary: "Both can run on your own server. Stirling PDF is a PDF-focused editor that also ships desktop apps for Windows, macOS and Linux, and sells Team and Enterprise licences for larger self-hosted installations. PrivaTools covers PDFs plus images, audio, video and developer utilities in one web app, with its own code under the MIT licence and no paid tier.",
    category: "Local & self-hosted",
    highlights: ["Open-core licensing with paid tiers; PrivaTools' own code is MIT, with no paid tier.", "Desktop apps with a local mode, against a browser app you install as a PWA.", "SAML sign-in and audit logs on Stirling Enterprise, which PrivaTools does not offer."],
    overview: [
      "Stirling PDF's README calls it open-core: its repository is MIT-licensed except for listed directories that carry a proprietary Stirling PDF User License, and production use of that proprietary code needs a valid licence. It offers desktop apps for Windows, macOS and Linux, self-hosting with Docker, Kubernetes or a Java .jar, and a hosted version at stirling.com/app.",
      "Its pricing page lists a Free plan at $0 a month, a Team plan at $99 a month with 100 users included, an Enterprise plan on custom terms, and a PDF Processor billed at 1 cent per credit. Its documentation adds that a Team licence covers one installation, that the free plan covers up to five users and already includes OAuth2 single sign-on with Google, GitHub, Keycloak or any OIDC provider, and that SAML sign-in and audit logs come with Enterprise.",
    ],
    features: [
      { label: "Price", privatools: "Free to use and to self-host, with nothing to license.", competitor: "Free plan at $0 a month; Team at $99 a month with 100 users; Enterprise on custom terms.", sourceUrl: "https://www.stirling.com/pricing" },
      { label: "Free tier", privatools: "No user or seat limit, on the public site or your own server.", competitor: "The Free plan covers up to 5 users, with all PDF operations and OAuth2 single sign-on; more users need Team or Enterprise.", sourceUrl: "https://docs.stirlingpdf.com/Paid-Offerings/" },
      { label: "File size", privatools: "500 MB per upload request on the public site; the web app caps each file at 500 MB even when self-hosted.", competitor: "Self-hosted installs default to a 2,000 MB upload limit, which administrators can change.", sourceUrl: "https://docs.stirlingpdf.com/Configuration/" },
      { label: "Where files are processed", privatools: "In your browser for browser-only tools, otherwise on privatools.me or your own server.", competitor: "The desktop app runs its Ultra-Lite tools on your device, fully offline; OCR, Office conversions and other Full-only tools need Stirling Cloud or your own server.", sourceUrl: "https://docs.stirlingpdf.com/Installation/Versions/" },
      { label: "Account", privatools: "Not needed on the public site; a self-hosted copy signs in through Clerk or legacy local accounts.", competitor: "The Docker image turns login on by default, and you can switch it off.", sourceUrl: "https://docs.stirlingpdf.com/Installation/Docker%20Install/" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT; some dependencies, such as PyMuPDF under the AGPL, keep their own licences.", competitor: "Open-core: MIT outside listed directories, which carry a proprietary licence.", sourceUrl: "https://github.com/Stirling-Tools/Stirling-PDF/blob/main/LICENSE" },
      { label: "Platforms", privatools: "Web app and PWA; self-host with Docker Compose.", competitor: "Desktop apps for Windows, Mac and Linux; Docker, Kubernetes or a .jar on a server.", sourceUrl: "https://www.stirling.com/download" },
      { label: "Team administration", privatools: "Optional accounts, with Google or GitHub sign-in through Clerk, issue API keys; no roles, SAML or audit logs.", competitor: "OAuth2 single sign-on with Google, GitHub, Keycloak or any OIDC provider on every plan, Free included; SAML sign-in and audit logs on Enterprise.", sourceUrl: "https://docs.stirlingpdf.com/Paid-Offerings/" },
    ],
    sections: [
      { heading: "Licences and what you pay for", body: [
        "Stirling PDF's free tier suits individuals and small groups: its documentation limits the free plan to five users, who can already sign in with OAuth2 single sign-on, and says a Team licence, at $99 a month, covers one installation with 100 users. Enterprise adds SAML sign-in, audit logs, SCIM provisioning and air-gapped deployment. Because proprietary directories sit inside an otherwise MIT repository, check which features your deployment uses before assuming all of it is freely licensed.",
        "PrivaTools has no licence tiers. The same code runs the public site and any copy you host, its own code is MIT-licensed, and nothing is unlocked by payment. The trade-off is that PrivaTools has no organisation features: accounts exist to issue developer API keys, not to manage teams.",
      ] },
      { heading: "Running it yourself", body: [
        "Stirling documents Docker, Kubernetes with Helm, bare-metal .jar installs and managed desktop deployments, where IT pre-configures desktop installs through device-management tools. Its automation includes a REST API, pipelines, folder scanning and an MCP server for AI assistants, and its 2.14 release added desktop signing with USB tokens and smart cards. PrivaTools ships as a Docker Compose project whose heavy tools rely on bundled engines such as LibreOffice, Tesseract and FFmpeg, so plan for their CPU and memory use.",
        "On the public PrivaTools site you run nothing: browser-only tools keep their input on the device, and server tools upload to temporary storage that is cleaned after the response.",
      ] },
    ],
    chooseCompetitor: ["You want a PDF editor that also runs as a desktop app on Windows, macOS or Linux.", "You want user accounts with OAuth2 single sign-on, or can budget for Enterprise to add SAML sign-in and audit logs.", "You want to automate PDF work with its pipelines, folder scanning or REST API on your own server.", "You need certificate signing from a USB token or smart card on the desktop."],
    choosePrivaTools: ["You want no paid tiers or seat counts to track.", "Your work mixes PDFs with images, audio, video, archives and developer utilities.", "You want AI features that run on your device or with your own provider key.", "You would like to try a public site first and self-host later with the same tools."],
    tradeoffs: ["Self-hosting either product makes you responsible for updates, backups, logs and capacity, and for how the copy you run handles files.", "PrivaTools' own code is MIT-licensed, but it depends on libraries with other licences, including PyMuPDF under the AGPL; check them before you redistribute a modified copy or run one as a network service, which the AGPL also covers.", "We did not benchmark conversion quality, OCR accuracy or speed for either product."],
    sources: [
      { label: "Stirling PDF pricing", url: "https://www.stirling.com/pricing" },
      { label: "Stirling PDF downloads and deployment", url: "https://www.stirling.com/download" },
      { label: "Stirling PDF modes", url: "https://docs.stirlingpdf.com/Modes%20and%20Licensing/" },
      { label: "Stirling PDF versions and desktop tools", url: "https://docs.stirlingpdf.com/Installation/Versions/" },
      { label: "Stirling PDF paid offerings", url: "https://docs.stirlingpdf.com/Paid-Offerings/" },
      { label: "Stirling PDF configuration", url: "https://docs.stirlingpdf.com/Configuration/" },
      { label: "Stirling PDF Docker installation", url: "https://docs.stirlingpdf.com/Installation/Docker%20Install/" },
      { label: "Stirling PDF managed desktop deployment", url: "https://docs.stirlingpdf.com/Installation/Managed%20Deployment/" },
      { label: "Stirling PDF README", url: "https://github.com/Stirling-Tools/Stirling-PDF" },
      { label: "Stirling PDF licence file", url: "https://github.com/Stirling-Tools/Stirling-PDF/blob/main/LICENSE" },
      { label: "Stirling PDF documentation", url: "https://docs.stirlingpdf.com/" },
      { label: "Stirling PDF v2.14.0 release notes", url: "https://github.com/Stirling-Tools/Stirling-PDF/releases/tag/v2.14.0" },
    ],
    relatedLinks: [{ label: "Developer API", url: "/api" }, { label: "Build a PDF pipeline", url: "/pipeline" }, { label: "Where your files go when you run a tool", url: "/blog/where-your-files-go" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "dochub", name: "DocHub",
    title: "PrivaTools vs DocHub: signing, forms and free-plan limits",
    description: "DocHub is an online editor for signing and forms, with three free uses a month of core features; PrivaTools needs no account but has no sign requests.",
    summary: "DocHub is a web editor built around signing: sign requests, envelopes, templates and an audit trail, with iOS and Android apps and integrations with Google Drive, Gmail, Dropbox and OneDrive. Its free plan shares three uses a month across core features and its merge tool needs a free account to download; Pro makes PDF editing and sign requests unlimited. PrivaTools needs no account and has form and signature tools, but no sign requests, audit trail or document library.",
    category: "Signing & forms",
    highlights: ["Signature requests and audit trails, which PrivaTools does not offer.", "Three uses a month of core features on DocHub's free plan; PrivaTools has no monthly count.", "Documents stored on AWS there; PrivaTools keeps only temporary copies."],
    overview: [
      "DocHub is an online PDF editor and e-signature service listed among airSlate's products. It lets you edit and annotate PDFs, build reusable templates and fillable fields, send sign requests and envelopes, and keep an audit trail; its legal page says its e-signatures comply with the US ESIGN Act and UETA. It needs no installation, and its integrations page lists Google Drive, Gmail, Dropbox, OneDrive, Box and Google Classroom, plus Chrome and Edge extensions.",
      "The pricing page lists a Free plan, Basic, Pro and a Site License for enterprises. Documents are stored in encrypted AWS S3 storage; its subprocessor list names Amazon Web Services in the United States, Germany and Australia, and its privacy notice says the service depends on data transfers to the United States. Its help centre says uploaded files must be under 30 MB and fewer than 1,000 pages.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no plans or trials.", competitor: "Free plan; Basic and Pro billed monthly or yearly; Site License by quote.", sourceUrl: "https://dochub.com/pricing" },
      { label: "Free-plan limits", privatools: "No monthly allowance on the website.", competitor: "Core features, including text editing, self-signing, sign requests and templates, share 3 uses a month; Pro makes editing and sign requests unlimited.", sourceUrl: "https://dochub.com/pricing" },
      { label: "File size", privatools: "Uploads of up to 500 MB per request, so roughly 250 MB for a single file on most pages.", competitor: "Files under 30 MB and fewer than 1,000 pages.", sourceUrl: "https://help.dochub.com/knowledge-base/creating-importing-downloading-and-exporting-documents/uploading-documents-and-pdfs-to-dochub" },
      { label: "Where documents are kept", privatools: "No document library; server tools use temporary per-request files.", competitor: "Stored on Amazon Web Services and encrypted at rest.", sourceUrl: "https://dochub.com/site/security" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "A free account is needed to download the result of its merge tool.", sourceUrl: "https://merge-pdf.dochub.com" },
      { label: "Licence", privatools: "PrivaTools' own code is MIT-licensed, and you can self-host it.", competitor: "Its terms grant a limited, non-exclusive licence to use the service.", sourceUrl: "https://legal.dochub.com/terms" },
      { label: "Platforms", privatools: "Any modern browser; installable as a web app.", competitor: "Web, with iOS and Android apps included in the free plan.", sourceUrl: "https://dochub.com/pricing" },
      { label: "Signing", privatools: "Sign PDF and E-Sign PDF place your own signature image; no requests or audit trail.", competitor: "E-signatures its legal page says comply with ESIGN and UETA, with an audit trail.", sourceUrl: "https://dochub.com/site/legal" },
    ],
    sections: [
      { heading: "Signing with other people", body: [
        "DocHub is built for documents other people sign. You can send sign requests and envelopes, share templates so that each recipient completes a copy, and signers do not need a DocHub account. Its legal page says each audit trail includes a SHA-256 identifier stored in Bitcoin's blockchain for verification. Pro adds unlimited sign requests, bulk sending and in-person signing.",
        "PrivaTools stops at your own signature. Sign PDF places a drawn or uploaded signature image, E-Sign PDF can also set a typed name in a script style, Form Creator adds fillable fields including signature fields, and Fill Form completes existing fields. There is no way to send a document for signature, track it or produce a certificate of completion.",
      ] },
      { heading: "The free plan in practice", body: [
        "DocHub's free plan suits occasional use: its core features share a limit of three uses a month, and Basic keeps that cap on selected Pro features while adding unlimited downloads, self-signing and templates. Pro makes PDF editing and sign requests unlimited.",
        "PrivaTools has no monthly allowance, but it has other limits: 500 MB per upload request, lower caps on some tools, such as 200 MB for Mute Video and Trim Media, a 60-second wait on pages such as OCR and PDF to Word, a five-minute limit on the server, and about five runs a minute on heavy tools. It also has no account to keep documents in, so download a completed form before you leave the page.",
      ] },
    ],
    chooseCompetitor: ["You send documents to other people for signature and need an audit trail.", "Your documents live in Google Drive or Gmail and you want to sign them there.", "You reuse templates that several people complete and sign.", "You want to change existing PDF text in a web editor."],
    choosePrivaTools: ["You need a conversion, page operation or form fill without creating an account.", "You would use core features such as editing and signing more than three times a month, without a subscription.", "You want conversions, OCR, compression and media tools alongside PDF editing."],
    tradeoffs: ["A visible signature image and a tracked signature request are different things; if you need proof of who signed and when, PrivaTools is not the right tool.", "We did not benchmark either editor."],
    sources: [
      { label: "DocHub pricing and plan comparison", url: "https://dochub.com/pricing" },
      { label: "DocHub security", url: "https://dochub.com/site/security" },
      { label: "DocHub legal and e-signature compliance", url: "https://dochub.com/site/legal" },
      { label: "DocHub help: uploading documents", url: "https://help.dochub.com/knowledge-base/creating-importing-downloading-and-exporting-documents/uploading-documents-and-pdfs-to-dochub" },
      { label: "DocHub help: sign requests", url: "https://help.dochub.com/knowledge-base/document-signing-and-sign-requests/sign-requests-getting-started" },
      { label: "DocHub merge PDF", url: "https://merge-pdf.dochub.com" },
      { label: "DocHub terms", url: "https://legal.dochub.com/terms" },
      { label: "DocHub privacy notice", url: "https://legal.dochub.com/privacy-notice" },
      { label: "DocHub subprocessors", url: "https://legal.dochub.com/subprocessors" },
      { label: "DocHub integrations", url: "https://www.dochub.com/en/integrations" },
      { label: "airSlate products", url: "https://www.airslate.com/products" },
    ],
    relatedLinks: [{ label: "Sign PDF", url: "/tool/sign-pdf" }, { label: "Form Creator", url: "/tool/form-creator" }, { label: "Fill Form", url: "/tool/fill-form" }, { label: "E-Sign PDF", url: "/tool/esign-pdf" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "pdfescape", name: "PDFescape",
    title: "PrivaTools vs PDFescape: online form editing and limits",
    description: "PDFescape's free online editor takes 10 MB, 100-page PDFs and stores them on US servers; PrivaTools is free and open source. Limits and storage compared.",
    summary: "PDFescape is a long-running online PDF editor and form filler with a free tier, paid Premium and Ultimate plans, and PDFescape Desktop for Windows. It suits annotating, filling and building simple forms, and keeps your files in an online list for days or weeks. PrivaTools has no paid tier and keeps no documents between visits; it runs each tool in the browser or on a temporary server, and adds conversions, OCR and media tools.",
    category: "Signing & forms",
    highlights: ["10 MB and 100 pages free, 40 MB paid; PrivaTools takes about 250 MB per file on most pages.", "Files kept in an online account, against temporary processing and local downloads.", "Existing-text editing in PDFescape Desktop on paid plans; PrivaTools only adds content."],
    overview: [
      "PDFescape, from Avanquest Software, offers PDFescape Online, an editor and form filler that runs in the web browser, and PDFescape Desktop for Windows. The free online tier needs no registration and lets you annotate, fill in forms and add new form fields. Premium and Ultimate subscriptions raise the limits, remove ads and include PDFescape Desktop features, such as editing existing text and images; Ultimate adds advanced forms, digital signing and redaction.",
      "Documents opened in PDFescape Online are uploaded and saved on its web servers, which it says are in a United States data centre. Free users keep up to 10 stored files for 7 days, Premium users 100 files for 30 days, and Ultimate users 100 files with no expiry. Its signup page says all plans come with a 15-day money-back guarantee.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no plans to upgrade to.", competitor: "Free online tier with ads; Premium $2.99 a month billed yearly or $5.99 billed monthly; Ultimate $5.99 a month billed yearly or $8.99 billed monthly.", sourceUrl: "https://www.pdfescape.com/signup/" },
      { label: "File limits", privatools: "Up to 500 MB per upload request, which is about 250 MB for one file on most pages.", competitor: "Free uploads up to 10 MB and 100 pages; Premium and Ultimate up to 40 MB and 1,000 pages.", sourceUrl: "https://support.pdfescape.com/hc/en-us/articles/360028432531" },
      { label: "Stored files", privatools: "No saved documents on the website; each result downloads to your device.", competitor: "Free: 10 files kept 7 days; Premium: 100 files for 30 days; Ultimate: 100 files with no expiry.", sourceUrl: "https://www.pdfescape.com/what/premium/" },
      { label: "Where files are processed", privatools: "In your browser or on PrivaTools' server, depending on the tool, with no saved workspace.", competitor: "Online documents are saved on its web servers in a United States data centre.", sourceUrl: "https://www.pdfescape.com/signup/" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "No registration is required for the free online editor.", sourceUrl: "https://www.pdfescape.com/what/features/" },
      { label: "Platforms", privatools: "Any modern browser, including on macOS and Linux.", competitor: "Online in Chrome, Firefox, Edge, Safari and other browsers; Desktop runs on Windows.", sourceUrl: "https://www.pdfescape.com/" },
      { label: "Editing existing text", privatools: "Not available: Edit PDF adds text, drawings, images and whiteout on top.", competitor: "Its feature list puts editing existing text and images among the Premium Desktop features.", sourceUrl: "https://www.pdfescape.com/what/features/" },
    ],
    sections: [
      { heading: "Forms, annotations and signatures", body: [
        "PDFescape's free online tier covers everyday form jobs: filling existing forms, adding new form fields, commenting, marking up and adding text. Ultimate adds advanced forms, digital signing and sealing, and redaction, and its support pages say OCR is not available. Its help centre also says PDFescape Online can modify only text added with PDFescape and points to PDFescape Desktop for other text.",
        "PrivaTools covers the same ground with separate free tools. Fill Form enters values into existing fields; Form Creator adds text, checkbox, radio, dropdown, list and signature fields; Annotate PDF adds highlights, underlines and sticky notes; Redact PDF removes the content under each box; and OCR PDF makes scans searchable. Its signatures are images placed on the page, not certificate-based signatures.",
      ] },
      { heading: "What happens to your documents", body: [
        "PDFescape is built around an online workspace: files you open are saved to a recent-files list on its servers so that you can come back to them, for seven days on the free tier. That suits a form you finish over several sessions, and paid plans keep more files for longer.",
        "PrivaTools keeps no workspace. Server tools remove the job's files after the response, and a background sweep clears anything older than ten minutes, so a half-finished task has to be saved as a download.",
      ] },
    ],
    chooseCompetitor: ["You fill in or build a simple form online and want to come back to it from a file list.", "You want existing text and images edited in a Windows app and can pay for Premium or Ultimate.", "You want forms, digital signing and redaction inside one editor rather than separate tools."],
    choosePrivaTools: ["Your PDFs are larger than 10 MB or longer than 100 pages and you do not want a subscription.", "You need OCR, conversions to and from Office formats, or tools for images and media.", "You prefer not to keep documents in an online account between sessions."],
    tradeoffs: ["PrivaTools' editor and form tools are separate steps, and its signatures are visible images; if you need certificate-based signing, choose a product that issues one.", "Big uploads to PrivaTools can still fail on a slow connection, because some of its pages stop waiting after 60 seconds.", "We did not benchmark either editor's output."],
    sources: [
      { label: "PDFescape plans and pricing", url: "https://www.pdfescape.com/signup/" },
      { label: "PDFescape feature list", url: "https://www.pdfescape.com/what/features/" },
      { label: "PDFescape Premium comparison", url: "https://www.pdfescape.com/what/premium/" },
      { label: "PDFescape Desktop", url: "https://www.pdfescape.com/what/desktop/" },
      { label: "PDFescape home page", url: "https://www.pdfescape.com/" },
      { label: "PDFescape file size and page limits", url: "https://support.pdfescape.com/hc/en-us/articles/360028432531" },
      { label: "PDFescape: editing existing text", url: "https://support.pdfescape.com/hc/en-us/articles/360026444112" },
      { label: "PDFescape: OCR availability", url: "https://support.pdfescape.com/hc/en-us/articles/13941069845652" },
    ],
    relatedLinks: [{ label: "Fill Form", url: "/tool/fill-form" }, { label: "Form Creator", url: "/tool/form-creator" }, { label: "Annotate PDF", url: "/tool/annotate-pdf" }, { label: "Redact PDF", url: "/tool/redact-pdf" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "nitro-pdf", name: "Nitro PDF",
    title: "PrivaTools vs Nitro PDF: desktop editing, trial and plans",
    description: "Nitro PDF is a paid desktop editor for Windows and Mac with a 14-day trial and free online converters; PrivaTools is free in the browser. Editing compared.",
    summary: "Nitro sells PDF editing as annual subscriptions for Windows, macOS and iOS, a three-year Windows licence and separate Nitro Sign plans, after a 14-day trial with no card, and it offers free online converters that need no registration. It edits existing text with paragraph reflow, runs OCR and converts to Office formats. PrivaTools is free, needs no account and works in any browser, but it adds content rather than editing existing text, and it has no desktop app or signature-request service.",
    category: "Desktop & teams",
    highlights: ["Existing-text editing with reflow, which PrivaTools does not offer.", "A 14-day trial, then a subscription or a three-year Classic licence; its converters are free.", "Signature requests through Nitro Sign, against image signatures you place yourself."],
    overview: [
      "Nitro offers PDF software for Windows, macOS and iOS, the cloud-based Nitro Workspace, and Nitro Sign for electronic signatures. Its pricing page lists Nitro PDF Standard and Plus subscriptions, a Nitro PDF Classic licence that is a one-time payment for three years of use on the Windows desktop, and Nitro Sign plans; its trial page calls the desktop product Nitro PDF Pro. Subscriptions bought online are billed annually.",
      "The 14-day trial covers the PDF apps, Nitro Sign and Nitro Workspace without a credit card; when it ends, the web-based conversion tools remain available and other features lock. Its free online converters, such as PDF to Word, need no registration or email, while the desktop product needs an active subscription or licence. Nitro's compliance page lists ISO 27001 and SOC 2 among its certifications.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no trial period or licence.", competitor: "Standard and Plus subscriptions billed annually; Classic is a three-year, per-licence Windows desktop licence.", sourceUrl: "https://www.gonitro.com/pricing" },
      { label: "Trial", privatools: "Every tool is free without an account.", competitor: "14 days without a credit card; afterwards the web conversion tools stay available.", sourceUrl: "https://www.gonitro.com/free-trial" },
      { label: "File limits", privatools: "A 500 MB request cap, so about 250 MB for one file on most pages.", competitor: "Its web-based conversion tools take files up to 100 MB and 500 pages; Table Data Extract takes 25 MB.", sourceUrl: "https://www.gonitro.com/user-guide/workspace/web-based-tools" },
      { label: "Where files are processed", privatools: "In the browser tab for local tools, or on PrivaTools' server for conversions, with nothing to install.", competitor: "Downloadable software on your own computers, plus cloud services reached over the internet.", sourceUrl: "https://www.gonitro.com/legal/pdf-sign/terms-of-service" },
      { label: "Account", privatools: "Not needed; an optional account only issues API keys.", competitor: "Its free online converters need no registration or email.", sourceUrl: "https://www.gonitro.com/pdf-to-word" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "Proprietary: Nitro remains the sole owner of its software and IP.", sourceUrl: "https://www.gonitro.com/legal/pdf-sign/terms-of-service" },
      { label: "Platforms", privatools: "Any modern browser; installable as a web app.", competitor: "Windows 10 or 11 (64-bit), macOS 10.14 or later, and iOS.", sourceUrl: "https://www.gonitro.com/documentation/technical-requirements" },
      { label: "Editing existing text", privatools: "Edit PDF adds text, drawings, images and whiteout over the page.", competitor: "Edits text within a paragraph and reflows it inside the text box as you type.", sourceUrl: "https://www.gonitro.com/user-guide/pro/article/add-or-edit-text-in-a-pdf" },
    ],
    sections: [
      { heading: "Editing depth", body: [
        "Nitro is a full desktop editor. Its Windows guide describes editing existing paragraphs with text reflow, and its plans include OCR that turns scans into editable, searchable PDFs, conversion to Word, Excel and PowerPoint, and batch processing for conversion, printing and OCR. Its AI Document Assistant runs on Azure OpenAI, and Nitro says documents are deleted once the task is complete.",
        "PrivaTools approaches the same jobs as separate tools. Edit PDF draws new content over the page rather than changing existing text; OCR PDF's server engine adds a searchable text layer, while its browser engine returns plain text for up to 50 pages; PDF to Word extracts text line by line into an editable draft without rebuilding paragraphs or tables. For a document you revise every day, a desktop editor such as Nitro does more.",
      ] },
      { heading: "Signatures and teams", body: [
        "Nitro Sign is sold as its own plans, and the Mac app can send documents for signature with Nitro Sign or DocuSign. Single sign-on for the PDF apps is listed on the Plus plan. PrivaTools has no signature-request workflow: Sign PDF and E-Sign PDF place a visible signature image that you add yourself, and nothing in the file records who signed or whether it changed afterwards.",
      ] },
    ],
    chooseCompetitor: ["You edit existing text, images and forms in PDFs every day and want a desktop app.", "You need scans made searchable and editable, with batch OCR or conversion.", "Your team sends documents for signature and tracks them, or needs single sign-on."],
    choosePrivaTools: ["You need OCR, redaction or page editing without installing software or starting a trial.", "You want image, audio, video and developer tools alongside PDFs.", "You want open code, or to host the service yourself."],
    tradeoffs: ["Placing a signature image and running a signature-request service are different jobs; compare them separately.", "A large file on a slow connection can outlast the 60-second wait on PrivaTools' OCR and PDF to Word pages.", "We did not benchmark editing accuracy, OCR quality or speed."],
    sources: [
      { label: "Nitro pricing and plans", url: "https://www.gonitro.com/pricing" },
      { label: "Nitro free trial", url: "https://www.gonitro.com/free-trial" },
      { label: "Nitro free PDF to Word converter", url: "https://www.gonitro.com/pdf-to-word" },
      { label: "Nitro technical requirements", url: "https://www.gonitro.com/documentation/technical-requirements" },
      { label: "Nitro product downloads", url: "https://www.gonitro.com/documentation/product-downloads" },
      { label: "Nitro guide: add or edit text", url: "https://www.gonitro.com/user-guide/pro/article/add-or-edit-text-in-a-pdf" },
      { label: "Nitro guide: batch processing", url: "https://www.gonitro.com/user-guide/pro/article/batch-processing" },
      { label: "Nitro web-based tools", url: "https://www.gonitro.com/user-guide/workspace/web-based-tools" },
      { label: "Nitro terms of service", url: "https://www.gonitro.com/legal/pdf-sign/terms-of-service" },
      { label: "Nitro PDF Pro for Mac guide", url: "https://www.gonitro.com/user-guide/mac/article/introduction" },
      { label: "Nitro AI security", url: "https://www.gonitro.com/security-compliance/artificial-intelligence" },
      { label: "Nitro compliance", url: "https://www.gonitro.com/security-compliance/compliance" },
    ],
    relatedLinks: [{ label: "Edit PDF", url: "/tool/edit-pdf" }, { label: "OCR PDF", url: "/tool/ocr-pdf" }, { label: "PDF to Word", url: "/tool/pdf-to-word" }, { label: "E-Sign PDF", url: "/tool/esign-pdf" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "tinywow", name: "TinyWow",
    title: "PrivaTools vs TinyWow: free tools, plans and file handling",
    description: "TinyWow offers free PDF, image, video and AI writing tools, with paid plans that list no ads; PrivaTools has no ads and is open source. Plans and data compared.",
    summary: "TinyWow is a broad free toolbox, now part of Jenni AI, covering PDF, image, video, file conversion and AI writing tasks without registration. Its pricing page also sells optional plans whose features include no ads, faster processing and no captcha. PrivaTools covers PDFs, images, audio, video and developer data with no paid tier, no advertising and open code, but it has no AI writing tools or video downloader.",
    category: "Mixed file tools",
    highlights: ["An AI Humanizer and a TikTok video downloader, which PrivaTools does not offer.", "Paid plans that list no ads or captchas, against no ads and no paid tier.", "Uploads deleted within an hour on US servers, against cleanup after each response."],
    overview: [
      "TinyWow offers online tools for PDFs, images, video, file conversion and AI writing, and its terms say the site does not currently require registration or fees. Its about page says it joined forces with Jenni.ai in 2025, and its footer describes it as a Jenni AI company. Processing happens on its servers, which its privacy policy says are hosted in the United States.",
      "Its pricing page says the tools are free to use without registration and lists optional paid plans, shown to us in Indian rupees, whose features include no ads, faster processing and no captcha. Its privacy policy says uploaded files are deleted an hour after processing and that analytics and third-party tracking are used to personalise the ads it serves, and it summarises ways to opt out of that tracking, such as blocking cookies in your browser.",
    ],
    features: [
      { label: "Price", privatools: "Free, with no paid tier.", competitor: "Free without registration; optional monthly or yearly plans list no ads, faster processing and no captcha.", sourceUrl: "https://tinywow.com/support-tinywow" },
      { label: "Account", privatools: "Not needed for any tool.", competitor: "No registration or fees currently required; subscriptions are managed in an account.", sourceUrl: "https://tinywow.com/tos" },
      { label: "Where files are processed", privatools: "Most developer and text tools run in your browser; file conversions run on PrivaTools' server in temporary storage.", competitor: "On its servers, hosted in the United States.", sourceUrl: "https://tinywow.com/privacy" },
      { label: "Retention", privatools: "Deleted by response cleanup, with a background sweep for anything older than ten minutes.", competitor: "The privacy policy says uploaded files are deleted one hour after processing.", sourceUrl: "https://tinywow.com/privacy" },
      { label: "Ads and tracking", privatools: "No ad networks; Google Analytics is on by default with an off switch on the Privacy page.", competitor: "Analytics and third-party tracking personalise its ads; the policy lists ways to opt out.", sourceUrl: "https://tinywow.com/privacy" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "The terms say the underlying software is the property of TinyWow and its partners.", sourceUrl: "https://tinywow.com/tos" },
      { label: "Tool range", privatools: "PDF, image, audio, video, archive and developer tools, with on-device and own-key AI options.", competitor: "Tools for PDFs, images, video, AI writing and file conversion.", sourceUrl: "https://tinywow.com/tools" },
    ],
    sections: [
      { heading: "Two different kinds of breadth", body: [
        "Both toolboxes are broad, in different directions. TinyWow's catalogue lists an AI Humanizer among its writing tools, alongside a PDF translator, e-signing, audio to text, background removal, a TikTok video downloader and a photo clean-up tool that uses AI to remove unwanted objects from images. PrivaTools has no AI writing tools or video downloaders, though it does generate placeholder text, passwords, UUIDs and .gitignore files. Its Remove Image Watermark rebuilds a small area you select from the surrounding pixels, without AI, so it suits logos and marks rather than whole objects.",
        "PrivaTools' breadth is in file operations such as PDF editing and conversion, OCR, audio and video conversion, archives and developer formats. Most of its developer and text tools run in the browser, while most of its PDF, media and archive tools upload to its server.",
      ] },
      { heading: "How files are handled", body: [
        "TinyWow processes uploads on servers in the United States. Its privacy policy, last revised in March 2023, says files are deleted one hour after processing; its tool pages say one hour after upload, and its terms say 15 minutes after processing. The privacy policy also says TinyWow does not sell information about its users or their files.",
        "PrivaTools labels each tool before it runs: browser tools keep the input on the device, and server tools write it to temporary per-request storage that is cleaned after the response. It uses Google Analytics by default to record page visits and where they come from, including campaign tags; Google's automatic scroll, outbound-click and video events; and each tool run with its outcome and, for failures, a fixed category. Analytics never receives file names or contents, and you can switch it off on the Privacy page.",
      ] },
    ],
    chooseCompetitor: ["You want AI writing or humanizing tools next to your file tools.", "You need its video downloader or its AI tool for removing objects from photos.", "You are happy with a free tier supported by ads, or want its paid plan for faster processing."],
    choosePrivaTools: ["You want tools without ads, captchas or a paid plan.", "You want some tasks to stay in your browser, with a clear label on every tool that does not.", "You want to read the code or run the service on your own server."],
    tradeoffs: ["PrivaTools' free server tools are rate-limited, with heavy jobs capped at about five runs a minute from one visitor.", "We did not benchmark output quality for either toolbox."],
    sources: [
      { label: "TinyWow pricing and plans", url: "https://tinywow.com/support-tinywow" },
      { label: "TinyWow terms of service", url: "https://tinywow.com/tos" },
      { label: "TinyWow privacy policy", url: "https://tinywow.com/privacy" },
      { label: "TinyWow tool catalogue", url: "https://tinywow.com/tools" },
      { label: "TinyWow compress PDF and file deletion", url: "https://tinywow.com/pdf/compress" },
      { label: "TinyWow about page", url: "https://tinywow.com/about" },
      { label: "TinyWow home page", url: "https://tinywow.com/" },
    ],
    relatedLinks: [{ label: "Compress PDF", url: "/tool/compress-pdf" }, { label: "Background Remover", url: "/tools/remove-background" }, { label: "Evaluate privacy claims in online PDF tools", url: "/blog/online-pdf-tools-tracking-you" }, { label: "Five questions to ask a privacy policy", url: "/blog/reading-privacy-policies" }],
    reviewedAt: "2026-09-24",
  },
  {
    slug: "ihatepdf", name: "ihatepdf.cv",
    title: "PrivaTools vs ihatepdf.cv: browser-only PDF tools compared",
    description: "ihatepdf.cv runs most PDF tools in the browser but sends text to AI services for chat and summaries; PrivaTools mixes browser and server tools.",
    summary: "Both sites let you work without an account. ihatepdf.cv says its PDF tools run in the browser with WebAssembly, is free without ads and is funded by donations; its terms say the code is not open source. PrivaTools runs some tools in the browser and others on its server, covers images, media and developer tasks too, and publishes its own code under the MIT licence.",
    category: "Local & self-hosted",
    highlights: ["Browser-first PDF tools, against a mix of browser and disclosed server tools.", "Proprietary code; PrivaTools' own code is MIT-licensed and self-hostable.", "PDF chat through Google Gemini, against a choice of AI providers."],
    overview: [
      "ihatepdf.cv is a free collection of PDF and document tools that, by its own description, run in the web browser: its merge page says processing uses WebAssembly and files do not leave the device. Its about page names three tools that involve another party by design, Chat with PDF, P2P Share and a collaborative whiteboard, and its Summarize PDF page says the extracted text is sent to an AI service.",
      "The site says it has no ads, no paid tier and no account, and is kept running by voluntary donations. It uses Microsoft Clarity to understand how pages are used, with the tool workspace masked in those recordings so the text of your documents is not captured, and its terms state that the software is not open source and that no licence to reuse it is granted.",
    ],
    features: [
      { label: "Price", privatools: "Free to use, with no paid tier and no advertising.", competitor: "Free, with no ads or paid tier; funded by voluntary donations.", sourceUrl: "https://www.ihatepdf.cv/about" },
      { label: "File limits", privatools: "500 MB per server request, about 250 MB per file on most pages; browser tools depend on your device.", competitor: "No server limit for merging; typically up to 150 MB across all files on a desktop, set by device memory.", sourceUrl: "https://www.ihatepdf.cv/merge-pdf" },
      { label: "Where files are processed", privatools: "Each tool states whether it runs in your browser or uploads for temporary server processing.", competitor: "Most tools run in the browser with WebAssembly; its about page names three tools that involve another party.", sourceUrl: "https://www.ihatepdf.cv/about" },
      { label: "AI chat", privatools: "Extracted text goes from your browser to the provider you choose, such as Anthropic, OpenAI or Gemini, or a local server.", competitor: "Chat with PDF extracts text locally and sends that text to Google's Gemini API, using a key you supply.", sourceUrl: "https://www.ihatepdf.cv/chat-with-pdf" },
      { label: "Account", privatools: "Not needed; an optional account issues API keys.", competitor: "No account or email required.", sourceUrl: "https://www.ihatepdf.cv/merge-pdf" },
      { label: "Source code", privatools: "PrivaTools' own code is MIT-licensed and self-hostable.", competitor: "Its terms say it is not open source and grant no licence to reuse it.", sourceUrl: "https://www.ihatepdf.cv/terms" },
      { label: "Platforms", privatools: "Browser app, installable as a PWA; previously opened browser tools can work offline.", competitor: "Its homepage says the site works offline after the first page load.", sourceUrl: "https://www.ihatepdf.cv/" },
      { label: "Analytics", privatools: "Google Analytics on by default: visits, referrers, campaign tags, tool outcomes and Google's scroll, outbound-click and video events, never file names or contents.", competitor: "Microsoft Clarity records how pages are used, with the tool workspace masked.", sourceUrl: "https://www.ihatepdf.cv/about" },
    ],
    sections: [
      { heading: "What local processing covers", body: [
        "ihatepdf.cv's merge page says files never leave the device because processing runs in WebAssembly, and it ties capacity to memory: typically 20 to 50 files, or about 150 MB in total, on a desktop browser. Its homepage describes Summarize PDF as on-device AI, while the tool's own page says the extracted text is sent to an AI service; check the page for the exact tool before sending anything sensitive.",
        "PrivaTools labels every tool. Most developer and text utilities and several AI tools run in the browser; PDF conversions, the default OCR engine and media work run on the server, where inputs sit in temporary per-request storage and are cleaned after the response.",
      ] },
      { heading: "Asking questions about a PDF", body: [
        "Both products extract the PDF's text in the browser before a chat. ihatepdf.cv then sends that text to Google Gemini with a key you supply, and keeps the key in your browser only if you choose to save it. PrivaTools' Chat with PDF sends the text, your question and recent messages straight from the browser to the provider you select, without routing them through PrivaTools. Either way, the provider's own terms and charges apply.",
      ] },
    ],
    chooseCompetitor: ["You want PDF tools that its pages describe as running entirely in the browser.", "You already use a Gemini API key and want to chat with a PDF using it.", "You need its India-specific document tools, such as its GST invoice and POS billing tools."],
    choosePrivaTools: ["You want to read, audit or self-host the code that processes your files.", "Your tasks go beyond PDFs to images, audio, video, archives and developer data.", "You want a choice of AI providers, or a server or browser engine for OCR."],
    tradeoffs: ["A file that stays in the browser can still have its text sent elsewhere: on both sites, chat features send extracted text to an AI provider.", "Browser processing is bound by device memory; ihatepdf.cv's own merge figures vary by device, while PrivaTools' server tools have fixed request limits instead.", "Neither product's output quality or speed was benchmarked for this page."],
    sources: [
      { label: "ihatepdf.cv about page", url: "https://www.ihatepdf.cv/about" },
      { label: "ihatepdf.cv merge PDF", url: "https://www.ihatepdf.cv/merge-pdf" },
      { label: "ihatepdf.cv chat with PDF", url: "https://www.ihatepdf.cv/chat-with-pdf" },
      { label: "ihatepdf.cv summarize PDF", url: "https://www.ihatepdf.cv/summarize-pdf" },
      { label: "ihatepdf.cv terms", url: "https://www.ihatepdf.cv/terms" },
      { label: "ihatepdf.cv home page", url: "https://www.ihatepdf.cv/" },
      { label: "ihatepdf.cv tool list", url: "https://www.ihatepdf.cv/llms.txt" },
    ],
    relatedLinks: [{ label: "Merge PDF", url: "/tool/merge-pdf" }, { label: "Chat with PDF", url: "/tool/chat-with-pdf" }, { label: "PrivaTools and ihatepdf: what local means", url: "/blog/privatools-vs-ihatepdf" }, { label: "What browser-local processing means", url: "/blog/how-local-first-works" }],
    reviewedAt: "2026-09-24",
  },
];
