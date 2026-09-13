import { describe, expect, it } from "vitest";
import { parseHash } from "./SkinApp";

/**
 * Daylight routes on the hashes withPathRoutes produces from real site paths,
 * so this parser IS the skin's URL contract. Site-shaped inputs first.
 */
describe("daylight route parser", () => {
    it("maps the site's own URL shapes", () => {
        expect(parseHash("#/tool/merge-pdf")).toEqual({ view: "tool", slug: "merge-pdf" });
        expect(parseHash("#/tools/image-compressor")).toEqual({ view: "tool", slug: "image-compressor" });
        expect(parseHash("#/tools")).toEqual({ view: "tools", cat: "" });
        expect(parseHash("#/tools?cat=image")).toEqual({ view: "tools", cat: "image" });
        expect(parseHash("#/my-stuff")).toEqual({ view: "mystuff" });
        expect(parseHash("#/my-stuff/vault")).toEqual({ view: "vault" });
        expect(parseHash("#/account")).toEqual({ view: "account", keys: false });
        expect(parseHash("#/account/keys")).toEqual({ view: "account", keys: true });
        expect(parseHash("#/blog")).toEqual({ view: "blog", post: "" });
        expect(parseHash("#/blog/some-post")).toEqual({ view: "blog", post: "some-post" });
        expect(parseHash("#/security")).toEqual({ view: "security" });
        expect(parseHash("#/compare/ilovepdf")).toEqual({ view: "compare", competitor: "ilovepdf" });
        expect(parseHash("#/compare")).toEqual({ view: "compare", competitor: "" });
        for (const p of ["pipeline", "batch", "about", "privacy", "terms", "status", "support"]) {
            expect(parseHash(`#/${p}`)).toEqual({ view: p });
        }
    });

    it("opens dedicated trust, AI, API, and account surfaces", () => {
        for (const view of ["trust", "ai", "api", "settings"]) expect(parseHash(`#/${view}`)).toEqual({ view });
        expect(parseHash("#/account/settings")).toEqual({ view: "settings" });
        expect(parseHash("#/account/sign-in")).toEqual({ view: "account", keys: false, authMode: "signin" });
        expect(parseHash("#/account/sign-up")).toEqual({ view: "account", keys: false, authMode: "signup" });
    });

    it("falls back to home for the empty route, never to a crash", () => {
        expect(parseHash("")).toEqual({ view: "home" });
        expect(parseHash("#/")).toEqual({ view: "home" });
    });

    it("treats an unknown route as a 404, not a silent homepage", () => {
        expect(parseHash("#/nonsense")).toEqual({ view: "notfound" });
        expect(parseHash("#/tool-not-a-real-prefix/x")).toEqual({ view: "notfound" });
        expect(parseHash("#/tool/")).toEqual({ view: "tools", cat: "" });
    });

    it("trailing slashes don't change the route", () => {
        expect(parseHash("#/tools/")).toEqual({ view: "tools", cat: "" });
        expect(parseHash("#/my-stuff/vault/")).toEqual({ view: "vault" });
    });
});
