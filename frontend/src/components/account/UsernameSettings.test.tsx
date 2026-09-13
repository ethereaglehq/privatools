import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import UsernameSettings from "./UsernameSettings";

const mocks = vi.hoisted(() => ({ enabled: vi.fn(), clerkEnabled: vi.fn(), ready: vi.fn(), require: vi.fn() }));
vi.mock("@/lib/auth-mode", () => ({ usernameAccountsEnabled: mocks.enabled }));
vi.mock("@/lib/clerk/instance", () => ({ isClerkEnabled: mocks.clerkEnabled, whenClerkReady: mocks.ready, requireClerk: mocks.require }));
let user: { id: string; username: string | null; update: ReturnType<typeof vi.fn> };
beforeEach(() => {
    vi.resetAllMocks();
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
        user.update.mockRejectedValue({ errors: [{ longMessage: "That username is already taken. Choose another." }] });
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
});
