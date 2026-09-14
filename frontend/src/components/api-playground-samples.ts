export type PlaygroundOperation = "merge" | "compress" | "pdf-to-text";

// ASCII-only content keeps the PDF cross-reference offsets equal to byte offsets.
// These public, deterministic samples contain no uploaded or account data.
export function samplePdf(page: 1 | 2): string {
    const content = `BT /F1 22 Tf 72 740 Td (PrivaTools API sample ${page}) Tj 0 -38 Td /F1 12 Tf (A small document for your first API request.) Tj ET\n`;
    const objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        `<< /Length ${content.length} >>\nstream\n${content}endstream`,
    ];
    let pdf = "%PDF-1.4\n";
    const offsets = [0];
    objects.forEach((object, index) => {
        offsets.push(pdf.length);
        pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
    });
    const xref = pdf.length;
    pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
    pdf += offsets.slice(1).map(offset => `${String(offset).padStart(10, "0")} 00000 n \n`).join("");
    return `${pdf}trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
}

export const playgroundOperations = {
    merge: { label: "Merge two PDFs", units: 1, output: "merged.pdf", files: 2, field: "files", description: "Combine two one-page samples into a two-page PDF." },
    compress: { label: "Compress a PDF", units: 1, output: "compressed.pdf", files: 1, field: "files", description: "Try recommended compression. This tiny text sample may already be as small as it can get." },
    "pdf-to-text": { label: "Extract PDF text", units: 5, output: "extracted-text.json", files: 1, field: "file", description: "Read the sample’s text and receive a JSON response." },
} as const;

export function playgroundForm(operation: PlaygroundOperation): FormData {
    const form = new FormData();
    const config = playgroundOperations[operation];
    for (let page = 1; page <= config.files; page++) {
        form.append(config.field, new Blob([samplePdf(page as 1 | 2)], { type: "application/pdf" }), `sample-${page}.pdf`);
    }
    if (operation === "compress") form.append("level", "recommended");
    return form;
}

export function playgroundCurl(operation: PlaygroundOperation, endpoint: string): string {
    const config = playgroundOperations[operation];
    const quote = (text: string) => `'${text.replace(/'/g, "'\\''")}'`;
    const lines = [
        `curl --fail-with-body --max-time 120 ${quote(endpoint)}`,
        '  -H "X-API-Key: $PRIVATOOLS_API_KEY"',
        ...Array.from({ length: config.files }, (_, index) => `  -F '${config.field}=@sample-${index + 1}.pdf;type=application/pdf'`),
        ...(operation === "compress" ? ["  --form-string 'level=recommended'"] : []),
        `  --output ${config.output}`,
    ];
    return `# Download the sample files below. Set your key in the environment.\n# A timed-out processing request may still finish and use allowance.\n${lines.join(" \\\n")}`;
}
