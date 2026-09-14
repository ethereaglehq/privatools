import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import ApiPage from "./ApiPage";

const identity = { key_id: "hash_1234", label: "Local test", created_at: "2026-09-13T12:00:00Z" };
const usage = { ...identity, units: { used: 15, limit: 500, remaining: 485 }, bytes: { used: 1048576, limit: 262144000 }, resets_at: "2026-09-14T00:00:00Z" };
const response = (body: unknown) => ({ ok: true, status: 200, json: async () => body });
const publicDocs = () => response({ schema_version: "1", operations: [], components: {}, limits: { daily_units: 500, daily_bytes: 262144000 }, unavailable_tools: [] });
afterEach(() => vi.unstubAllGlobals());

describe("API page credential checks", () => {
    it("sends a supplied key only in headers and renders actual usage", async () => {
        const fetchMock = vi.fn().mockImplementation(async (path: string) => path.endsWith("/operations") ? publicDocs() : response(path.endsWith("/usage") ? usage : identity));
        vi.stubGlobal("fetch", fetchMock);
        const stored = vi.spyOn(Storage.prototype, "setItem");
        render(<ApiPage />);
        const user = userEvent.setup();
        await user.type(screen.getByLabelText("PrivaTools API key"), "pk_TEST_SECRET");
        await user.click(screen.getByRole("button", { name: "Check key & usage" }));
        expect(await screen.findByText("Key verified: Local test")).toBeInTheDocument();
        expect(screen.getByText("15 / 500")).toBeInTheDocument();
        const credentialCalls = fetchMock.mock.calls.filter(([url]) => !url.endsWith("/operations"));
        expect(credentialCalls).toHaveLength(2);
        for (const [url, options] of credentialCalls) {
            expect(url).not.toContain("pk_TEST_SECRET");
            expect(options.headers["X-API-Key"]).toBe("pk_TEST_SECRET");
            expect(options.cache).toBe("no-store");
        }
        expect(stored).not.toHaveBeenCalled();
        stored.mockRestore();
        await user.click(screen.getByRole("button", { name: "Clear key" }));
        expect(screen.getByLabelText("PrivaTools API key")).toHaveValue("");
        expect(screen.queryByText("Key verified: Local test")).not.toBeInTheDocument();
    });

    it("rejects failed key checks without a success state", async () => {
        vi.stubGlobal("fetch", vi.fn().mockImplementation(async (path: string) => path.endsWith("/operations") ? publicDocs() : { ok: false, status: 401 }));
        render(<ApiPage />);
        fireEvent.change(screen.getByLabelText("PrivaTools API key"), { target: { value: "pk_INVALID" } });
        fireEvent.click(screen.getByRole("button", { name: "Check key & usage" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("not recognised or has been revoked");
        expect(screen.queryByText(/Key verified:/)).not.toBeInTheDocument();
    });

    it("cannot repopulate old results after clearing during a request", async () => {
        const finish: ((value: unknown) => void)[] = [];
        vi.stubGlobal("fetch", vi.fn().mockImplementation((path: string) => path.endsWith("/operations") ? Promise.resolve(publicDocs()) : new Promise(resolve => finish.push(resolve))));
        render(<ApiPage />);
        fireEvent.change(screen.getByLabelText("PrivaTools API key"), { target: { value: "pk_OLD" } });
        fireEvent.click(screen.getByRole("button", { name: "Check key & usage" }));
        await waitFor(() => expect(finish).toHaveLength(2));
        fireEvent.click(screen.getByRole("button", { name: "Clear key" }));
        await act(async () => { finish[0](response(identity)); finish[1](response(usage)); });
        expect(screen.queryByText(/Key verified:/)).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Check key & usage" })).toBeDisabled();
    });

    it("shows an unexpected response as an error rather than inventing usage", async () => {
        vi.stubGlobal("fetch", vi.fn().mockImplementation(async (path: string) => path.endsWith("/operations") ? publicDocs() : response({ ok: true })));
        render(<ApiPage />);
        fireEvent.change(screen.getByLabelText("PrivaTools API key"), { target: { value: "pk_TEST" } });
        fireEvent.click(screen.getByRole("button", { name: "Check key & usage" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("unexpected response");
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });
});
