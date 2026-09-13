import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
const predownload = vi.hoisted(() => vi.fn());
vi.mock("@/lib/localModels", () => ({ LOCAL_MODELS: [{ id: 'bg', hfId: 'PrivaTools/u2netp', label:'Browser background model', approxLabel:'~4.4 MB', toolHref:'#/tools/remove-background', predownload }] }));
import { LocalModelBanner } from "./LocalModelBanner";
beforeEach(() => { predownload.mockReset(); });
it("does not download on opening a tool with another processing option", () => {
    render(<LocalModelBanner slug="remove-background"/>);
    expect(predownload).not.toHaveBeenCalled();
    expect(screen.getByText(/optional browser model/i)).toBeInTheDocument();
});
it("downloads only on request and describes browser readiness without claiming all work is local", async () => {
    predownload.mockImplementation(async (progress: (n:number)=>void) => progress(70));
    render(<LocalModelBanner slug="remove-background"/>);
    await act(async () => fireEvent.click(screen.getByRole('button', {name:'Download'})));
    expect(predownload).toHaveBeenCalledOnce();
    expect(screen.getByText('Browser model ready for this visit.')).toBeInTheDocument();
    expect(screen.getByText(/server and api-key modes have different data paths/i)).toBeInTheDocument();
});
it("allows retry after a failed model download", async () => {
    predownload.mockRejectedValueOnce(new Error('Network unavailable')).mockResolvedValueOnce(undefined);
    render(<LocalModelBanner slug="remove-background"/>);
    await act(async () => fireEvent.click(screen.getByRole('button', {name:'Download'})));
    expect(screen.getByText('Network unavailable')).toBeInTheDocument();
    await act(async () => fireEvent.click(screen.getByRole('button', {name:'Try again'})));
    expect(predownload).toHaveBeenCalledTimes(2);
});
