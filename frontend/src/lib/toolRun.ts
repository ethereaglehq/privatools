/**
 * Usage signal for the analytics beacon: one event per tool run.
 *
 * Tool code dispatches a DOM event and never touches analytics directly, the
 * same pattern as the first-success celebration. The beacon decides whether
 * anything is sent and what the tool is called; callers only report shape.
 */
export const TOOL_RUN_EVENT = "privatools:tool-run";

export type ToolRunMode = "single" | "batch" | "pipeline";
export type ToolRunOutcome = "success" | "partial" | "error";

export interface ToolRunDetail {
    /** Registry slug. Tool pages omit it; the beacon reads it from the route. */
    slug?: string;
    /** Defaults to "single" (a tool page). */
    mode?: ToolRunMode;
    outcome: ToolRunOutcome;
    /** How many files the run handled. Never names, sizes or contents. */
    files?: number;
}

export function emitToolRun(detail: ToolRunDetail): void {
    try {
        window.dispatchEvent(new CustomEvent<ToolRunDetail>(TOOL_RUN_EVENT, { detail }));
    } catch { /* */ }
}

/** Collapse per-file results into one outcome; null when nothing ran. */
export function runOutcome(done: number, failed: number): ToolRunOutcome | null {
    if (done + failed === 0) return null;
    if (failed === 0) return "success";
    return done === 0 ? "error" : "partial";
}
