import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import PipelinePage from "@/pages/PipelinePage";
import BatchPage from "@/pages/BatchPage";
const api = vi.hoisted(() => ({ postFormData: vi.fn(), downloadBlob: vi.fn() }));
vi.mock("@/lib/api", async (load) => ({ ...await load<typeof import("@/lib/api")>(), ...api }));

const RUN_EVENT = "privatools:tool-run";
type Detail = Record<string, unknown>;
function listen(): Detail[] {
    const seen: Detail[] = [];
    window.addEventListener(RUN_EVENT, event => seen.push((event as CustomEvent<Detail>).detail));
    return seen;
}
function ok() { return { blob: async () => new Blob(["output"], { type: "application/pdf" }), headers: new Headers() } as Response; }
/** The shape api.ts gives an HTTP error: a message the UI shows, plus the status. */
function httpError(status: number) { return Object.assign(new Error("boom secret"), { __status: status }); }
const original = new File(["%PDF-1.4\noriginal"], "Secret.pdf", { type: "application/pdf" });

beforeEach(() => {
    localStorage.clear(); api.postFormData.mockReset(); api.downloadBlob.mockReset();
    URL.createObjectURL = vi.fn(() => "blob:synthetic"); URL.revokeObjectURL = vi.fn();
});
afterEach(cleanup);

describe("batch usage events", () => {
    function setup(tool: string, files: File[]) {
        const { container } = render(<BatchPage />);
        fireEvent.click(within(container.querySelector(".pt-batch-tool-picker") as HTMLElement).getByRole("button", { name: /Change tool/ }));
        fireEvent.change(screen.getByPlaceholderText(/Filter .* batchable tools/), { target: { value: tool } });
        fireEvent.click(screen.getByRole("button", { name: tool }));
        fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files } });
        return container;
    }
    it("emits one batch run with the tool slug and counts when the run finishes", async () => {
        const seen = listen();
        api.postFormData.mockResolvedValueOnce(ok()).mockRejectedValueOnce(httpError(422));
        setup("PNG to WebP", [new File(["png"], "secret-a.png", { type: "image/png" }), new File(["png"], "secret-b.png", { type: "image/png" })]);
        fireEvent.click(screen.getByRole("button", { name: "Process 2" }));
        await waitFor(() => expect(seen).toHaveLength(1));
        expect(seen).toEqual([{ slug: "png-to-webp", mode: "batch", outcome: "partial", files: 2, errorKind: "bad_input" }]);
        expect(JSON.stringify(seen)).not.toContain("secret");
    });
});

describe("pipeline usage events", () => {
    function run(container: HTMLElement) {
        const header = within(container.querySelector(".pt-workflow-header") as HTMLElement);
        fireEvent.click(container.querySelector(".pt-pipeline-recipe") as HTMLButtonElement);
        fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, { target: { files: [original] } });
        fireEvent.click(header.getByRole("button", { name: "Run pipeline" }));
    }
    it("emits one pipeline run per step when the server chain succeeds", async () => {
        const seen = listen();
        api.postFormData.mockResolvedValue(ok());
        const { container } = render(<PipelinePage />);
        run(container);
        await waitFor(() => expect(api.downloadBlob).toHaveBeenCalledOnce());
        const steps = JSON.parse(localStorage.getItem("privatools_pipeline_draft") || "[]") as string[];
        expect(steps.length).toBeGreaterThan(0);
        expect(seen).toEqual(steps.map(slug => ({ slug, mode: "pipeline", outcome: "success", files: 1 })));
        expect(JSON.stringify(seen)).not.toContain("Secret");
    });
    it("reports the failing step as an error when the per-step fallback breaks", async () => {
        const seen = listen();
        // The whole-chain call fails, the first per-step call succeeds, the second fails.
        api.postFormData.mockRejectedValueOnce(new Error("chain unavailable")).mockResolvedValueOnce(ok()).mockRejectedValueOnce(httpError(504));
        const { container } = render(<PipelinePage />);
        run(container);
        await waitFor(() => expect(seen.length).toBeGreaterThanOrEqual(2));
        const steps = JSON.parse(localStorage.getItem("privatools_pipeline_draft") || "[]") as string[];
        expect(seen).toEqual([
            { slug: steps[0], mode: "pipeline", outcome: "success", files: 1 },
            { slug: steps[1], mode: "pipeline", outcome: "error", files: 1, errorKind: "timeout" },
        ]);
        expect(JSON.stringify(seen)).not.toContain("secret");
    });
});
