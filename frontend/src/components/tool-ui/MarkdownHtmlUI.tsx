import { simpleMarkdownToHtml } from "./markdown-render";
import { useCallback, useEffect, useRef, useState } from "react";
import { Download, Upload, Bold, Italic, List, Code, Link, Heading2 } from "lucide-react";
import { downloadBlob } from "@/lib/api";
import { useToolDefaults } from "@/hooks/useToolDefaults";
import { useExperience } from "@/lib/experience";
import { consumeFileHandoffs } from "@/lib/file-handoff";
import { LabWorkspace, LabPair, LabOutput, ToolCopyButton } from "./SpecialistTools";

type View = "split" | "html" | "preview";

const SAMPLE = "# Hello, notebook.\n\nA little **Markdown**, a little possibility.\n\n## On the list\n\n- Write something useful\n- See it take shape\n- Take the HTML with you\n\n[Visit example](https://example.com)";
const DEFAULTS: { view: View } = { view: "split" };

export function MarkdownHtmlUI() {
    const [config, , { setField }] = useToolDefaults("markdown-html", DEFAULTS);
    const setView = useCallback((view: View) => setField("view", view), [setField]);
    const [input, setInput] = useState(SAMPLE);
    const [filename, setFilename] = useState("document.md");
    const [fileError, setFileError] = useState<string | null>(null);
    const [reading, setReading] = useState(false);
    const editor = useRef<HTMLTextAreaElement>(null), fileInput = useRef<HTMLInputElement>(null), readingId = useRef(0);
    const loadFile = useCallback(async (file: File) => {
        const current = ++readingId.current;
        setFileError(null);
        if (!/\.(md|markdown|txt)$/i.test(file.name)) { setFileError("Choose a .md, .markdown or plain .txt file."); return; }
        if (file.size > 2 * 1024 * 1024) { setFileError("This editor supports Markdown files up to 2 MB. Choose a smaller document."); return; }
        setReading(true);
        try { const content = await file.text(); if (current === readingId.current) { setInput(content.replace(/^\uFEFF/, "")); setFilename(file.name.replace(/\.(md|markdown|txt)$/i, ".md")); setView("split"); } }
        catch { if (current === readingId.current) setFileError("Couldn't read this file. Your current draft is still here."); }
        finally { if (current === readingId.current) setReading(false); }
    }, [setView]);
    const invalidatePending = useCallback(() => { readingId.current++; }, []);
    useEffect(() => { let cancelled = false; void consumeFileHandoffs("markdown-html").then(files => { if (!cancelled && files[0]) void loadFile(files[0]); }); return () => { cancelled = true; invalidatePending(); }; }, [loadFile, invalidatePending]);
    function format(before: string, after = "", example = "text") {
        const node = editor.current; if (!node) return;
        const start = node.selectionStart, end = node.selectionEnd, text = input.slice(start, end) || example;
        setInput(input.slice(0, start) + before + text + after + input.slice(end));
        requestAnimationFrame(() => { node.focus(); node.setSelectionRange(start + before.length, start + before.length + text.length); });
    }
    const words = input.trim() ? input.trim().split(/\s+/).length : 0;
    const headings = input.replace(/```[^\n]*\n[\s\S]*?(?:```|$)/g, "").split("\n").filter(line => /^#{1,6}\s+/.test(line)).length;
    const stem = filename.replace(/\.md$/i, "");
    const { resolved, experience } = useExperience();
    const html = simpleMarkdownToHtml(input);
    const dark = resolved === "dark", play = experience === "play";
    const ink = dark ? "#f3f4f7" : play ? "#472732" : "#23394f";
    const bg = dark ? "#232323" : play ? "#fff5f5" : "#f8fbff";
    const accent = dark ? play ? "#ff9677" : "#91b5ff" : play ? "#a32749" : "#285cc7";
    const preview = `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><style>body{font:15px/1.85 system-ui,sans-serif;color:${ink};background:${bg};padding:24px;margin:0;overflow-wrap:anywhere}h1,h2,h3{line-height:1.25;letter-spacing:-.035em}h1{font-size:30px}h2{font-size:23px}pre{white-space:pre-wrap}code{font:13px/1.8 ui-monospace,monospace}a{color:${accent}}blockquote{border-left:2px solid ${accent};margin:20px 0;padding-left:18px}li{margin:7px 0}</style></head><body>${html}</body></html>`;
    return <LabWorkspace kind="markdown" note="Write here, preview here. Your text stays in this browser; the preview cannot load remote content or run scripts.">
        <div className="pt-markdown-document"><div><strong>{filename}</strong><span>{reading ? "Reading your file…" : `${words.toLocaleString()} words · ${headings} headings`}</span></div><input ref={fileInput} type="file" accept=".md,.markdown,.txt,text/markdown,text/plain" className="sr-only" tabIndex={-1} aria-label="Open Markdown file" onChange={e => { if (e.target.files?.[0]) void loadFile(e.target.files[0]); e.target.value = ""; }}/><div className="pt-lab-controls"><button className="pt-lab-button" disabled={reading} onClick={() => fileInput.current?.click()}><Upload size={15}/>Open .md</button><button className="pt-lab-button" onClick={() => downloadBlob(new Blob([input], {type:"text/markdown;charset=utf-8"}), filename)}><Download size={15}/>Save Markdown</button></div></div>
        {fileError && <p role="alert" className="pt-lab-issue is-error">{fileError}</p>}
        <div className="pt-lab-toolbar"><div className="pt-lab-tabs" role="group" aria-label="Markdown workspace view">{([['split','Write & preview'],['html','HTML output'],['preview','Preview only']] as const).map(([view,label]) => <button type="button" key={view} aria-pressed={config.view === view} onClick={() => setView(view)}>{label}</button>)}</div><div className="pt-lab-controls"><ToolCopyButton value={html} label="Copy HTML"/><button type="button" className="pt-lab-button is-primary" disabled={!html} onClick={() => downloadBlob(new Blob([`<!doctype html><html><head><meta charset="utf-8"><title>Document</title></head><body>${html}</body></html>`], {type:"text/html"}), `${stem}.html`)}><Download size={15}/>Download .html</button></div></div>
        <div className={`pt-lab-reading is-${config.view}`}><LabPair input={<><div className="pt-lab-toolbar"><h2>Your Markdown</h2></div><div role="group" aria-label="Markdown formatting" className="pt-markdown-format">{([{label:"Heading",icon:Heading2,before:"## ",after:"",example:"Heading"},{label:"Bold",icon:Bold,before:"**",after:"**",example:"bold text"},{label:"Italic",icon:Italic,before:"*",after:"*",example:"emphasis"},{label:"List",icon:List,before:"- ",after:"",example:"List item"},{label:"Code",icon:Code,before:"`",after:"`",example:"code"},{label:"Link",icon:Link,before:"[",after:"](https://example.com)",example:"link text"}]).map(item => <button key={item.label} type="button" aria-label={`Insert ${item.label.toLowerCase()}`} title={item.label} onClick={() => format(item.before,item.after,item.example)}><item.icon size={16}/><span>{item.label}</span></button>)}</div><label className="pt-lab-field"><span className="sr-only">Markdown source</span><textarea ref={editor} aria-label="Markdown source" value={input} onChange={e => setInput(e.target.value)} spellCheck={false} className="pt-lab-textarea"/><small className="pt-lab-caption">{input.length.toLocaleString()} characters · edit to update the result</small></label></>} output={<><div className="pt-lab-toolbar"><h2>{config.view === "html" ? "Your HTML" : "How it reads"}</h2></div><div hidden={config.view !== "html"}><LabOutput value={html} label="HTML output"/></div><iframe title="Markdown preview" sandbox="" referrerPolicy="no-referrer" srcDoc={preview} hidden={config.view === "html"}/></>}/></div>
        <p className="pt-lab-caption">Supports headings, paragraphs, lists, quotes, fenced code and basic inline formatting. Raw HTML is shown as text. Complex Markdown extensions may need a dedicated parser.</p>
    </LabWorkspace>;
}
