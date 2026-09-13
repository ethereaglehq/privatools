import { fileFormatLabel } from "./file-format-label";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowDownToLine, ArrowUpRight, Check, FileText, Plus, X } from "lucide-react";
import "./tool-studio.css";

export function FileIntake({ accepts, multiple, onFiles, label = "Choose files", title, detail, disabled = false, compact = false }: {
    accepts?: string; multiple?: boolean; onFiles: (files: File[]) => void; label?: string;
    title?: string; detail?: string; disabled?: boolean; compact?: boolean;
}) {
    const input = useRef<HTMLInputElement>(null);
    const [dragging, setDragging] = useState(false);
    const open = () => { if (!disabled) input.current?.click(); };
    const receive = (files: FileList | null) => { if (!disabled && files?.length) onFiles(Array.from(files)); };
    const format = fileFormatLabel(accepts);
    return <div className={`ts-intake${compact ? " ts-intake-compact" : ""}`} data-dragging={dragging} data-disabled={disabled}
        role="button" tabIndex={disabled ? -1 : 0} aria-label={label} aria-disabled={disabled}
        onClick={open} onKeyDown={event => { if (event.target === event.currentTarget && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); open(); } }}
        onDragOver={event => { event.preventDefault(); if (!disabled) setDragging(true); }}
        onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); receive(event.dataTransfer.files); }}>
        <input ref={input} type="file" accept={accepts} multiple={multiple} disabled={disabled} className="ts-native-input"
            onClick={event => event.stopPropagation()} onChange={event => { receive(event.target.files); event.target.value = ""; }} />
        <div className="ts-intake-art" aria-hidden="true"><span className="ts-sheet ts-sheet-back" /><span className="ts-sheet ts-sheet-front"><FileText size={31} strokeWidth={1.35} /><span>{format?.slice(0, 6)}</span><i /><i /><i /></span><span className="ts-intake-plus"><Plus size={22} /></span></div>
        <div className="ts-intake-copy"><span className="ts-intake-overline">{compact ? "Your selection" : "Start with your file"}</span><h3>{compact ? "Add to your selection" : title || label}</h3><p>{detail || "Choose from your device, or bring your files into this space."}</p><span className="ts-intake-choose">{compact ? "Add files" : multiple ? "Choose files" : "Choose a file"}<ArrowUpRight size={18} /></span><span className="ts-intake-drag">or drag {multiple ? "them" : "it"} here</span></div>
    </div>;
}

export function StudioLayout({ children, options, summary, className = "" }: { children: ReactNode; options?: ReactNode; summary?: ReactNode; className?: string }) {
    return <div className={`tool-studio ${options ? "tool-studio-with-options" : ""} ${className}`}>
        <div className="ts-canvas">{children}</div>
        {options && <aside className="ts-options">{options}</aside>}
        {summary && <div className="ts-summary">{summary}</div>}
    </div>;
}

export function StudioProgress({ label = "Working on your file", progress, detail, onCancel }: { label?: string; progress?: number; detail?: string; onCancel?: () => void }) {
    const value = progress === undefined ? undefined : Math.max(0, Math.min(100, progress));
    return <section className="ts-progress" role="status" aria-live="polite"><div className="ts-progress-heading"><span className="ts-orbit" aria-hidden="true"><i /><i /><i /></span><div><h3>{label}</h3>{detail && <p>{detail}</p>}</div>{onCancel && <button type="button" onClick={onCancel} className="ts-text-button">Cancel</button>}</div><div className="ts-progress-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={value} data-indeterminate={value === undefined}><i style={value === undefined ? undefined : { transform: `scaleX(${value / 100})` }} /></div>{value !== undefined && <span className="ts-progress-value">{Math.round(value)}%</span>}</section>;
}

export function StudioResult({ title, detail, children, onReset }: { title: string; detail?: string; children?: ReactNode; onReset?: () => void }) {
    return <section className="ts-result"><header><div className="ts-result-art" aria-hidden="true"><span /><span /><Check size={38} strokeWidth={1.5} /></div><div><p className="ts-eyebrow">Ready for what’s next</p><h2>{title}</h2>{detail && <p className="ts-result-detail">{detail}</p>}</div></header><div className="ts-result-content">{children}</div>{onReset && <button type="button" className="ts-text-button ts-result-reset" onClick={onReset}>Start with another file <ArrowUpRight size={16} /></button>}</section>;
}

export function StudioFile({ name, detail, status, onRemove, onDownload, children, removeLabel }: { name: string; detail?: string; status?: string; onRemove?: () => void; onDownload?: () => void; children?: ReactNode; removeLabel?: string }) {
    return <article className="ts-file" data-status={status}><span className="ts-file-icon" aria-hidden="true">{status === "done" ? <Check size={22} /> : <FileText size={22} strokeWidth={1.5} />}</span><div className="ts-file-copy"><h4>{name}</h4>{detail && <p>{detail}</p>}{children}</div>{onDownload && <button type="button" className="ts-icon-button" aria-label={`Download ${name}`} onClick={onDownload}><ArrowDownToLine size={18} /></button>}{onRemove && <button type="button" className="ts-icon-button" aria-label={removeLabel || `Remove ${name}`} onClick={onRemove}><X size={17} /></button>}</article>;
}

/** Object URLs stay on this device and are released when their source changes. */
export function LocalFilePreview({ file, name, label = "Preview" }: { file: Blob; name: string; label?: string }) {
    const [url, setUrl] = useState("");
    const [failed, setFailed] = useState(false);
    const ext = name.split(".").pop()?.toLowerCase() || "";
    const kind = /^(png|jpe?g|webp|gif|bmp|svg|avif)$/.test(ext) ? "image"
        : /^(mp4|mov|webm|m4v|ogv)$/.test(ext) ? "video"
        : /^(mp3|wav|ogg|m4a|aac|flac|opus)$/.test(ext) ? "audio" : null;
    useEffect(() => {
        if (!kind) return;
        const next = URL.createObjectURL(file);
        setUrl(next); setFailed(false);
        return () => URL.revokeObjectURL(next);
    }, [file, kind]);
    if (!kind || !url) return null;
    return <figure className="ts-local-preview" data-kind={kind}>
        <figcaption><span>{label}</span><span>{name}</span></figcaption>
        {failed ? <p className="ts-caption">This browser cannot preview this format. Your file can still be processed or downloaded.</p>
            : kind === "image" ? <img src={url} alt={name} onError={() => setFailed(true)} />
            : kind === "video" ? <video src={url} controls preload="metadata" aria-label={`${label}: ${name}`} onError={() => setFailed(true)} />
            : <audio src={url} controls preload="metadata" aria-label={`${label}: ${name}`} onError={() => setFailed(true)} />}
    </figure>;
}

export function ConversionPath({ accepts, output }: { accepts: string; output: string }) {
    const target = output.includes(".") ? output.split(".").pop() : output;
    return <div className="ts-conversion-path" aria-label={`${fileFormatLabel(accepts)} to ${target?.toUpperCase()}`}><span>{fileFormatLabel(accepts)}</span><ArrowUpRight size={22} aria-hidden="true"/><span>{target?.toUpperCase()}</span></div>;
}
