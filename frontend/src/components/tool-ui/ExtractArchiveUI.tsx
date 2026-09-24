import { useCallback, useEffect, useRef, useState } from "react";
import { Archive, Download, File, Folder, Loader2 } from "lucide-react";
import { postFormData, formatFileSize, downloadBlob } from "@/lib/api";
import { emitToolRun } from "@/lib/toolRun";
import { friendlyError } from "@/lib/utils";
import { consumeFileHandoff } from "@/lib/file-handoff";
import { FileUploadZone, ProcessingBar } from "./FileUploadZone";
import { LabWorkspace } from "./SpecialistTools";
import { readZipDirectory, type ZipDirectory } from "./zip-directory";

export function ExtractArchiveUI() {
    const [file, setFile] = useState<File | null>(null), [busy, setBusy] = useState(false), [result, setResult] = useState<Blob | null>(null), [directory, setDirectory] = useState<ZipDirectory | null>(null), [error, setError] = useState<string | null>(null), [listingError, setListingError] = useState<string | null>(null);
    const active = useRef(false), generation = useRef(0);
    const invalidatePending = useCallback(() => { generation.current++; }, []);
    useEffect(() => { let cancelled = false; void consumeFileHandoff("extract-archive").then(value => { if (!cancelled && value) setFile(value); }); return () => { cancelled = true; invalidatePending(); }; }, [invalidatePending]);
    const choose = (value: File | null) => { if (active.current) return; setFile(value); setError(null); setResult(null); setDirectory(null); setListingError(null); };
    async function extract() {
        if (!file || active.current) return;
        active.current = true; const current = ++generation.current; setBusy(true); setError(null); setResult(null); setDirectory(null); setListingError(null);
        try {
            const response = await postFormData("/extract-archive", () => { const form = new FormData(); form.append("file", file); return form; }, {timeoutMs: 300_000});
            const blob = await response.blob();
            if (generation.current !== current) return;
            setResult(blob);
            emitToolRun({outcome: "success", files: 1});
            try { const manifest = await readZipDirectory(blob); if (generation.current === current) setDirectory(manifest); }
            catch (e) { if (generation.current === current) setListingError(e instanceof Error ? e.message : "Couldn't display the file list. Your ZIP is ready to download."); }
        } catch (e) { if (generation.current === current) setError(friendlyError(e instanceof Error ? e.message : "", "Couldn't open that archive.")); emitToolRun({outcome: "error", files: 1}, e); }
        finally { if (generation.current === current) { active.current = false; setBusy(false); } }
    }
    return <LabWorkspace kind="archive"><div className="pt-archive-workspace"><section className="pt-archive-intake"><div className="pt-lab-toolbar"><h2>Open your archive</h2><Archive size={23}/></div><FileUploadZone file={file} onFileSelect={choose} onClear={() => choose(null)} accept=".zip,.tar,.tar.gz,.tgz,.tar.bz2,.tbz2,.tar.xz,.txz" label="Choose an archive" hint="ZIP, TAR, GZ, BZ2 or XZ archive"/><p className="pt-lab-caption">The server checks and extracts the archive, then packages its contents as a standard ZIP. You can inspect the file list before downloading.</p><button className="pt-lab-button is-primary pt-lab-spaced" disabled={!file || busy} onClick={() => void extract()}>{busy ? <Loader2 size={16} className="animate-spin"/> : <Archive size={16}/>} {busy ? "Opening archive…" : result ? "Extract again" : "Extract archive"}</button>{busy && <ProcessingBar label="Extracting and packaging your files…"/>}{error && <p role="alert" className="pt-lab-issue is-error">{error}</p>}</section><section className="pt-archive-contents"><div className="pt-lab-toolbar"><h2>{result ? "Inside your archive" : "A look inside"}</h2>{result && <span>{formatFileSize(result.size)} ZIP</span>}</div>{result ? <><div role="status" className="pt-lab-fact"><strong>{directory ? `${directory.total} entries ready` : "ZIP ready"}</strong></div>{directory && <ul className="pt-archive-list">{directory.entries.map((entry, i) => <li key={i}>{entry.directory ? <Folder size={17}/> : <File size={17}/>}<span title={entry.name}>{entry.name}</span><small>{entry.directory ? "Folder" : formatFileSize(entry.bytes)}</small></li>)}</ul>}{directory?.truncated && <p className="pt-lab-caption">Showing the first 1,000 entries. The download contains the complete archive.</p>}{listingError && <p className="pt-lab-caption" role="status">{listingError}</p>}<button className="pt-lab-button is-primary pt-lab-spaced" onClick={() => downloadBlob(result, "extracted.zip")}><Download size={16}/>Download extracted ZIP</button></> : <div className="pt-specialist-empty"><Folder size={42}/><h3>Your files, unpacked</h3><p>File names and sizes will appear here after extraction. Nothing is saved to your device until you download.</p></div>}</section></div></LabWorkspace>;
}
