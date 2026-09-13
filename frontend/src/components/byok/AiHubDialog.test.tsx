import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AiHubContent } from "./AiHubDialog";

const mocks = vi.hoisted(() => ({ cached: vi.fn(), remove: vi.fn(), download: vi.fn() }));
vi.mock("@/lib/localModels", () => ({
    LOCAL_MODELS: [{ id: "summary", hfId: "test/summary", label: "Test summarizer", powers: "Summarize PDF", approxLabel: "20 MB", predownload: mocks.download }],
    TRANSLATE_HF_PREFIX: "test/translate-", listCachedModels: mocks.cached, removeCachedModel: mocks.remove, formatBytes: (n: number) => `${n} bytes`,
}));
vi.mock("@/hooks/useByok", () => ({ useByok: () => ({ configured: [], provider: "", ready: false }) }));
vi.mock("./ByokPanel", () => ({ ByokPanel: () => <div>Provider configuration</div> }));

beforeEach(() => { mocks.cached.mockReset().mockResolvedValue([]); mocks.remove.mockReset().mockResolvedValue(undefined); mocks.download.mockReset(); });

async function models() {
    render(<AiHubContent />);
    await userEvent.setup().click(screen.getByRole("tab", { name: "On-device models" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Download" })).toBeInTheDocument());
}

describe("shared AI model management", () => {
    it("uses actual download progress and refreshes installed cache after completion", async () => {
        let finish: () => void;
        mocks.download.mockImplementation((onProgress: (n: number) => void) => { onProgress(37); return new Promise<void>(resolve => { finish = resolve; }); });
        await models();
        fireEvent.click(screen.getByRole("button", { name: "Download" }));
        expect(await screen.findByRole("progressbar", { name: "Downloading Test summarizer" })).toHaveAttribute("value", "37");
        mocks.cached.mockResolvedValue([{ hfId: "test/summary", bytes: 20000000 }]);
        await act(async () => finish!());
        expect(await screen.findByRole("button", { name: "Remove Test summarizer from this browser" })).toBeInTheDocument();
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });

    it("shows download failure without claiming a model is installed", async () => {
        mocks.download.mockRejectedValue(new Error("Network unavailable"));
        await models();
        fireEvent.click(screen.getByRole("button", { name: "Download" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Network unavailable");
        expect(screen.queryByRole("button", { name: /Remove Test summarizer/ })).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Download" })).toBeEnabled();
    });

    it("handles cache removal failures without removing the model from the UI", async () => {
        mocks.cached.mockResolvedValue([{ hfId: "test/summary", bytes: 20000000 }]);
        mocks.remove.mockRejectedValue(new Error("Storage blocked"));
        render(<AiHubContent />);
        await userEvent.setup().click(screen.getByRole("tab", { name: "On-device models" }));
        fireEvent.click(await screen.findByRole("button", { name: "Remove Test summarizer from this browser" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Could not remove that model");
        expect(screen.getByRole("button", { name: "Remove Test summarizer from this browser" })).toBeEnabled();
    });
});
