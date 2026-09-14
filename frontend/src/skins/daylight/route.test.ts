import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import DaylightSkinApp, { parseRoute } from "./SkinApp";

/**
 * The skin renders public paths and continues to understand old hash links.
 */
describe("daylight route parser", () => {
    it("reads clean public paths", () => {
        expect(parseRoute("/")).toEqual({ view: "home" });
        expect(parseRoute("/tools?cat=image")).toEqual({ view: "tools", cat: "image" });
        expect(parseRoute("/tool/merge-pdf")).toEqual({ view: "tool", slug: "merge-pdf" });
        expect(parseRoute("/tools/image-compressor")).toEqual({ view: "tool", slug: "image-compressor" });
        for (const view of ["pipeline", "batch", "ai"]) expect(parseRoute(`/${view}`)).toEqual({ view });
    });

    it("ignores ordinary page fragments and preserves the route query", () => {
        expect(parseRoute("/privacy#retention")).toEqual({ view: "privacy" });
        expect(parseRoute("/tools?cat=image#catalog")).toEqual({ view: "tools", cat: "image" });
        expect(parseRoute("/tools?cat=video%2Daudio&from=nav#catalog")).toEqual({ view: "tools", cat: "video-audio" });
        expect(parseRoute("/tool/merge-pdf#faq")).toEqual({ view: "tool", slug: "merge-pdf" });
        expect(parseRoute("/tools?cat=image?extra")).toEqual({ view: "tools", cat: "image?extra" });
    });

    it("maps the site's own URL shapes", () => {
        expect(parseRoute("#/tool/merge-pdf")).toEqual({ view: "tool", slug: "merge-pdf" });
        expect(parseRoute("#/tools/image-compressor")).toEqual({ view: "tool", slug: "image-compressor" });
        expect(parseRoute("#/tools")).toEqual({ view: "tools", cat: "" });
        expect(parseRoute("#/tools?cat=image")).toEqual({ view: "tools", cat: "image" });
        expect(parseRoute("#/my-stuff")).toEqual({ view: "mystuff" });
        expect(parseRoute("#/my-stuff/vault")).toEqual({ view: "vault" });
        expect(parseRoute("#/account")).toEqual({ view: "account", keys: false });
        expect(parseRoute("#/account/keys")).toEqual({ view: "account", keys: true });
        expect(parseRoute("#/blog")).toEqual({ view: "blog", post: "" });
        expect(parseRoute("#/blog/some-post")).toEqual({ view: "blog", post: "some-post" });
        expect(parseRoute("#/security")).toEqual({ view: "security" });
        expect(parseRoute("#/compare/ilovepdf")).toEqual({ view: "compare", competitor: "ilovepdf" });
        expect(parseRoute("#/compare")).toEqual({ view: "compare", competitor: "" });
        for (const p of ["pipeline", "batch", "about", "privacy", "terms", "status", "support"]) {
            expect(parseRoute(`#/${p}`)).toEqual({ view: p });
        }
    });

    it("opens dedicated trust, AI, API, and account surfaces", () => {
        for (const view of ["trust", "ai", "api", "settings"]) expect(parseRoute(`#/${view}`)).toEqual({ view });
        expect(parseRoute("#/account/settings")).toEqual({ view: "settings" });
        expect(parseRoute("#/account/sign-in")).toEqual({ view: "account", keys: false, authMode: "signin" });
        expect(parseRoute("#/account/sign-up")).toEqual({ view: "account", keys: false, authMode: "signup" });
    });

    it("falls back to home for the empty route, never to a crash", () => {
        expect(parseRoute("")).toEqual({ view: "home" });
        expect(parseRoute("#/")).toEqual({ view: "home" });
    });

    it("treats an unknown route as a 404, not a silent homepage", () => {
        expect(parseRoute("#/nonsense")).toEqual({ view: "notfound" });
        expect(parseRoute("#/tool-not-a-real-prefix/x")).toEqual({ view: "notfound" });
        expect(parseRoute("#/tool/")).toEqual({ view: "tools", cat: "" });
    });

    it("trailing slashes don't change the route", () => {
        expect(parseRoute("#/tools/")).toEqual({ view: "tools", cat: "" });
        expect(parseRoute("#/my-stuff/vault/")).toEqual({ view: "vault" });
    });
});

describe("shared pipeline navigation", () => {
    afterEach(() => {
        cleanup();
        window.history.replaceState(null, "", "/");
        localStorage.clear();
    });

    const pipelineUrl = (slug: string) => `/pipeline?p=${encodeURIComponent(window.btoa(JSON.stringify({ version: 1, steps: [slug] })))}`;

    it("loads a new shared pipeline when its query changes on the same page", async () => {
        window.history.replaceState(null, "", pipelineUrl("compress-pdf"));
        const shell = new DaylightSkinApp({});
        const page = render(shell.Pipeline());
        const canvas = await screen.findByRole("region", { name: "Workflow canvas" });
        expect(within(canvas).getByRole("heading", { name: "Compress PDF" })).toBeInTheDocument();

        window.history.replaceState(null, "", pipelineUrl("rotate-pdf"));
        page.rerender(shell.Pipeline());
        expect(await within(screen.getByRole("region", { name: "Workflow canvas" })).findByRole("heading", { name: "Rotate PDF" })).toBeInTheDocument();
    });

    it("keeps edits mounted when unrelated query parameters change", async () => {
        const shared = pipelineUrl("compress-pdf");
        window.history.replaceState(null, "", shared);
        const shell = new DaylightSkinApp({});
        const page = render(shell.Pipeline());
        const search = await screen.findByRole("textbox", { name: "Search pipeline tools" });
        fireEvent.change(search, { target: { value: "rotate" } });

        window.history.replaceState(null, "", shared + "&from=share");
        page.rerender(shell.Pipeline());
        expect(screen.getByRole("textbox", { name: "Search pipeline tools" })).toHaveValue("rotate");
    });
});
