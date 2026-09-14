import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AccountSettingsPage from "./AccountSettingsPage";
import { AccountSecurityError } from "@/lib/clerk/securityActions";

const mocks = vi.hoisted(() => ({ verify: vi.fn(), changePassword: vi.fn(), me: vi.fn(), clerkEnabled: vi.fn() }));
vi.mock("@clerk/react", () => ({ useReverification: (callback: (action: () => Promise<void>) => Promise<void>) => (action: () => Promise<void>) => mocks.verify(() => callback(action)) }));
vi.mock("@/skins/accountLogic", () => ({ accountApi: mocks, MIN_PASSWORD_LENGTH: 10 }));
vi.mock("@/lib/clerk/instance", () => ({ isClerkEnabled: mocks.clerkEnabled, whenClerkReady: vi.fn(), requireClerk: vi.fn() }));
vi.mock("@/lib/auth-mode", () => ({ usernameAccountsEnabled: () => false, passkeyAccountsEnabled: () => false }));
const accountUser = { id: "test-user", email: "test@example.test", created_at: "2026-09-13" };
beforeEach(() => { mocks.verify.mockReset(); mocks.verify.mockImplementation(action => action()); mocks.changePassword.mockReset(); mocks.me.mockReset(); mocks.clerkEnabled.mockReturnValue(false); });

function fill(next = "a longer new passphrase", confirmation = next) {
    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "a previous passphrase" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: next } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: confirmation } });
    fireEvent.submit(screen.getByRole("button", { name: "Update password" }).closest("form")!);
}

describe("account settings password flow", () => {
    it("creates a password inline for a hosted passwordless account", async () => {
        mocks.clerkEnabled.mockReturnValue(true);
        mocks.changePassword.mockResolvedValue({ ok: true });
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: false }} appearanceArea={<button>Choose Air</button>} />);
        expect(screen.getByRole("heading", { name: "Create your password" })).toBeInTheDocument();
        expect(screen.queryByLabelText("Current password")).not.toBeInTheDocument();
        expect(screen.queryByRole("link", { name: /Set up a password by email/ })).not.toBeInTheDocument();
        expect(mocks.changePassword).not.toHaveBeenCalled();
        fireEvent.change(screen.getByLabelText("New password"), { target: { value: "a brand new passphrase" } });
        fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "a brand new passphrase" } });
        fireEvent.submit(screen.getByRole("button", { name: "Create password" }).closest("form")!);
        expect(await screen.findByRole("status")).toHaveTextContent("password has been created");
        expect(mocks.changePassword).toHaveBeenCalledExactlyOnceWith("", "a brand new passphrase", accountUser.id);
        expect(screen.getByLabelText("Current password")).toBeRequired();
        expect(screen.getByLabelText("New password")).toHaveValue("");
        expect(screen.getByRole("button", { name: "Choose Air" })).toBeInTheDocument();
    });

    it("keeps the current-password form for a hosted account with a password", () => {
        mocks.clerkEnabled.mockReturnValue(true);
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: true }} />);
        expect(screen.getByLabelText("Current password")).toBeRequired();
        expect(screen.queryByText("You sign in without a password")).not.toBeInTheDocument();
    });

    it("keeps password change unavailable to a signed-out visitor", () => {
        render(<AccountSettingsPage accountUser={null} appearanceArea={<button>Choose Air</button>} />);
        expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/account/sign-in?next=/account/settings");
        expect(screen.queryByText("A little housekeeping.")).not.toBeInTheDocument();
        expect(screen.queryByRole("heading", { name: "Change your password" })).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Choose Air" })).not.toBeInTheDocument();
        expect(screen.queryByLabelText("Current password")).not.toBeInTheDocument();
        expect(mocks.me).not.toHaveBeenCalled();
    });

    it("waits for verified account resolution before offering sign-in", () => {
        render(<AccountSettingsPage accountUser={null} accountChecking />);
        expect(screen.getByRole("status")).toHaveTextContent("Checking your account");
        expect(screen.queryByRole("link", { name: "Sign in" })).not.toBeInTheDocument();
        expect(screen.queryByLabelText("Current password")).not.toBeInTheDocument();
    });

    it("rejects a mismatched confirmation before sending credentials", async () => {
        render(<AccountSettingsPage accountUser={accountUser} />);
        fill(undefined, "a different passphrase");
        expect(await screen.findByRole("alert")).toHaveTextContent("do not match");
        expect(mocks.changePassword).not.toHaveBeenCalled();
    });

    it("updates the actual account API and clears credentials only after success", async () => {
        mocks.changePassword.mockResolvedValue({ ok: true });
        render(<AccountSettingsPage accountUser={accountUser} appearanceArea={<button>Choose Air</button>} />);
        fill();
        expect(await screen.findByRole("status")).toHaveTextContent("password has been updated");
        expect(mocks.changePassword).toHaveBeenCalledExactlyOnceWith("a previous passphrase", "a longer new passphrase");
        expect(screen.getByLabelText("Current password")).toHaveValue("");
        expect(screen.getByLabelText("New password")).toHaveValue("");
        expect(screen.getByRole("button", { name: "Choose Air" })).toBeInTheDocument();
    });

    it("does not report success or echo credential material after rejection", async () => {
        mocks.changePassword.mockRejectedValue(new Error("Server reflected a previous passphrase"));
        render(<AccountSettingsPage accountUser={accountUser} />);
        fill();
        expect(await screen.findByRole("alert")).toHaveTextContent("could not be changed");
        expect(screen.queryByText(/Server reflected/)).not.toBeInTheDocument();
        expect(screen.queryByText("Your password has been updated.")).not.toBeInTheDocument();
        expect(screen.getByLabelText("Current password")).toHaveValue("a previous passphrase");
    });

    it("requires the current password for local accounts even if profile metadata says passwordless", async () => {
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: false }} />);
        fireEvent.change(screen.getByLabelText("New password"), { target: { value: "a longer new passphrase" } });
        fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "a longer new passphrase" } });
        fireEvent.submit(screen.getByRole("button", { name: "Update password" }).closest("form")!);
        expect(await screen.findByRole("alert")).toHaveTextContent("Enter your current password");
        expect(mocks.changePassword).not.toHaveBeenCalled();
        expect(mocks.verify).not.toHaveBeenCalled();
    });

    it("retries a hosted password change only after identity verification", async () => {
        mocks.clerkEnabled.mockReturnValue(true);
        mocks.changePassword.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ ok: true });
        let verify!: () => void;
        const gate = new Promise<void>(resolve => { verify = resolve; });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { await gate; return operation(); } });
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: true }} />);
        fill();
        await waitFor(() => expect(mocks.changePassword).toHaveBeenCalledTimes(1));
        expect(screen.getByRole("button", { name: "Saving password…" })).toBeDisabled();
        expect(screen.queryByText("Your password has been updated.")).not.toBeInTheDocument();
        await act(async () => verify());
        expect(await screen.findByRole("status")).toHaveTextContent("password has been updated");
        expect(mocks.changePassword).toHaveBeenNthCalledWith(2, "a previous passphrase", "a longer new passphrase", accountUser.id);
    });

    it("keeps cancellation recoverable and does not expose the server error", async () => {
        mocks.clerkEnabled.mockReturnValue(true);
        mocks.changePassword.mockRejectedValue({ errors: [{ code: "session_reverification_required", message: "a previous passphrase" }] });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { throw { code: "reverification_cancelled", message: "a previous passphrase" }; } });
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: true }} />);
        fill();
        expect(await screen.findByRole("alert")).toHaveTextContent("Verification was cancelled");
        expect(screen.getByRole("alert")).not.toHaveTextContent("a previous passphrase");
        expect(mocks.changePassword).toHaveBeenCalledTimes(1);
        expect(screen.getByRole("button", { name: "Update password" })).toBeEnabled();
        mocks.verify.mockImplementation(operation => operation());
        mocks.changePassword.mockResolvedValue({ ok: true });
        fill();
        expect(await screen.findByRole("status")).toHaveTextContent("password has been updated");
    });

    it("does not retry credentials for a changed account after verification", async () => {
        mocks.clerkEnabled.mockReturnValue(true);
        mocks.changePassword.mockRejectedValueOnce({ errors: [{ code: "session_reverification_required" }] }).mockResolvedValue({ ok: true });
        let verify!: () => void;
        const gate = new Promise<void>(resolve => { verify = resolve; });
        mocks.verify.mockImplementation(async operation => { try { return await operation(); } catch { await gate; return operation(); } });
        const view = render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: true }} />);
        fill();
        await waitFor(() => expect(mocks.changePassword).toHaveBeenCalledTimes(1));
        view.rerender(<AccountSettingsPage accountUser={{ ...accountUser, id: "other-account", email: "other@example.test", password_enabled: false }} />);
        await act(async () => verify());
        expect(mocks.changePassword).toHaveBeenCalledTimes(1);
        expect(screen.queryByText("Your password has been updated.")).not.toBeInTheDocument();
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
        expect(screen.getByLabelText("New password")).toHaveValue("");
        expect(screen.getByRole("button", { name: "Create password" })).toBeEnabled();
    });

    it("ignores a completed password update after the signed-in account changes", async () => {
        let finish!: () => void;
        mocks.changePassword.mockImplementation(() => new Promise(resolve => { finish = () => resolve({ ok: true }); }));
        const view = render(<AccountSettingsPage accountUser={accountUser} />);
        fill();
        view.rerender(<AccountSettingsPage accountUser={{ ...accountUser, id: "other-account", email: "other@example.test" }} />);
        await act(async () => finish());
        expect(screen.queryByText("Your password has been updated.")).not.toBeInTheDocument();
        expect(screen.getByLabelText("Current password")).toHaveValue("");
    });

    it("never treats an unresolved reverification hint as password success", async () => {
        mocks.clerkEnabled.mockReturnValue(true);
        mocks.verify.mockResolvedValue({ clerk_error: { type: "reverification" } });
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: true }} />);
        fill();
        expect(await screen.findByRole("alert")).toHaveTextContent("could not be verified");
        expect(screen.queryByText("Your password has been updated.")).not.toBeInTheDocument();
    });

    it("clears credentials and stops submission if the SDK identity differs from the page", async () => {
        mocks.clerkEnabled.mockReturnValue(true);
        mocks.changePassword.mockRejectedValue(new AccountSecurityError("account_changed"));
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: true }} />);
        fill();
        expect(await screen.findByRole("alert")).toHaveTextContent("Your sign-in has changed");
        expect(screen.getByLabelText("Current password")).toHaveValue("");
        expect(screen.getByLabelText("New password")).toHaveValue("");
        expect(screen.getByRole("button", { name: "Update password" })).toBeDisabled();
    });
});
