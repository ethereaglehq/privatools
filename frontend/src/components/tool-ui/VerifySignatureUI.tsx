/**
 * VerifySignatureUI — check each PDF signature against the file and the certificate it carries.
 * Workshop: lab-report style result panel with signer rows + status chips.
 * The server does not check certificates against a trust list, so no verdict here names who signed.
 */
import { useCallback, useEffect, useState } from "react";
import { Loader2, AlertCircle, ShieldCheck, ShieldAlert, ShieldX, RotateCcw, Search, ShieldQuestion } from "lucide-react";
import { cn, friendlyError } from "@/lib/utils";
import { uploadFile } from "@/lib/api";
import { emitToolRun } from "@/lib/toolRun";
import { FileUploadZone } from "./FileUploadZone";

type SignatureStatus = "valid" | "modified" | "invalid" | "unsigned" | "unchecked";
type Modification = "none" | "form_filling" | "annotations" | "other" | null;

interface SignatureEntry {
    field: string;
    signed: boolean;
    kind: "signature" | "timestamp";
    signer: string;
    date: string;
    status: SignatureStatus;
    modification: Modification;
    certificate: { subject: string; issuer: string; valid_from: string; valid_until: string; self_signed: boolean } | null;
    reason: string;
}

interface SigResult {
    has_signatures: boolean;
    signatures: SignatureEntry[];
    note?: string;
}

type Tone = "accent" | "copper" | "danger" | "muted";
type Verdict = "none" | "empty" | "invalid" | "altered" | "unchecked" | "changed" | "valid";

const CHANGES: Record<"form_filling" | "annotations" | "other", string> = {
    form_filling: "Saved after signing: form fields were filled in or signed. The signed version is unchanged.",
    annotations: "Saved after signing: comments or other annotations. The signed version is unchanged.",
    other: "Saved after signing: edits that can change what the document shows.",
};

const STATUS_META: Record<SignatureStatus, { label: string; tone: Tone; icon: typeof ShieldCheck }> = {
    valid: { label: "Valid", tone: "accent", icon: ShieldCheck },
    modified: { label: "Later additions", tone: "copper", icon: ShieldAlert },
    invalid: { label: "Invalid", tone: "danger", icon: ShieldX },
    unsigned: { label: "Not signed", tone: "muted", icon: ShieldQuestion },
    unchecked: { label: "Not checked", tone: "copper", icon: ShieldQuestion },
};

function rowMeta(s: SignatureEntry) {
    // Changes that can alter the page are as serious as a failed check.
    if (s.status === "modified" && s.modification === "other") return { label: "Changed", tone: "danger" as Tone, icon: ShieldX };
    return STATUS_META[s.status] ?? STATUS_META.unchecked;
}

function verdictOf(signatures: SignatureEntry[]): Verdict {
    if (!signatures.length) return "none";
    const signed = signatures.filter(s => s.signed);
    if (!signed.length) return "empty";
    if (signed.some(s => s.status === "invalid")) return "invalid";
    if (signed.some(s => s.status === "modified" && s.modification === "other")) return "altered";
    if (signed.some(s => s.status === "unchecked")) return "unchecked";
    if (signed.some(s => s.status === "modified")) return "changed";
    return "valid";
}

function formatDate(iso: string) {
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? iso : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function details(s: SignatureEntry) {
    const lines: string[] = [];
    if (s.certificate) {
        lines.push(`Certificate: ${s.certificate.subject} · issued by ${s.certificate.issuer}${s.certificate.self_signed ? " (self-signed)" : ""}`);
    }
    if (s.status === "modified" && s.modification && s.modification !== "none") lines.push(CHANGES[s.modification]);
    if (s.reason) lines.push(s.reason);
    return lines;
}

export function VerifySignatureUI() {
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<"idle" | "processing" | "done">("idle");
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<SigResult | null>(null);

    const canProcess = !!file && status !== "processing";

    const process = useCallback(async () => {
        if (!file) return;
        setStatus("processing"); setError(null);
        try {
            const res = await uploadFile("/verify-signature", file);
            const data = await res.json();
            setResult(data);
            setStatus("done");
            emitToolRun({ outcome: "success", files: 1 });
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Could not verify signatures";
            setError(friendlyError(msg, "Couldn't verify that signature."));
            setStatus("idle");
            emitToolRun({ outcome: "error", files: 1 });
        }
    }, [file]);

    useEffect(() => {
        const h = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && canProcess) { e.preventDefault(); process(); }
        };
        window.addEventListener("keydown", h);
        return () => window.removeEventListener("keydown", h);
    }, [canProcess, process]);

    const signatures = result?.signatures ?? [];
    const signedCount = signatures.filter(s => s.signed).length;
    const verdict = verdictOf(signatures);
    const verdictMeta: Record<Verdict, { tone: Tone; title: string; sub: string; icon: typeof ShieldCheck }> = {
        none: { tone: "muted", title: "No signature fields found", sub: "A visible signature image is not a digital signature field.", icon: ShieldQuestion },
        empty: { tone: "muted", title: "Signature fields are empty", sub: "The PDF has places for signatures, but none has been signed.", icon: ShieldQuestion },
        invalid: { tone: "danger", title: "A signature does not match the document", sub: "The signed content has changed, a signature does not match its certificate, or part of the file is outside what was signed.", icon: ShieldX },
        altered: { tone: "danger", title: "Changed after signing", sub: "The file was saved again after signing, with changes that can alter what it shows.", icon: ShieldX },
        unchecked: { tone: "copper", title: "A signature could not be checked", sub: "The reason is shown below. Open the file in a PDF reader that validates signatures.", icon: ShieldAlert },
        changed: { tone: "copper", title: "Signed, with later additions", sub: "Each signed version is unchanged; form filling, further signatures or comments were added afterwards.", icon: ShieldAlert },
        valid: { tone: "accent", title: signedCount === 1 ? "Signature matches the document" : "Signatures match the document", sub: "Nothing has changed since signing. Certificates are not checked against a trust list, so this does not confirm who signed.", icon: ShieldCheck },
    };

    const toneStyles = (tone: Tone) => {
        if (tone === "accent") return { border: "border-accent/30 bg-accent/[0.05]", icon: "bg-accent/15 border-accent/35", iconColor: "text-accent", label: "text-accent", chip: "bg-accent/15 text-accent" };
        if (tone === "copper") return { border: "border-copper/40 bg-copper-soft/40", icon: "bg-copper/15 border-copper/35", iconColor: "text-copper", label: "text-copper", chip: "bg-copper/15 text-copper" };
        if (tone === "danger") return { border: "border-destructive/40 bg-destructive/[0.05]", icon: "bg-destructive/15 border-destructive/35", iconColor: "text-destructive", label: "text-destructive", chip: "bg-destructive/15 text-destructive" };
        return { border: "border-border bg-card", icon: "bg-secondary border-border", iconColor: "text-muted-foreground", label: "text-muted-foreground", chip: "bg-secondary text-muted-foreground" };
    };

    return (
        <div className="space-y-4">
            <FileUploadZone
                file={file}
                onFileSelect={setFile}
                onClear={() => { setFile(null); setResult(null); setStatus("idle"); }}
                accept=".pdf"
                label="Drop signed PDF"
                hint="Checks every signature against the file"
            />

            {status === "done" && result && (
                <div className="space-y-3 animate-fade-up">
                    {/* Verdict panel: the most serious finding across all signatures */}
                    {(() => {
                        const meta = verdictMeta[verdict];
                        const t = toneStyles(meta.tone);
                        const Icon = meta.icon;
                        const cornerTone = meta.tone === "copper" || meta.tone === "danger" ? meta.tone : "accent";
                        return (
                            <div className={cn("relative rounded-2xl border overflow-hidden", t.border)} role="status" aria-live="polite">
                                <div className="relative p-6 animate-corner-extend">
                                    <CornerMarks tone={cornerTone} />
                                    <div className="flex items-start gap-4">
                                        <div className={cn("h-12 w-12 rounded-xl border flex items-center justify-center shrink-0 animate-success-pop", t.icon)}>
                                            <Icon size={22} className={t.iconColor} strokeWidth={1.75} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className={cn("font-medium text-[11.5px] mb-1.5", t.label)}>
                                                Verification result
                                            </p>
                                            <h3 className="font-display text-[20px] font-bold text-foreground tracking-[-0.02em] leading-tight">
                                                {meta.title}
                                            </h3>
                                            <p className="text-[13px] text-muted-foreground mt-1">{meta.sub}</p>
                                            <p className="font-medium text-[11.5px] text-muted-foreground mt-2">
                                                {signatures.length} signature field{signatures.length !== 1 && "s"} found, {signedCount} signed
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })()}

                    {/* One row per signature field */}
                    {signatures.length > 0 && (
                        <div className="rounded-xl border border-border bg-card overflow-hidden">
                            <div className="font-medium px-4 py-2 border-b border-border bg-paper-2/40 text-[11.5px] text-muted-foreground">
                                Signatures
                            </div>
                            <div className="divide-y divide-border">
                                {signatures.map((s, i) => {
                                    const meta = rowMeta(s);
                                    const t = toneStyles(meta.tone);
                                    const RowIcon = meta.icon;
                                    const lines = details(s);
                                    const when = s.signed ? (s.date ? formatDate(s.date) : "Date unknown") : "";
                                    return (
                                        <div key={i} className="px-4 py-3">
                                            <div className="flex items-center gap-3">
                                                <span className="font-mono text-[10px] tracking-wider text-muted-foreground w-6 text-right shrink-0">{String(i + 1).padStart(2, "0")}</span>
                                                <div className={cn("h-8 w-8 rounded-lg border flex items-center justify-center shrink-0", t.icon)}>
                                                    <RowIcon size={14} className={t.iconColor} />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-[13.5px] font-medium text-foreground truncate">{s.signer || (s.signed ? "Unknown signer" : "Empty signature field")}</p>
                                                    <p className="font-mono text-[10.5px] tracking-[0.04em] text-muted-foreground mt-0.5 break-words">
                                                        {[s.kind === "timestamp" ? "Document timestamp" : "Signature", when, `field ${s.field}`].filter(Boolean).join(" · ")}
                                                    </p>
                                                </div>
                                                <span className={cn("font-medium text-[9.5px] px-2 py-0.5 rounded shrink-0", t.chip)}>
                                                    {meta.label}
                                                </span>
                                            </div>
                                            {lines.length > 0 && (
                                                <div className="mt-2 pl-[4.25rem] space-y-1">
                                                    {lines.map(line => <p key={line} className="text-[12px] text-muted-foreground break-words">{line}</p>)}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    <p className="font-medium text-[11px] text-muted-foreground">
                        Checks that each signature matches the file and the certificate inside it. Certificates are not checked against a trust list or for revocation, so confirm who signed in a PDF reader that validates certificates.
                    </p>

                    <button
                        onClick={() => { setFile(null); setStatus("idle"); setResult(null); }}
                        className="inline-flex items-center gap-1.5 h-9 px-4 rounded-md border border-border bg-card text-[13px] font-medium text-foreground hover:bg-secondary/60 transition-colors"
                    >
                        <RotateCcw size={12} /> Verify another
                    </button>
                </div>
            )}

            {error && (
                <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/[0.06] px-3 py-2.5 text-[13px] text-destructive">
                    <AlertCircle size={13} className="shrink-0" />{error}
                </div>
            )}

            {status !== "done" && (
                <div className="flex items-center gap-3 flex-wrap">
                    <button onClick={process} disabled={!canProcess} className="btn-accent disabled:opacity-60 disabled:cursor-not-allowed">
                        {status === "processing" ? <><Loader2 size={13} className="animate-spin" /> Checking…</> : <><Search size={13} /> Verify signatures</>}
                    </button>
                    {canProcess && (
                        <kbd className="hidden sm:inline-flex items-center gap-0.5 font-mono text-[10px] text-muted-foreground bg-secondary/30 rounded px-1.5 py-0.5">⌘↵</kbd>
                    )}
                </div>
            )}
        </div>
    );
}

function CornerMarks({ tone = "accent" }: { tone?: "accent" | "copper" | "danger" }) {
    const cls = "corner-mark absolute h-3 w-3 pointer-events-none";
    const c = tone === "danger" ? "bg-destructive" : tone === "copper" ? "bg-copper" : "bg-accent";
    return (
        <>
            <span className={`${cls} -top-1 -left-1`}><span className={`absolute top-0 left-0 h-px w-3 ${c}/70`} /><span className={`absolute top-0 left-0 w-px h-3 ${c}/70`} /></span>
            <span className={`${cls} -top-1 -right-1`}><span className={`absolute top-0 right-0 h-px w-3 ${c}/70`} /><span className={`absolute top-0 right-0 w-px h-3 ${c}/70`} /></span>
            <span className={`${cls} -bottom-1 -left-1`}><span className={`absolute bottom-0 left-0 h-px w-3 ${c}/70`} /><span className={`absolute bottom-0 left-0 w-px h-3 ${c}/70`} /></span>
            <span className={`${cls} -bottom-1 -right-1`}><span className={`absolute bottom-0 right-0 h-px w-3 ${c}/70`} /><span className={`absolute bottom-0 right-0 w-px h-3 ${c}/70`} /></span>
        </>
    );
}
