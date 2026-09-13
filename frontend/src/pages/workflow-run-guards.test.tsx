import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import PipelinePage from "@/pages/PipelinePage";
import BatchPage from "@/pages/BatchPage";
const api = vi.hoisted(() => ({ postFormData: vi.fn(), downloadBlob: vi.fn() }));
vi.mock("@/lib/api", async (load) => ({ ...await load<typeof import("@/lib/api")>(), ...api }));
const original = new File(["%PDF-1.4\noriginal"], "Original.pdf", { type: "application/pdf" });
const replacement = new File(["%PDF-1.4\nreplacement"], "Replacement.pdf", { type: "application/pdf" });
beforeEach(() => {
    localStorage.clear(); api.postFormData.mockReset();
    api.postFormData.mockImplementation((_path, _body, options) => new Promise((_resolve, reject) => {
        options.signal.addEventListener("abort", () => reject(new DOMException("Cancelled", "AbortError")), { once: true });
    }));
});
afterEach(cleanup);
describe("active workflow protection", () => {
    it("reorders a recipe by dropping a step onto the next position and saves that order", () => {
        const { container } = render(<PipelinePage />);
        fireEvent.click(container.querySelector(".pt-pipeline-recipe") as HTMLButtonElement);
        const cards = container.querySelectorAll(".pt-pipeline-step");
        const initial = Array.from(cards, card => card.querySelector("h3")?.textContent);
        const dataTransfer = { setData: vi.fn(), effectAllowed: "move" };
        fireEvent.dragStart(cards[0], { dataTransfer });
        fireEvent.dragOver(cards[1], { dataTransfer });
        fireEvent.drop(cards[1], { dataTransfer });
        expect(Array.from(container.querySelectorAll(".pt-pipeline-step h3"), title => title.textContent)).toEqual([initial[1], initial[0]]);
        expect(JSON.parse(localStorage.getItem("privatools_pipeline_draft") || "[]")).toEqual(["strip-metadata", "compress-pdf"]);
    });

    it("freezes pipeline structure and its input while a server run is active, while keeping cancellation available", async () => {
        const { container } = render(<PipelinePage />);
        const header = within(container.querySelector(".pt-workflow-header") as HTMLElement);
        fireEvent.click(container.querySelector(".pt-pipeline-recipe") as HTMLButtonElement);
        const input = container.querySelector('input[type="file"]') as HTMLInputElement;
        fireEvent.change(input, { target: { files: [original] } });
        fireEvent.click(header.getByRole("button", { name: "Run pipeline" }));
        await waitFor(() => expect(api.postFormData).toHaveBeenCalledOnce());
        expect(input).toBeDisabled();
        expect(header.getByRole("button", { name: "Clear" })).toBeDisabled();
        expect(container.querySelectorAll(".pt-pipeline-recipe:not([disabled])")).toHaveLength(0);
        expect(container.querySelectorAll('.pt-palette-tool:not([disabled])')).toHaveLength(0);
        fireEvent.change(input, { target: { files: [replacement] } });
        expect(screen.queryByText("Replacement.pdf")).not.toBeInTheDocument();
        expect(screen.getByText("Original.pdf")).toBeInTheDocument();
        fireEvent.click(header.getByRole("button", { name: /Cancel/ }));
        await waitFor(() => expect(input).toBeEnabled());
        expect(header.getByRole("button", { name: "Run pipeline" })).toBeEnabled();
    }, 15000);
    it("keeps batch input, tool choice and queue clearing locked until cancellation finishes", async () => {
        const { container } = render(<BatchPage />);
        const header = within(container.querySelector(".pt-workflow-header") as HTMLElement);
        const input = container.querySelector('input[type="file"]') as HTMLInputElement;
        fireEvent.change(input, { target: { files: [original] } });
        fireEvent.click(header.getByRole("button", { name: "Process 1" }));
        await waitFor(() => expect(api.postFormData).toHaveBeenCalledOnce());
        expect(input).toBeDisabled();
        expect(header.getByRole("button", { name: "Clear" })).toBeDisabled();
        expect(within(container.querySelector(".pt-batch-tool-picker") as HTMLElement).getByRole("button", { name: /Change tool/ })).toBeDisabled();
        expect(container.querySelector(".pt-batch-dropzone")).toBeDisabled();
        fireEvent.change(input, { target: { files: [replacement] } });
        expect(screen.queryByText("Replacement.pdf")).not.toBeInTheDocument();
        expect(container.querySelectorAll('.pt-batch-file')).toHaveLength(1);
        fireEvent.click(header.getByRole("button", { name: /Cancel/ }));
        await waitFor(() => expect(input).toBeEnabled());
    }, 15000);
});
