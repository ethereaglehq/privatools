import type { BlogPost } from "@/data/blog";
export const JOURNAL_TOPICS = ["Markdown", "PDF", "Privacy", "AI", "Workflow", "Accounts", "Comparison"];

export function journalDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(new Date(value.length === 10 ? value + "T00:00:00Z" : value));
}

export function filterGuides(posts: BlogPost[], query: string, topic: string) {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return posts.filter(post => {
    if (topic && !post.tags.includes(topic)) return false;
    const text = new DOMParser().parseFromString(post.body, "text/html").body.textContent ?? "";
    const searchable = `${post.title} ${post.description} ${post.tldr ?? ""} ${post.tags.join(" ")} ${text}`.toLocaleLowerCase();
    return words.every(word => searchable.includes(word));
  });
}

export function guideTopic(post: BlogPost) {
  return ["Markdown", "Accounts", "Workflow", "Comparison", "AI", "Privacy", "PDF"].find(topic => post.tags.includes(topic)) || post.tags[0] || "Guide";
}

export interface BlogHeading { id: string; text: string; level: 2 | 3; }
const ARTICLE_TAGS = ["p", "h2", "h3", "h4", "a", "strong", "em", "b", "i", "ul", "ol", "li", "blockquote", "pre", "code", "table", "thead", "tbody", "tr", "th", "td", "br", "hr", "span", "del", "kbd"] as const;
type ArticleTag = typeof ARTICLE_TAGS[number];
export type BlogNode = string | { tag: ArticleTag; children: BlogNode[]; id?: string; href?: string; section?: string; codeBlock?: boolean };
const articleTags: ReadonlySet<string> = new Set(ARTICLE_TAGS);
const discardedTags = new Set(["script", "style", "template", "iframe", "object", "embed", "svg", "math", "form", "input", "button", "img", "link", "meta", "base"]);

/** Article links may use an ordinary web URL or a path on this application. */
function articleHref(value: string | null): string | undefined {
  if (!value || value.includes("\\") || Array.from(value).some(character => character.charCodeAt(0) <= 32 || character.charCodeAt(0) === 127)) return undefined;
  if (/^https?:\/\//i.test(value)) {
    try { const url = new URL(value); return url.username || url.password ? undefined : url.href; }
    catch { return undefined; }
  }
  return value.startsWith("/") && !value.startsWith("//") ? value : undefined;
}

/** Parse inertly, then copy only article semantics into data rendered by React. */
export function prepareBlogBody(body: string, slug: string): { nodes: BlogNode[]; headings: BlogHeading[] } {
  const headings: BlogHeading[] = [];
  const used = new Set<string>();
  function children(node: Node): BlogNode[] { return Array.from(node.childNodes).flatMap(convert); }
  function convert(node: Node): BlogNode[] {
    if (node.nodeType === Node.TEXT_NODE) return [node.textContent ?? ""];
    if (node.nodeType !== Node.ELEMENT_NODE) return [];
    const element = node as Element;
    const name = element.localName.toLowerCase();
    if (discardedTags.has(name)) return [];
    if (!articleTags.has(name)) return children(node);
    const result: Exclude<BlogNode, string> = { tag: name as ArticleTag, children: children(node) };
    if (name === "a") result.href = articleHref(element.getAttribute("href"));
    if (name === "pre" && element.firstElementChild?.localName === "code") result.codeBlock = true;
    if (name === "h2" || name === "h3") {
      const text = element.textContent?.trim() ?? "";
      const base = text.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "section";
      let id = base, count = 2;
      while (used.has(id)) id = `${base}-${count++}`;
      used.add(id); headings.push({ id, text, level: name === "h2" ? 2 : 3 });
      result.id = id;
      result.children.push({ tag: "a", children: ["#"], section: id, href: `/blog/${encodeURIComponent(slug)}?section=${encodeURIComponent(id)}` });
    }
    return [result];
  }
  const document = new DOMParser().parseFromString(body, "text/html");
  return { nodes: children(document.body), headings };
}
