import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PasskeySettings from "./PasskeySettings";

const mocks = vi.hoisted(() => ({ verify: vi.fn(), enabled: vi.fn(), supported: vi.fn(), ready: vi.fn(), require: vi.fn() }));
vi.mock("@clerk/react", () => ({ useReverification: (callback: (action: () => Promise<void>) => Promise<void>) => (action: () => Promise<void>) => mocks.verify(() => callback(action)) }));
vi.mock("@/lib/auth-mode", () => ({ passkeyAccountsEnabled: mocks.enabled }));
vi.mock("@/lib/clerk/instance", () => ({ whenClerkReady: mocks.ready, requireClerk: mocks.require }));
vi.mock("@/lib/clerk/accountApi", () => ({ passkeysSupported: mocks.supported, readablePasskeyError: (error: Error) => new Error(error.message || "Request failed.") }));

function savedPasskey(name = "Personal laptop", id = "key-1") {
    return { id, name, createdAt: new Date("2026-09-12T00:00:00Z"), lastUsedAt: null, update: vi.fn(), delete: vi.fn() };
}
type TestPasskey = ReturnType<typeof savedPasskey>;
let user: { id: string; passkeys: TestPasskey[]; reload: ReturnType<typeof vi.fn>; createPasskey: ReturnType<typeof vi.fn> };

beforeEach(() => {
    vi.resetAllMocks();
    mocks.verify.mockImplementation(action => action());
    user = { id: "account-1", passkeys: [], reload: vi.fn(), createPasskey: vi.fn() };
    user.reload.mockImplementation(async () => user);
    mocks.enabled.mockReturnValue(true);
    mocks.supported.mockReturnValue(true);
    mocks.ready.mockResolvedValue({ user });
    mocks.require.mockImplementation(() => ({ user }));
});

async function show() {
    const view = render(<PasskeySettings accountId="account-1" />);
    await waitFor(() => expect(screen.queryByText("Checking your account…")).not.toBeInTheDocument());
    return view;
}

describe("hosted passkey settings", () => {
    it("does not load hosted security or show controls when deployment passkeys are disabled", () => {
        mocks.enabled.mockReturnValue(false);
        const view = render(<PasskeySettings accountId="account-1" />);
        expect(view.container).toBeEmptyDOMElement();
        expect(mocks.ready).not.toHaveBeenCalled();
        expect(user.createPasskey).not.toHaveBeenCalled();
    });

    it("opens enrollment only after the explicit click, blocks duplicate prompts, and lists the created key", async () => {
        let complete!: (key: TestPasskey) => void;
        const created = savedPasskey("Phone", "key-phone");
        user.createPasskey.mockImplementation(() => new Promise<TestPasskey>(resolve => { complete = resolve; }));
        await show();
        expect(user.createPasskey).not.toHaveBeenCalled();
        const button = screen.getByRole("button", { name: "Add a passkey" });
        fireEvent.click(button); fireEvent.click(button);
        expect(user.createPasskey).toHaveBeenCalledTimes(1);
        expect(screen.getByRole("button", { name: /Follow your browser/ })).toBeDisabled();
        await act(async () => { user.passkeys = [created]; complete(created); });
        expect(await screen.findByText("Phone")).toBeInTheDocument();
        expect(screen.getByRole("status")).toHaveTextContent("Your passkey is ready");
        expect(user.reload).toHaveBeenCalledTimes(2);
    });

    it("makes browser cancellation recoverable without inventing a saved key", async () => {
        user.createPasskey.mockRejectedValue(new DOMException("User cancelled", "NotAllowedError"));
        await show(); fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("cancelled or timed out");
        expect(screen.getByRole("button", { name: "Add a passkey" })).toBeEnabled();
        expect(screen.queryByText(/Your passkey is ready/)).not.toBeInTheDocument();
        expect(screen.getByText("A simpler sign-in starts here.")).toBeInTheDocument();
    });

    it("keeps existing passkeys manageable when this browser cannot enroll", async () => {
        mocks.supported.mockReturnValue(false);
        const key = savedPasskey(); user.passkeys = [key];
        key.update.mockImplementation(async ({ name }: { name: string }) => { key.name = name; return key; });
        await show();
        expect(screen.getByRole("button", { name: "Add a passkey" })).toBeDisabled();
        expect(screen.getByText(/This browser cannot create passkeys here/)).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Rename Personal laptop" }));
        fireEvent.change(screen.getByLabelText("Passkey name"), { target: { value: "  Work laptop  " } });
        fireEvent.submit(screen.getByRole("button", { name: "Save name" }).closest("form")!);
        expect(await screen.findByText("Work laptop")).toBeInTheDocument();
        expect(key.update).toHaveBeenCalledExactlyOnceWith({ name: "Work laptop" });
        expect(user.createPasskey).not.toHaveBeenCalled();
    });

    it("requires confirmation before deleting the actual passkey resource", async () => {
        const key = savedPasskey(); user.passkeys = [key];
        key.delete.mockImplementation(async () => { user.passkeys = []; return { id: key.id }; });
        await show(); fireEvent.click(screen.getByRole("button", { name: "Remove Personal laptop" }));
        expect(key.delete).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: "Keep passkey" }));
        expect(key.delete).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: "Remove Personal laptop" }));
        fireEvent.click(screen.getByRole("button", { name: "Confirm removal" }));
        expect(await screen.findByRole("status")).toHaveTextContent("Passkey removed from your account");
        expect(key.delete).toHaveBeenCalledTimes(1);
        expect(screen.queryByRole("button", { name: "Rename Personal laptop" })).not.toBeInTheDocument();
    });

    it("retains the key and confirmation when deletion fails", async () => {
        const key = savedPasskey(); user.passkeys = [key]; key.delete.mockRejectedValue(new Error("Connection interrupted."));
        await show(); fireEvent.click(screen.getByRole("button", { name: "Remove Personal laptop" }));
        fireEvent.click(screen.getByRole("button", { name: "Confirm removal" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Passkeys could not be updated");
        expect(screen.getByRole("button", { name: "Confirm removal" })).toBeEnabled();
        expect(screen.getByRole("button", { name: "Rename Personal laptop" })).toBeInTheDocument();
    });

    it("preserves a successful enrollment when the subsequent list refresh fails", async () => {
        const key = savedPasskey();
        user.createPasskey.mockResolvedValue(key);
        await show(); user.reload.mockRejectedValue(new Error("Offline"));
        fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        expect(await screen.findByText("Personal laptop")).toBeInTheDocument();
        expect(screen.getByRole("status")).toHaveTextContent("Your passkey is ready");
        expect(screen.getByRole("status")).toHaveTextContent("list could not refresh");
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });

    it("does not mutate a different account if the SDK session changes", async () => {
        await show();
        user.id = "another-account";
        fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Your sign-in has changed");
        expect(user.createPasskey).not.toHaveBeenCalled();
    });

    it("offers refresh after an initial load failure", async () => {
        user.reload.mockRejectedValueOnce(new Error("Offline"));
        await show();
        expect(screen.getByRole("alert")).toHaveTextContent("Account security could not load");
        expect(screen.getByRole("button", { name: "Add a passkey" })).toBeDisabled();
        fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
        await waitFor(() => expect(screen.getByRole("button", { name: "Add a passkey" })).toBeEnabled());
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });

    it("asks for a fresh click after reverification before opening another enrollment prompt", async () => {
        const key = savedPasskey("Verified phone");
        user.createPasskey.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockImplementation(async () => { user.passkeys = [key]; return key; });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { return operation(); } });
        await show();
        fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        expect(user.createPasskey).toHaveBeenCalledTimes(1);
        expect(await screen.findByRole("status")).toHaveTextContent("Click Add a passkey again");
        expect(user.createPasskey).toHaveBeenCalledTimes(1);
        expect(screen.queryByText("Verified phone")).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        // The initial create call stays synchronous with this explicit click.
        expect(user.createPasskey).toHaveBeenCalledTimes(2);
        expect(await screen.findByText("Verified phone")).toBeInTheDocument();
        expect(screen.getByRole("status")).toHaveTextContent("Your passkey is ready");
    });

    it("allows a cancelled verification to be retried without claiming enrollment succeeded", async () => {
        user.createPasskey.mockRejectedValue({ errors: [{ code: "session_reverification_required" }] });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { throw { code: "reverification_cancelled", message: "private response" }; } });
        await show();
        fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Verification was cancelled");
        expect(screen.getByRole("alert")).not.toHaveTextContent("private response");
        expect(user.createPasskey).toHaveBeenCalledTimes(1);
        expect(screen.getByRole("button", { name: "Add a passkey" })).toBeEnabled();
        expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    it("retries the confirmed removal after verification and refreshes the actual list", async () => {
        const key = savedPasskey(); user.passkeys = [key];
        key.delete.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockImplementation(async () => { user.passkeys = []; });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { return operation(); } });
        await show();
        fireEvent.click(screen.getByRole("button", { name: "Remove Personal laptop" }));
        fireEvent.click(screen.getByRole("button", { name: "Confirm removal" }));
        expect(await screen.findByRole("status")).toHaveTextContent("Passkey removed from your account");
        expect(key.delete).toHaveBeenCalledTimes(2);
        expect(screen.queryByRole("button", { name: "Rename Personal laptop" })).not.toBeInTheDocument();
    });

    it.each(["account change", "unmount"])("does not resume a passkey mutation after %s during verification", async reason => {
        const key = savedPasskey(); user.passkeys = [key];
        key.update.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ ...key, name: "Work laptop" });
        let verify!: () => void;
        const gate = new Promise<void>(resolve => { verify = resolve; });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { await gate; return operation(); } });
        const view = await show();
        fireEvent.click(screen.getByRole("button", { name: "Rename Personal laptop" }));
        fireEvent.change(screen.getByLabelText("Passkey name"), { target: { value: "Work laptop" } });
        fireEvent.submit(screen.getByRole("button", { name: "Save name" }).closest("form")!);
        await waitFor(() => expect(key.update).toHaveBeenCalledTimes(1));
        if (reason === "unmount") view.unmount();
        else user.id = "another-account";
        await act(async () => verify());
        expect(key.update).toHaveBeenCalledTimes(1);
        expect(screen.queryByText("Passkey name updated.")).not.toBeInTheDocument();
        if (reason === "account change") {
            expect(screen.getByRole("alert")).toHaveTextContent("Your sign-in has changed");
            expect(screen.queryByRole("button", { name: "Rename Personal laptop" })).not.toBeInTheDocument();
        }
    });

    it("never renders passkey server errors verbatim", async () => {
        user.createPasskey.mockRejectedValue({ errors: [{ message: "private credential material", longMessage: "private credential material" }] });
        await show();
        fireEvent.click(screen.getByRole("button", { name: "Add a passkey" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Passkeys could not be updated");
        expect(screen.getByRole("alert")).not.toHaveTextContent("private credential material");
    });
});
