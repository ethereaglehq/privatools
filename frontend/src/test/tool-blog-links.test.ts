import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { blogPosts, postsForTool } from "@/data/blog";

// scripts/gen-llms.mjs writes src/data/tool-blog-links.json so a tool page can
// list its guides without downloading the blog module. The file is committed,
// so it can fall behind blog.ts. postsForTool(slug, 4) is the selection it
// replaced on the client and the one backend/app/seo_meta.py mirrors for
// crawlers, so it is the reference here.
const committed = () => JSON.parse(readFileSync(join(process.cwd(), "src/data/tool-blog-links.json"), "utf8"));

describe("generated tool → guide index", () => {
    it("matches postsForTool(slug, 4) for every tool a post mentions", () => {
        const mentioned = [...new Set(blogPosts.flatMap(post => post.relatedTools ?? []))];
        const expected = Object.fromEntries(mentioned.map(slug => [slug, postsForTool(slug, 4).map(post => ({ slug: post.slug, title: post.title }))]));
        // Sanity: the recomputation exercises the cap and real data, so an
        // empty blog registry cannot make this pass vacuously.
        expect(mentioned.length).toBeGreaterThan(10);
        expect(Object.values(expected).some(links => links.length === 4)).toBe(true);
        expect(committed(), "src/data/tool-blog-links.json is stale — run `npm run gen:llms` and commit the result").toEqual(expected);
    });
});
