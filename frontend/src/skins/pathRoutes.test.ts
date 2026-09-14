import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { canonicalPath } from "@/lib/navigation";
import { PATH_ROUTE_PREFIXES } from "./pathRoutes";

/** Public routes declared by the house router, including the root. */
function declaredRoutes(): string[] {
    const src = readFileSync(resolve(__dirname, "../App.tsx"), "utf-8");
    const found = [...src.matchAll(/<Route\s+path="([^"]*)"/g)].map((match) => match[1]);
    expect(found.length).toBeGreaterThan(10);
    return found.filter(path => path.startsWith("/"));
}

describe("public route registry", () => {
    it("supports clean navigation to every route App.tsx declares", () => {
        for (const route of declaredRoutes()) {
            const path = route.replace(/:[^/]+/g, "example");
            const expected = path === "/settings" ? "/account/settings" : path;
            expect(canonicalPath(path), route).toBe(expected);
            expect(canonicalPath("#" + path), `legacy ${route}`).toBe(expected);
        }
    });

    it("orders longer prefixes first", () => {
        const lengths = PATH_ROUTE_PREFIXES.map(prefix => prefix.length);
        expect(lengths).toEqual([...lengths].sort((a, b) => b - a));
        expect(PATH_ROUTE_PREFIXES.indexOf("/tools")).toBeLessThan(PATH_ROUTE_PREFIXES.indexOf("/tool"));
    });

    it("declines paths that only resemble a registered route", () => {
        for (const path of ["/toolshed", "/toolbox", "/about-us", "/unknown", "/api/private"]) {
            expect(canonicalPath(path)).toBeNull();
        }
    });
});
