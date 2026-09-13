const escapeHtml = (text: string) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function inline(text: string): string {
    const protectedCode: string[] = [];
    const escaped = escapeHtml(text).replace(/`([^`]+)`/g, (_match, code) => `\uE100${protectedCode.push(`<code>${code}</code>`) - 1}\uE100`);
    return escaped.replace(/\[([^\]]+)\]\(([^\s)]+)\)/g, (_match, label, href: string) => /^(https?:\/\/|mailto:|#)/i.test(href) ? `<a href="${href}" rel="noreferrer noopener">${label}</a>` : label)
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/\*([^*]+)\*/g, "<em>$1</em>")
        .replace(/\uE100(\d+)\uE100/g, (_match, index) => protectedCode[Number(index)] ?? "");
}

export function simpleMarkdownToHtml(markdown: string): string {
    const blocks: string[] = [], paragraph: string[] = [], list: string[] = [], code: string[] = [];
    let listType = "", fenced = false;
    const flushParagraph = () => { if (paragraph.length) { blocks.push(`<p>${inline(paragraph.join("\n"))}</p>`); paragraph.length = 0; } };
    const flushList = () => { if (list.length) { blocks.push(`<${listType}>\n${list.map(item => `<li>${inline(item)}</li>`).join("\n")}\n</${listType}>`); list.length = 0; } };
    for (const line of markdown.replace(/\r\n?/g, "\n").split("\n")) {
        if (/^\s*```/.test(line)) { flushParagraph(); flushList(); if (fenced) { blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`); code.length = 0; } fenced = !fenced; continue; }
        if (fenced) { code.push(line); continue; }
        if (!line.trim()) { flushParagraph(); flushList(); continue; }
        const heading = line.match(/^(#{1,6})\s+(.+)$/), item = line.match(/^\s*(?:([-+*])|\d+[.)])\s+(.+)$/);
        if (heading) { flushParagraph(); flushList(); blocks.push(`<h${heading[1].length}>${inline(heading[2])}</h${heading[1].length}>`); }
        else if (item) { flushParagraph(); const next = item[1] ? "ul" : "ol"; if (listType !== next) flushList(); listType = next; list.push(item[2]); }
        else if (/^>\s?/.test(line)) { flushParagraph(); flushList(); blocks.push(`<blockquote>${inline(line.replace(/^>\s?/, ""))}</blockquote>`); }
        else if (/^\s*(?:---+|\*\*\*+)\s*$/.test(line)) { flushParagraph(); flushList(); blocks.push("<hr>"); }
        else { flushList(); paragraph.push(line); }
    }
    flushParagraph(); flushList();
    if (fenced) blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
    return blocks.join("\n\n");
}
