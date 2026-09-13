import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AccountSettingsPage from "./AccountSettingsPage";

const mocks = vi.hoisted(() => ({ changePassword: vi.fn(), me: vi.fn(), clerkEnabled: vi.fn() }));
vi.mock("@/skins/accountLogic", () => ({ accountApi: mocks, MIN_PASSWORD_LENGTH: 10 }));
vi.mock("@/lib/clerk/instance", () => ({ isClerkEnabled: mocks.clerkEnabled, whenClerkReady: vi.fn(), requireClerk: vi.fn() }));
vi.mock("@/lib/auth-mode", () => ({ usernameAccountsEnabled: () => false, passkeyAccountsEnabled: () => false }));
const accountUser = { id: "test-user", email: "test@example.test", created_at: "2026-09-13" };
beforeEach(() => { mocks.changePassword.mockReset(); mocks.me.mockReset(); mocks.clerkEnabled.mockReturnValue(false); });

function fill(next = "a longer new passphrase", confirmation = next) {
    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "a previous passphrase" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: next } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: confirmation } });
    fireEvent.submit(screen.getByRole("button", { name: "Update password" }).closest("form")!);
}

describe("account settings password flow", () => {
    it("offers email password setup without an impossible current-password form for a hosted social-only account", () => {
        mocks.clerkEnabled.mockReturnValue(true);
        render(<AccountSettingsPage accountUser={{ ...accountUser, password_enabled: false }} appearanceArea={<button>Choose Air</button>} />);
        expect(screen.getByRole("heading", { name: "You sign in without a password" })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Set up a password by email" })).toHaveAttribute("href", "/account?mode=recover");
        expect(screen.queryByLabelText("Current password")).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Update password" })).not.toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Choose Air" })).toBeInTheDocument();
        expect(mocks.changePassword).not.toHaveBeenCalled();
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
});
