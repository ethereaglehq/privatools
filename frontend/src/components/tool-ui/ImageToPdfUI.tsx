/**
 * ImageToPdfUI — batch images → single PDF, with page-size choice.
 * Arrange real image previews on a working sheet before binding the PDF.
 */
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Download, X, Image as ImageIcon, ChevronUp, ChevronDown, Sparkles } from "lucide-react";
import { friendlyError } from "@/lib/utils";
import { processFilesAndDownload, formatFileSize, buildOutputFilename } from "@/lib/api";
import { loadSampleJpg } from "@/lib/sample-files";
import { emitToolSuccess } from "@/hooks/useFirstSuccess";
import { consumeFileHandoffs } from "@/lib/file-handoff";
import { useToolDefaults } from "@/hooks/useToolDefaults";
import { FileIntake, StudioLayout, StudioProgress, StudioResult, StudioFile } from "@/skins/experience/ToolStudio";

type PageSize = "auto" | "a4" | "letter";
const sizes: { id: PageSize; label: string; desc: string }[] = [
    { id: "auto",   label: "Auto",   desc: "Match image dimensions" },
    { id: "a4",     label: "A4",     desc: "210 × 297 mm" },
    { id: "letter", label: "Letter", desc: "8.5 × 11 in" },
];

interface ImageToPdfUIProps {
    accept?: string;
    formatsLabel?: string;
    nounLabel?: string;
    handoffSlug?: string;
}

const IMAGE_TO_PDF_DEFAULTS: { pageSize: PageSize } = {
    pageSize: "auto",
};

export function ImageToPdfUI({
    accept = "image/*",
    formatsLabel = "JPEG · PNG · WebP · BMP · TIFF · HEIC — multiple allowed",
    nounLabel = "image",
    handoffSlug = "image-to-pdf",
}: ImageToPdfUIProps = {}) {
    const [config, , { setField }] = useToolDefaults("image-to-pdf", IMAGE_TO_PDF_DEFAULTS);
    const { pageSize } = config;
    const setPageSize = useCallback((v: React.SetStateAction<typeof IMAGE_TO_PDF_DEFAULTS["pageSize"]>) => setField("pageSize", v), [setField]);
    const [files, setFiles] = useState<{ id: string; name: string; size: string; raw: File }[]>([]);

    const [state, setState] = useState<"idle" | "processing" | "done">("idle");
    const [error, setError] = useState<string | null>(null);
    const [dragIdx, setDragIdx] = useState<number | null>(null);

    const add = useCallback((fl: FileList | File[]) => {
        setFiles(p => [...p, ...Array.from(fl).map(f => ({ id: Math.random().toString(36).slice(2), name: f.name, size: formatFileSize(f.size), raw: f }))]);
        setState("idle"); setError(null);
    }, []);

    useEffect(() => {
        let cancelled = false;
        queueMicrotask(() => {
            if (cancelled) return;
            void consumeFileHandoffs(handoffSlug).then(files => {
                if (!cancelled && files.length) add(files);
            });
        });
        return () => { cancelled = true; };
    }, [handoffSlug, add]);

    // Try with sample — loads the bundled JPEG so the user can try the flow
    // without leaving the page. Only available when accept includes JPEG-ish
    // formats (the wrappers in NamedImageToPdfVariants may narrow accept).
    const [loadingSample, setLoadingSample] = useState(false);
    const sampleSupported = !accept || accept === "image/*" || /jpe?g/i.test(accept);
    const trySample = useCallback(async () => {
        if (loadingSample || !sampleSupported) return;
        setLoadingSample(true);
        try {
            const f = await loadSampleJpg();
            add([f]);
            toast.message("Sample image loaded", { description: "Bound into a single-page PDF.", duration: 2400 });
        } catch (e) {
            console.error(e);
            toast.error("Couldn't load the sample image.");
        } finally {
            setLoadingSample(false);
        }
    }, [loadingSample, sampleSupported, add]);

    const moveFile = (from: number, to: number) => {
        if (to < 0 || to >= files.length || from === to) return;
        setFiles(p => {
            const next = [...p];
            const [moved] = next.splice(from, 1);
            next.splice(to, 0, moved);
            return next;
        });
    };

    const process = useCallback(async () => {
        if (!files.length) return;
        setState("processing"); setError(null);
        try {
            const outName = buildOutputFilename(files[0]?.name, null, "pdf");
            await processFilesAndDownload("/image-to-pdf", files.map(f => f.raw), outName, { page_size: pageSize });
            setState("done");
            emitToolSuccess("Image to PDF");
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Conversion failed";
            setError(friendlyError(msg, "Couldn't pack those images into a PDF."));
            setState("idle");
        }
    }, [files, pageSize]);

    // Cmd+Enter
    useEffect(() => {
        const h = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && files.length && state !== "processing") {
                e.preventDefault(); process();
            }
        };
        window.addEventListener("keydown", h);
        return () => window.removeEventListener("keydown", h);
    }, [files, state, process]);

    if (state === "done") return <StudioResult title={`${files.length} ${nounLabel}${files.length > 1 ? "s" : ""}, one PDF.`} detail="Your download has started. Each image has its own page, in your chosen order.">
        <StudioFile name={buildOutputFilename(files[0]?.name, null, "pdf")} detail={`${files.length} pages · ${sizes.find(size => size.id === pageSize)?.label} page size`} status="done" />
        <div className="ts-actions"><button className="ts-text-button" onClick={() => { setFiles([]); setState("idle"); }}>Convert more</button></div>
    </StudioResult>;
    return <StudioLayout className="ts-image-binding" options={<>
        <div><p className="ts-eyebrow">The shape of your document</p><h3>Page size</h3><div className="ts-choices">{sizes.map(size => <button className="ts-choice" key={size.id} onClick={() => setPageSize(size.id)} aria-pressed={pageSize === size.id} disabled={state === "processing"}><strong>{size.label}</strong><span>{size.desc}</span></button>)}</div></div>
        <div><p>Every image gets a page. Drag images into order, or use the arrow controls.</p><p className="ts-caption">{files.length} {nounLabel}{files.length !== 1 ? "s" : ""} selected</p></div>
        <div className="ts-actions"><button className="ts-primary-button" onClick={process} disabled={!files.length || state === "processing"}><Download size={16} /> Convert {files.length} {nounLabel}{files.length !== 1 ? "s" : ""} → PDF</button>{files.length > 0 && <button className="ts-text-button" disabled={state === "processing"} onClick={() => setFiles([])} aria-label="Clear all images">Clear</button>}</div>
    </>}>
        <FileIntake accepts={accept} multiple onFiles={add} label="Upload images" title="Turn pictures into pages." detail={formatsLabel} disabled={state === "processing"} compact={files.length > 0} />
        {files.length === 0 && sampleSupported && <button className="ts-text-button" onClick={trySample} disabled={loadingSample}><Sparkles size={15} /> {loadingSample ? "Loading sample…" : "Try with a sample image"}</button>}
        {files.length > 0 && <section className="ts-image-pages" aria-label="Page order">{files.map((file, i) => <article key={file.id} className="ts-image-page" draggable={state !== "processing"}
            onDragStart={() => setDragIdx(i)} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); if (dragIdx !== null && state !== "processing") moveFile(dragIdx, i); setDragIdx(null); }} onDragEnd={() => setDragIdx(null)} data-dragging={dragIdx === i}>
            <ImagePagePreview file={file.raw} /><div className="ts-image-page-info"><span>{i + 1}</span><p>{file.name}<small>{file.size}</small></p></div>
            <div className="ts-image-page-actions"><button className="ts-icon-button" onClick={() => moveFile(i, i - 1)} disabled={i === 0 || state === "processing"} aria-label="Move up"><ChevronUp size={16} /></button><button className="ts-icon-button" onClick={() => moveFile(i, i + 1)} disabled={i === files.length - 1 || state === "processing"} aria-label="Move down"><ChevronDown size={16} /></button><button className="ts-icon-button" disabled={state === "processing"} onClick={() => setFiles(prev => prev.filter(item => item.id !== file.id))} aria-label="Remove"><X size={16} /></button></div>
        </article>)}</section>}
        {state === "processing" && <StudioProgress label="Making a home for your images" detail={`${files.length} images, arranged in one PDF.`} />}
        {error && <div role="alert" className="ts-error">{error}</div>}
    </StudioLayout>;
}
function ImagePagePreview({ file }: { file: File }) {
    const [url, setUrl] = useState<string>();
    const [failed, setFailed] = useState(false);
    useEffect(() => { const next = URL.createObjectURL(file); setUrl(next); return () => URL.revokeObjectURL(next); }, [file]);
    return <div className="ts-image-page-preview">{url && !failed ? <img src={url} alt={`Preview of ${file.name}`} onError={() => setFailed(true)} /> : <span><ImageIcon size={34} /><small>Image preview unavailable</small></span>}</div>;
}
