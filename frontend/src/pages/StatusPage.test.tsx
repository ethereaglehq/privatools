import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import StatusPage from "./StatusPage";

const connection = vi.hoisted(() => ({ online: true }));
vi.mock("@/hooks/useOnline", () => ({ useOnline: () => connection.online }));

beforeEach(() => { connection.online = true; });
afterEach(() => { vi.unstubAllGlobals(); });

describe("live service status", () => {
    it("reports a failed health request honestly while preserving the browser connection signal", async () => {
        const fetcher = vi.fn().mockRejectedValue(new Error("Network unavailable"));
        vi.stubGlobal("fetch", fetcher);
        render(<StatusPage />);
        expect(await screen.findByRole("heading", { name: "Something needs a moment." })).toBeVisible();
        expect(screen.getByText("Unreachable", { exact: true })).toBeVisible();
        expect(screen.getByText("Online", { exact: true })).toBeVisible();
        expect(fetcher).toHaveBeenCalledWith(expect.stringContaining("/health"), expect.objectContaining({ cache: "no-store", signal: expect.any(AbortSignal) }));
        expect(screen.queryByText(/99\.9|Mumbai|the app is cached/i)).not.toBeInTheDocument();
    });

    it("ignores a superseded health result and aborts the active request when the page closes", async () => {
        const pending: { resolve: (value: { ok: boolean }) => void; signal: AbortSignal }[] = [];
        vi.stubGlobal("fetch", vi.fn((_url: string, options: RequestInit) => new Promise(resolve => pending.push({ resolve, signal: options.signal as AbortSignal }))));
        const view = render(<StatusPage />);
        connection.online = false;
        view.rerender(<StatusPage />);
        expect(pending).toHaveLength(2);
        expect(pending[0].signal.aborted).toBe(true);
        await act(async () => pending[0].resolve({ ok: true }));
        expect(screen.getByRole("heading", { name: "Taking a quick look…" })).toBeVisible();
        view.unmount();
        expect(pending[1].signal.aborted).toBe(true);
        await act(async () => pending[1].resolve({ ok: true }));
    });
});
