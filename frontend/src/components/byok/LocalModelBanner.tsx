/**
 * Offers an explicit browser-model download before running a tool.
 *
 * Before this, a first-time visitor to Summarize PDF picked a file, pressed
 * run, and then waited on a silent 250 MB download with no indication that
 * anything was happening. Now the download starts on mount and says so.
 *
 * Rendered from `withRealTools`, which is the one place every tool page in
 * every skin passes through, so PDF and non-PDF tools get it alike.
 */

import { useEffect, useRef, useState } from "react";
import { Loader2, Check, HardDrive, RotateCw } from "lucide-react";

import { LOCAL_MODELS, type LocalModelInfo } from "@/lib/localModels";

/**
 * The model a slug needs, or undefined.
 *
 * `LOCAL_MODELS` order decides ties: Transcribe Audio lists Whisper Tiny
 * before Whisper Base, so the small one is what we fetch unprompted. Anyone
 * who wants the accurate one can still install it from the AI hub.
 */
const BY_SLUG = new Map<string, LocalModelInfo>();
for (const m of LOCAL_MODELS) {
    const slug = m.toolHref.replace(/^#\/tools?\//, "");
    if (!BY_SLUG.has(slug)) BY_SLUG.set(slug, m);
}

type Phase = "checking" | "idle" | "downloading" | "ready" | "error";

export function LocalModelBanner({ slug }: { slug: string }) {
    const model = BY_SLUG.get(slug);
    const [phase, setPhase] = useState<Phase>("idle");
    const [pct, setPct] = useState(0);
    const [err, setErr] = useState("");
    // StrictMode mounts twice in development; without this the download starts
    // twice and the two progress streams fight over the same number.
    const started = useRef(false);
    // Set by the effect so the retry button can call it. A ref rather than a
    // window global: two banners must not clobber each other's handler.
    const beginRef = useRef<() => void>(() => {});

    useEffect(() => {
        if (!model) return;
        let alive = true;

        const begin = async () => {
            if (started.current) return;
            started.current = true;
            setPhase("downloading");
            setPct(0);
            try {
                await model.predownload((p) => { if (alive) setPct(p); });
                if (alive) { setPct(100); setPhase("ready"); }
            } catch (e) {
                started.current = false;
                if (alive) {
                    setErr(e instanceof Error ? e.message : "The download did not finish.");
                    setPhase("error");
                }
            }
        };

        // Opening a tool must not download hundreds of megabytes, nor imply
        // that its independently selected server/BYOK engine is browser-only.
        setPhase("idle");
        started.current = false;

        beginRef.current = () => { void begin(); };
        return () => { alive = false; };
    }, [model]);

    // Nothing to fetch, still looking, or it was already here when we arrived:
    // say nothing. A banner that announces a no-op is noise.
    if (!model || phase === "checking") return null;
    if (phase === "ready" && pct === 100 && !started.current) return null;

    const retry = () => beginRef.current();

    return (
        <div
            className="mb-4 rounded-xl border border-border bg-card px-4 py-3"
            role="status"
            aria-live="polite"
        >
            <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-secondary">
                    {phase === "downloading" && <Loader2 size={14} className="animate-spin text-accent" />}
                    {phase === "ready" && <Check size={14} className="text-accent" />}
                    {phase === "idle" && <HardDrive size={14} className="text-muted-foreground" />}
                    {phase === "error" && <RotateCw size={14} className="text-destructive" />}
                </div>

                <div className="min-w-0 flex-1">
                    <p className="text-[13px] font-medium text-foreground">
                        {phase === "downloading" && `Preparing the browser model — ${pct}%`}
                        {phase === "ready" && "Browser model ready for this visit."}
                        {phase === "idle" && `Optional browser model · ${model.approxLabel}`}
                        {phase === "error" && "The model could not download"}
                    </p>
                    <p className="mt-0.5 text-[11.5px] text-muted-foreground">
                        {phase === "downloading"
                            && `${model.label} downloads into this browser. Saved files can be reused while your browser keeps them.`}
                        {phase === "ready"
                            && "Choose the on-device engine to keep processing here. Server and API-key modes have different data paths."}
                        {phase === "idle"
                            && "Download ahead of time, or let the on-device engine prepare it when you run the tool."}
                        {phase === "error" && err}
                    </p>
                </div>

                {(phase === "idle" || phase === "error") && (
                    <button
                        type="button"
                        onClick={retry}
                        className="shrink-0 rounded-lg border border-border bg-card px-3 py-1.5 text-[12px] font-semibold text-foreground transition-colors hover:border-border-strong"
                    >
                        {phase === "error" ? "Try again" : "Download"}
                    </button>
                )}
            </div>

            {phase === "downloading" && (
                <div className="mt-2.5 h-1 w-full overflow-hidden rounded-full bg-secondary">
                    <div
                        className="h-full rounded-full bg-accent transition-[width] duration-300 ease-out"
                        style={{ width: `${Math.max(2, pct)}%` }}
                    />
                </div>
            )}
        </div>
    );
}
