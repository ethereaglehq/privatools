import type { BlogPost } from "@/data/blog";
export const JOURNAL_TOPICS = ["Markdown", "PDF", "Privacy", "AI", "Workflow", "Accounts", "Comparison"];

export function journalDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(new Date(value.length === 10 ? value + "T00:00:00Z" : value));
}

export function filterGuides(posts: BlogPost[], query: string, topic: string) {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return posts.filter(post => (!topic || post.tags.includes(topic)) && words.every(word => `${post.title} ${post.description} ${post.tldr ?? ""} ${post.tags.join(" ")} ${post.body.replace(/<[^>]*>/g, " ")}`.toLocaleLowerCase().includes(word)));
}

export function guideTopic(post: BlogPost) {
  return ["Markdown", "Accounts", "Workflow", "Comparison", "AI", "Privacy", "PDF"].find(topic => post.tags.includes(topic)) || post.tags[0] || "Guide";
}

export interface BlogHeading { id: string; text: string; level: 2 | 3; }

export function prepareBlogBody(body: string, slug: string): { html: string; headings: BlogHeading[] } {
  const headings: BlogHeading[] = [];
  const used = new Set<string>();
  const html = body.replace(/<h([23])(?:\s[^>]*)?>([\s\S]*?)<\/h\1>/gi, (_whole, level, content: string) => {
    const text = content.replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").trim();
    const base = text.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "section";
    let id = base, count = 2;
    while (used.has(id)) id = `${base}-${count++}`;
    used.add(id); headings.push({ id, text, level: Number(level) as 2 | 3 });
    return `<h${level} id="${id}" tabindex="-1">${content}<a class="journal-heading-link" data-blog-heading="${id}" href="/blog/${slug}?section=${id}" aria-label="Link to this section">#</a></h${level}>`;
  }).replace(/<pre><code>([\s\S]*?)<\/code><\/pre>/g, '<div class="journal-code"><button type="button" data-copy-code>Copy example</button><pre><code>$1</code></pre></div>');
  return { html, headings };
}
