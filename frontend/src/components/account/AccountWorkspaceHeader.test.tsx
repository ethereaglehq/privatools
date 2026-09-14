import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AccountWorkspaceHeader from "./AccountWorkspaceHeader";

describe("account workspace navigation", () => {
    it.each(["settings", "api"] as const)("keeps both real account destinations visible on %s", active => {
        render(<AccountWorkspaceHeader active={active} email="person@example.test" title="Account settings" />);
        const nav = within(screen.getByRole("navigation", { name: "Account sections" }));
        const settings = nav.getByRole("link", { name: "Settings & security" });
        const api = nav.getByRole("link", { name: "API keys & usage" });
        expect(settings).toHaveAttribute("href", "/account/settings");
        expect(api).toHaveAttribute("href", "/account/keys");
        expect(active === "settings" ? settings : api).toHaveAttribute("aria-current", "page");
        expect(active === "settings" ? api : settings).not.toHaveAttribute("aria-current");
        expect(screen.getByText("person@example.test")).toBeInTheDocument();
    });

    it("preserves caller actions and embedded heading hierarchy", () => {
        const createKey = vi.fn();
        render(<AccountWorkspaceHeader active="api" email="person@example.test" title="API access" embedded actions={<button onClick={createKey}>Create key</button>} />);
        expect(screen.getByRole("heading", { name: "API access", level: 2 })).toBeInTheDocument();
        expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Create key" }));
        expect(createKey).toHaveBeenCalledOnce();
    });
});
