import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AccountPage from "./AccountPage";

const mocks = vi.hoisted(() => ({ me: vi.fn(), listKeys: vi.fn(), deleteAccount: vi.fn(), verify: vi.fn(), warning: vi.fn(), success: vi.fn() }));
vi.mock("@/skins/accountLogic", async original => ({ ...await original<object>(), accountApi: mocks }));
vi.mock("@/lib/clerk/instance", async original => ({ ...await original<object>(), isClerkEnabled: () => true }));
vi.mock("@clerk/react", () => ({ useReverification: (callback: (action: () => Promise<void>) => Promise<void>) => (action: () => Promise<void>) => mocks.verify(() => callback(action)) }));
vi.mock("sonner", () => ({ toast: { warning: mocks.warning, success: mocks.success } }));
vi.mock("@/components/account/ApiActivity", () => ({ default: () => null }));
vi.mock("@/components/account/SocialSignIn", () => ({ SocialSignIn: () => null }));
const user = { id: "original-account", email: "person@example.test", created_at: "2026-09-13" };
beforeEach(() => {
    vi.resetAllMocks();
    mocks.me.mockResolvedValue({ user }); mocks.listKeys.mockResolvedValue({ keys: [] });
    mocks.verify.mockImplementation(action => action());
});
async function show() {
    const view = render(<AccountPage />);
    await screen.findByRole("button", { name: "Delete account" });
    return view;
}
function confirm() {
    fireEvent.click(screen.getByRole("button", { name: "Delete account" }));
    fireEvent.click(screen.getByRole("button", { name: "Press again to delete for good" }));
}

describe("fallback account page deletion", () => {
    it("keeps the account after cancelled verification without showing raw errors", async () => {
        mocks.deleteAccount.mockRejectedValue({ errors: [{ code: "session_reverification_required" }] });
        mocks.verify.mockImplementation(async action => { try { return await action(); } catch { throw { code: "reverification_cancelled", message: "private response" }; } });
        await show(); confirm();
        expect(await screen.findByRole("alert")).toHaveTextContent("Verification was cancelled");
        expect(screen.getByRole("alert")).not.toHaveTextContent("private response");
        expect(screen.getByRole("button", { name: "Delete account" })).toBeEnabled();
        expect(mocks.deleteAccount).toHaveBeenCalledExactlyOnceWith(user.id);
    });

    it("shows a truthful cleanup warning after deletion without retrying it", async () => {
        mocks.deleteAccount.mockResolvedValue({ ok: true, cleanupPending: true });
        await show(); confirm();
        await waitFor(() => expect(mocks.warning).toHaveBeenCalledWith(expect.stringContaining("API data cleanup could not be confirmed"), { duration: 15_000 }));
        expect(screen.queryByRole("button", { name: "Delete account" })).not.toBeInTheDocument();
        expect(mocks.deleteAccount).toHaveBeenCalledTimes(1);
        expect(mocks.success).not.toHaveBeenCalled();
    });

    it("does not retry a pending verification after the page unmounts", async () => {
        mocks.deleteAccount.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ ok: true });
        let verify!: () => void;
        const gate = new Promise<void>(resolve => { verify = resolve; });
        mocks.verify.mockImplementation(async action => { try { return await action(); } catch { await gate; return action(); } });
        const view = await show(); confirm();
        await waitFor(() => expect(mocks.deleteAccount).toHaveBeenCalledTimes(1));
        view.unmount(); await act(async () => verify());
        expect(mocks.deleteAccount).toHaveBeenCalledTimes(1);
        expect(mocks.warning).not.toHaveBeenCalled(); expect(mocks.success).not.toHaveBeenCalled();
    });
});
