/** Per-tool guide files exported from backend/app/tool_content.py (see scripts/seo/export-tool-guides.py). */
export interface ToolGuideStep { name: string; text: string }
export interface ToolGuideQuestion { q: string; a: string }
export interface ToolGuide { howto: ToolGuideStep[]; faq: ToolGuideQuestion[] }

// One chunk per tool; only the visited tool's file is fetched.
const guides = import.meta.glob<ToolGuide>("../data/tool-guide/*.json", { import: "default" });

export function loadToolGuide(slug: string): Promise<ToolGuide | null> {
  const loader = guides[`../data/tool-guide/${slug}.json`];
  return loader ? loader().catch(() => null) : Promise.resolve(null);
}
