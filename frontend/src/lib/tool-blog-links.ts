import { useEffect, useState } from "react";

/** A guide that names the tool in its relatedTools. */
export interface ToolBlogLink { slug: string; title: string }

/**
 * A tool's newest four guides, from the index scripts/gen-llms.mjs writes out
 * of blog.ts. Imported on demand, so the index stays out of the entry chunk;
 * a tool page never needs blog.ts itself, which is every article's HTML.
 * Empty until the index arrives, and if it cannot load: related reading is
 * optional.
 */
export function useToolBlogLinks(slug: string | undefined): ToolBlogLink[] {
  const [links, setLinks] = useState<ToolBlogLink[]>([]);
  useEffect(() => {
    let active = true;
    setLinks([]);
    if (slug) import("@/data/tool-blog-links.json").then(({ default: index }) => { if (active) setLinks((index as Record<string, ToolBlogLink[]>)[slug] ?? []); }).catch(() => {});
    return () => { active = false; };
  }, [slug]);
  return links;
}
