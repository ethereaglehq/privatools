import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ApiActivity from "./ApiActivity";
import { apiActivitySchema } from "@/lib/api-activity";

const mocks = vi.hoisted(() => ({ apiActivity: vi.fn() }));
vi.mock("@/skins/accountLogic", () => ({ accountApi: mocks }));
const key = (id: string) => ({ key_id: id, label: `Workflow ${id}`, revoked: false, units: { used: 2, limit: 500, remaining: 498 }, bytes: { used: 1024, limit: 262144000 } });
const activity = () => ({ retention_days: 7, recent_limit: 50, resets_at: "2026-09-15T00:00:00Z", keys: [key("a"), key("b")], days: [{ date: "2026-09-14", requests: 3, succeeded: 2, failed: 1, avg_duration_ms: 250 }], recent: [{ request_id: "request-123", key_id: "a", operation: "v1_post_jobs", method: "POST", status_code: 202, error_code: null, duration_ms: 125, created_at: "2026-09-14T12:00:00Z" }] });
beforeEach(() => { mocks.apiActivity.mockReset(); mocks.apiActivity.mockResolvedValue(activity()); });

describe("account API activity", () => {
    it("accepts the backend's full historical key list", () => {
        expect(apiActivitySchema.safeParse({ ...activity(), keys: Array.from({ length: 1001 }, (_, i) => key(String(i))) }).success).toBe(true);
    });

    it("refreshes all key choices when the managed key list changes", async () => {
        const { rerender } = render(<ApiActivity accountId="owner" keyVersion="initial" />);
        await screen.findByText("request-123");
        fireEvent.change(screen.getByLabelText("Activity for"), { target: { value: "a" } });
        await waitFor(() => expect(mocks.apiActivity).toHaveBeenLastCalledWith("a", expect.any(AbortSignal)));
        mocks.apiActivity.mockResolvedValue({ ...activity(), keys: [key("a"), key("b"), key("c")] });
        rerender(<ApiActivity accountId="owner" keyVersion="new-key" />);
        expect(await screen.findByRole("option", { name: "Workflow c" })).toBeInTheDocument();
        expect(screen.getByLabelText("Activity for")).toHaveValue("");
    });

    it("shows quota by key and distinguishes accepted jobs from completed processing", async () => {
        render(<ApiActivity accountId="owner" />);
        expect(await screen.findByText("request-123")).toBeInTheDocument();
        expect(screen.getByText("202 · Accepted")).toBeInTheDocument();
        expect(screen.getByText(/not completed conversions/i)).toBeInTheDocument();
        expect(screen.getAllByText("2 / 500 units")).toHaveLength(2);
        expect(screen.getByRole("table", { name: "Daily API requests in UTC" })).toHaveTextContent("2026-09-14");
        expect(mocks.apiActivity).toHaveBeenCalledWith(undefined, expect.any(AbortSignal));
    });

    it("filters using account authentication and keeps all key choices", async () => {
        render(<ApiActivity accountId="owner" />);
        await screen.findByText("request-123");
        mocks.apiActivity.mockResolvedValue({ ...activity(), keys: [key("a")] });
        fireEvent.change(screen.getByLabelText("Activity for"), { target: { value: "a" } });
        await waitFor(() => expect(mocks.apiActivity).toHaveBeenLastCalledWith("a", expect.any(AbortSignal)));
        expect(await screen.findByRole("option", { name: "Workflow b" })).toBeInTheDocument();
    });

    it("does not show the previous account's history while a new account loads", async () => {
        const { rerender } = render(<ApiActivity accountId="one" />);
        await screen.findByText("request-123");
        mocks.apiActivity.mockImplementation(() => new Promise(() => {}));
        rerender(<ApiActivity accountId="two" />);
        expect(screen.queryByText("request-123")).not.toBeInTheDocument();
        expect(screen.queryByRole("option", { name: "Workflow a" })).not.toBeInTheDocument();
    });

    it("ignores a late response after changing the account", async () => {
        let resolveOld!: (value: unknown) => void;
        mocks.apiActivity.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }));
        const { rerender } = render(<ApiActivity accountId="one" />);
        mocks.apiActivity.mockResolvedValue({ ...activity(), keys: [], recent: [], days: [] });
        rerender(<ApiActivity accountId="two" />);
        await screen.findByText("Create a key to start tracking API usage.");
        await act(async () => { resolveOld(activity()); });
        expect(screen.queryByText("request-123")).not.toBeInTheDocument();
    });

    it("uses a safe error and offers refresh without echoing a server error", async () => {
        mocks.apiActivity.mockRejectedValue(new Error("secret raw response"));
        render(<ApiActivity accountId="owner" />);
        expect(await screen.findByRole("alert")).toHaveTextContent("could not be loaded");
        expect(screen.queryByText(/secret raw/)).not.toBeInTheDocument();
        mocks.apiActivity.mockResolvedValue(activity());
        fireEvent.click(screen.getByRole("button", { name: "Refresh activity" }));
        expect(await screen.findByText("request-123")).toBeInTheDocument();
    });

    it("rejects invalid response numbers instead of displaying a broken dashboard", async () => {
        mocks.apiActivity.mockResolvedValue({ ...activity(), days: [{ ...activity().days[0], requests: -1 }] });
        render(<ApiActivity accountId="owner" />);
        expect(await screen.findByRole("alert")).toHaveTextContent("could not be loaded");
        expect(screen.queryByText("request-123")).not.toBeInTheDocument();
    });

    it("aborts in-flight history reads on unmount", () => {
        mocks.apiActivity.mockImplementation(() => new Promise(() => {}));
        const { unmount } = render(<ApiActivity accountId="owner" />);
        const signal = mocks.apiActivity.mock.calls[0][1];
        unmount();
        expect(signal.aborted).toBe(true);
    });
});
