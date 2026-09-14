import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AccountPage from "./AccountPage";

const api = vi.hoisted(() => ({ me: vi.fn(), listKeys: vi.fn(), createKey: vi.fn(), revokeKey: vi.fn(), logout: vi.fn(), deleteAccount: vi.fn() }));
vi.mock("@/skins/accountLogic", async importOriginal => ({ ...await importOriginal<typeof import("@/skins/accountLogic")>(), accountApi: api }));
vi.mock("@/components/account/SocialSignIn", () => ({ SocialSignIn: () => null }));
vi.mock("@/components/account/ApiActivity", () => ({ default: () => <section aria-label="API activity" /> }));

const record = { key_id: "test_key_id", label: "Sample workflow", created_at: "2026-09-14", last_used_at: null, revoked: false };
beforeEach(() => {
    vi.clearAllMocks();
    api.me.mockResolvedValue({ user: { id: "owner", email: "person@example.test", created_at: "2026-09-14" } });
    api.listKeys.mockResolvedValue({ keys: [record] });
    api.createKey.mockResolvedValue({ key: "synthetic-test-key", record: { ...record, key_id: "new_key", label: "Key 2" } });
    api.revokeKey.mockResolvedValue({ ok: true });
    api.logout.mockResolvedValue({ ok: true });
    api.deleteAccount.mockResolvedValue({ ok: true });
});

describe("fallback account workspace", () => {
    it("exposes the shared account navigation after sign-in", async () => {
        render(<AccountPage />);
        expect(await screen.findByRole("heading", { name: "API access", level: 1 })).toBeInTheDocument();
        const nav = within(screen.getByRole("navigation", { name: "Account sections" }));
        expect(nav.getByRole("link", { name: "Settings & security" })).toHaveAttribute("href", "/account/settings");
        expect(nav.getByRole("link", { name: "API keys & usage" })).toHaveAttribute("aria-current", "page");
        expect(screen.getByText("person@example.test")).toBeInTheDocument();
    });

    it("keeps key creation and the one-time key warning available", async () => {
        render(<AccountPage />);
        await screen.findByText(record.label);
        fireEvent.click(screen.getByRole("button", { name: "Create key" }));
        expect(await screen.findByText("synthetic-test-key")).toBeInTheDocument();
        expect(screen.getByText("Copy this now — it is not shown again")).toBeInTheDocument();
        expect(api.createKey).toHaveBeenCalledExactlyOnceWith("Key 2");
    });

    it("preserves revocation and refreshes the displayed key state", async () => {
        render(<AccountPage />);
        await screen.findByText(record.label);
        api.listKeys.mockResolvedValue({ keys: [{ ...record, revoked: true }] });
        fireEvent.click(screen.getByRole("button", { name: `Revoke ${record.label}` }));
        await waitFor(() => expect(api.revokeKey).toHaveBeenCalledExactlyOnceWith(record.key_id));
        await waitFor(() => expect(screen.queryByRole("button", { name: `Revoke ${record.label}` })).not.toBeInTheDocument());
        expect(screen.getByText(/Revoked · created/)).toBeInTheDocument();
    });

    it("requires the existing second confirmation before deleting the account", async () => {
        render(<AccountPage />);
        fireEvent.click(await screen.findByRole("button", { name: "Delete account" }));
        expect(api.deleteAccount).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: "Press again to delete for good" }));
        await waitFor(() => expect(api.deleteAccount).toHaveBeenCalledOnce());
        await waitFor(() => expect(screen.queryByRole("navigation", { name: "Account sections" })).not.toBeInTheDocument());
    });
});
