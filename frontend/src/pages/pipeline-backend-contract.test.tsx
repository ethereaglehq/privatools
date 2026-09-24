import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import PipelinePage from "./PipelinePage";

const api = vi.hoisted(() => ({ postFormData: vi.fn(), downloadBlob: vi.fn() }));
vi.mock("@/lib/api", async (load) => ({ ...await load<typeof import("@/lib/api")>(), ...api }));

const original = new File(["%PDF-1.4\noriginal"], "report.pdf", { type: "application/pdf" });
function ok() { return { blob: async () => new Blob(["%PDF-1.4\nstep output"], { type: "application/pdf" }), headers: new Headers() } as Response; }
/** Each request's endpoint and the fields its file parts were sent under. */
function requests() {
    return api.postFormData.mock.calls.map(([endpoint, body]) => {
        const form: FormData = typeof body === "function" ? body() : body;
        return [endpoint, [...form.entries()].filter(([, value]) => value instanceof File).map(([field]) => field)];
    });
}

beforeEach(() => {
    localStorage.clear(); api.postFormData.mockReset(); api.downloadBlob.mockReset();
    URL.createObjectURL = vi.fn(() => "blob:synthetic"); URL.revokeObjectURL = vi.fn();
});
afterEach(cleanup);

describe("pipeline requests", () => {
    it("sends the document once per step, under the field each step's route reads", async () => {
        // The one-request chain fails, so each step uploads the document on its own.
        api.postFormData.mockRejectedValueOnce(new Error("chain unavailable")).mockResolvedValue(ok());
        const { container } = render(<PipelinePage />);
        fireEvent.click(within(container).getByRole("button", { name: /Brand & ship/ }));
        fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, { target: { files: [original] } });
        fireEvent.click(within(container.querySelector(".pt-workflow-header") as HTMLElement).getByRole("button", { name: "Run pipeline" }));
        await waitFor(() => expect(api.downloadBlob).toHaveBeenCalledOnce());

        // /stamp-pdf and /page-numbers read `file`; /compress reads `files: list[UploadFile]`.
        expect(requests()).toEqual([
            ["/pipeline", ["file"]],
            ["/stamp-pdf", ["file"]],
            ["/page-numbers", ["file"]],
            ["/compress", ["files"]],
        ]);
    });
});
