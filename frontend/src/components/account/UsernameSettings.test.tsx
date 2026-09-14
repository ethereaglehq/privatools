import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import UsernameSettings from "./UsernameSettings";

const mocks = vi.hoisted(() => ({ verify: vi.fn(), enabled: vi.fn(), clerkEnabled: vi.fn(), ready: vi.fn(), require: vi.fn() }));
vi.mock("@clerk/react", () => ({ useReverification: (callback: (action: () => Promise<void>) => Promise<void>) => (action: () => Promise<void>) => mocks.verify(() => callback(action)) }));
vi.mock("@/lib/auth-mode", () => ({ usernameAccountsEnabled: mocks.enabled }));
vi.mock("@/lib/clerk/instance", () => ({ isClerkEnabled: mocks.clerkEnabled, whenClerkReady: mocks.ready, requireClerk: mocks.require }));
let user: { id: string; username: string | null; update: ReturnType<typeof vi.fn> };
beforeEach(() => {
    vi.resetAllMocks();
    mocks.verify.mockImplementation(action => action());
    user = { id: "account-1", username: "old-name", update: vi.fn() };
    mocks.enabled.mockReturnValue(true); mocks.clerkEnabled.mockReturnValue(true);
    mocks.ready.mockResolvedValue({ user }); mocks.require.mockImplementation(() => ({ user }));
    user.update.mockImplementation(async ({ username }: { username: string | null }) => { user.username = username; return user; });
});

const input = () => screen.getByRole("textbox", { name: /Username/ });
async function show() {
    render(<UsernameSettings accountId="account-1" />);
    await screen.findByRole("textbox", { name: /Username/ });
}
function submit(name: string) {
    fireEvent.change(input(), { target: { value: name } });
    fireEvent.submit(screen.getByRole("button", { name: "Save username" }).closest("form")!);
}

describe("username settings", () => {
    it("hides the editor for local accounts and disabled username deployments", () => {
        mocks.clerkEnabled.mockReturnValue(false);
        const view = render(<UsernameSettings accountId="account-1" />);
        expect(view.container).toBeEmptyDOMElement(); expect(mocks.ready).not.toHaveBeenCalled();
        mocks.clerkEnabled.mockReturnValue(true); mocks.enabled.mockReturnValue(false);
        view.rerender(<UsernameSettings accountId="account-1" />);
        expect(view.container).toBeEmptyDOMElement(); expect(mocks.ready).not.toHaveBeenCalled();
    });

    it("loads the account username without changing it or checking availability", async () => {
        await show(); expect(input()).toHaveValue("old-name");
        expect(user.update).not.toHaveBeenCalled();
        expect(screen.getByRole("button", { name: "Save username" })).toBeDisabled();
    });

    it("saves through the actual user update contract after an explicit submission", async () => {
        await show(); submit("  new-name  ");
        expect(await screen.findByRole("status")).toHaveTextContent("Your username has been saved");
        expect(user.update).toHaveBeenCalledExactlyOnceWith({ username: "new-name" });
        expect(input()).toHaveValue("new-name");
    });

    it("preserves the entered draft and existing saved name when Clerk rejects a duplicate", async () => {
        user.update.mockRejectedValue({ errors: [{ code: "form_identifier_exists", longMessage: "Server reflected a private value" }] });
        await show(); submit("taken-name");
        expect(await screen.findByRole("alert")).toHaveTextContent("already taken");
        expect(input()).toHaveValue("taken-name"); expect(user.username).toBe("old-name");
        expect(screen.getByRole("button", { name: "Save username" })).toBeEnabled();
        expect(screen.queryByText("Your username has been saved.")).not.toBeInTheDocument();
    });

    it("does not clear the username while typing and sends null only on explicit submission", async () => {
        await show(); fireEvent.change(input(), { target: { value: "" } });
        expect(user.update).not.toHaveBeenCalled(); expect(user.username).toBe("old-name");
        fireEvent.submit(screen.getByRole("button", { name: "Save username" }).closest("form")!);
        expect(await screen.findByRole("status")).toHaveTextContent("Your username has been removed");
        expect(user.update).toHaveBeenCalledExactlyOnceWith({ username: null });
        expect(input()).toHaveValue("");
    });

    it("rejects a too-short username before sending it to the server", async () => {
        await show(); submit("abc");
        expect(await screen.findByRole("alert")).toHaveTextContent("between 4 and 64");
        expect(user.update).not.toHaveBeenCalled();
    });

    it("guards a changed SDK identity before mutating the account", async () => {
        await show(); user.id = "other-account"; submit("new-name");
        expect(await screen.findByRole("alert")).toHaveTextContent("Your sign-in has changed");
        expect(user.update).not.toHaveBeenCalled();
    });

    it("prevents duplicate submissions while saving", async () => {
        let finish!: () => void;
        user.update.mockImplementation(() => new Promise(resolve => { finish = () => resolve({ ...user, username: "new-name" }); }));
        await show(); submit("new-name");
        fireEvent.submit(screen.getByRole("button", { name: "Saving…" }).closest("form")!);
        expect(user.update).toHaveBeenCalledTimes(1);
        expect(input()).toBeDisabled();
        await act(async () => finish());
        await waitFor(() => expect(input()).toHaveValue("new-name"));
    });

    it("retries the submitted username after verification", async () => {
        user.update.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { return operation(); } });
        await show(); submit("verified-name");
        expect(await screen.findByRole("status")).toHaveTextContent("Your username has been saved");
        expect(user.update).toHaveBeenCalledTimes(2);
        expect(user.update).toHaveBeenNthCalledWith(2, { username: "verified-name" });
        expect(input()).toHaveValue("verified-name");
    });

    it("preserves the draft on verification cancellation without echoing server content", async () => {
        user.update.mockRejectedValue({ errors: [{ code: "session_reverification_required" }] });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { throw { code: "reverification_cancelled", message: "private response" }; } });
        await show(); submit("draft-name");
        expect(await screen.findByRole("alert")).toHaveTextContent("Verification was cancelled");
        expect(screen.getByRole("alert")).not.toHaveTextContent("private response");
        expect(input()).toHaveValue("draft-name");
        expect(user.update).toHaveBeenCalledTimes(1);
        expect(screen.getByRole("button", { name: "Save username" })).toBeEnabled();
    });

    it.each(["account change", "unmount"])("does not retry a username change after %s during verification", async reason => {
        user.update.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] });
        let verify!: () => void;
        const gate = new Promise<void>(resolve => { verify = resolve; });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { await gate; return operation(); } });
        const view = render(<UsernameSettings accountId="account-1" />);
        await screen.findByRole("textbox", { name: /Username/ });
        submit("new-name");
        await waitFor(() => expect(user.update).toHaveBeenCalledTimes(1));
        if (reason === "unmount") view.unmount();
        else user.id = "another-account";
        await act(async () => verify());
        expect(user.update).toHaveBeenCalledTimes(1);
        expect(screen.queryByText("Your username has been saved.")).not.toBeInTheDocument();
        if (reason === "account change") {
            expect(screen.getByRole("alert")).toHaveTextContent("Your sign-in has changed");
            expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
        }
    });

    it("does not reflect raw username failures in the UI", async () => {
        user.update.mockRejectedValue({ errors: [{ longMessage: "private server response" }] });
        await show(); submit("draft-name");
        expect(await screen.findByRole("alert")).toHaveTextContent("Your username could not be saved");
        expect(screen.getByRole("alert")).not.toHaveTextContent("private server response");
    });
});
