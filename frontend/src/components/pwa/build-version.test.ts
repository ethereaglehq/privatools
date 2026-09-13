import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, expect, it } from "vitest";
import config from "../../../vite.config";
const temporary: string[] = [];
afterEach(() => temporary.splice(0).forEach((dir) => rmSync(dir, { recursive: true, force: true })));
it("gives changed built assets a new worker identity while keeping identical builds stable", () => {
    const plugin = (config as { plugins: { name: string }[] }).plugins.find((p) => p.name === "privatools-service-worker-version") as unknown as {
        configResolved: (config: { root: string; build: { outDir: string } }) => void;
        writeBundle: () => void;
    };
    const root = mkdtempSync(path.join(tmpdir(), "privatools-pwa-version-")); temporary.push(root);
    mkdirSync(path.join(root, "assets")); mkdirSync(path.join(root, "icons")); mkdirSync(path.join(root, "experience")); mkdirSync(path.join(root, "brand"));
    writeFileSync(path.join(root, "index.html"), '<script src="/assets/main-a.js"></script>');
    writeFileSync(path.join(root, "manifest.json"), "{}");
    for (const icon of ["icon-192.png", "icon-512.png", "icon-maskable-512.png"]) writeFileSync(path.join(root, "icons", icon), "icon");
    for (const image of ["air-mist.png", "air-graphite.png"]) writeFileSync(path.join(root, "experience", image), "artwork");
    const brandIcons = ["privatools-icon-96.png", "privatools-favicon.svg", "privatools-icon-180.png"];
    for (const icon of brandIcons) writeFileSync(path.join(root, "brand", icon), "brand icon");
    plugin.configResolved({ root, build: { outDir: "." } });
    const build = () => {
        writeFileSync(path.join(root, "sw.js"), 'const CACHE_VERSION = "v2.0.0";');
        plugin.writeBundle(); return readFileSync(path.join(root, "sw.js"), "utf8");
    };
    const first = build(); expect(first).toMatch(/v2\.[a-f0-9]{16}/); expect(build()).toBe(first);
    writeFileSync(path.join(root, "assets", "lazy-new-hash.js"), "new tool code");
    expect(build()).not.toBe(first);
    // Public favicon names remain stable; their bytes must still invalidate
    // the shell so an installed app can receive a refreshed identity.
    for (const icon of brandIcons) {
        const previous = build();
        writeFileSync(path.join(root, "brand", icon), "updated icon bytes");
        const next = build();
        expect(next).not.toBe(previous);
        expect(build()).toBe(next);
    }
});
