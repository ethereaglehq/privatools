import { searchToolList } from '@/lib/tool-search';
import { tools } from '@/data/tools';
import { nonPdfTools } from '@/data/non-pdf-tools';

export interface ConsumerTool {
  slug: string;
  name: string;
  description: string;
  category: string;
  kind: 'pdf' | 'other';
  clientOnly?: boolean;
  accepts?: string;
  synonyms?: string;
  popularity?: number;
}

export const catalogue: ConsumerTool[] = [
  ...tools.map(tool => ({ ...tool, kind: 'pdf' as const })),
  ...nonPdfTools.map(tool => ({ ...tool, kind: 'other' as const })),
];
export const toolBySlug = new Map(catalogue.map(tool => [tool.slug, tool]));
export const toolHref = (tool: ConsumerTool) => (tool.kind === 'pdf' ? '/tool/' : '/tools/') + tool.slug;
export const commonSlugs = ['merge-pdf', 'compress-pdf', 'split-pdf', 'pdf-to-word', 'resize-crop-image', 'json-xml-formatter'];

export function searchTools(query: string): ConsumerTool[] { return searchToolList(catalogue, query); }

export type RecentTool = { s: string; ts: number };
export type SavedWorkflow = { name: string; slugs: string[]; savedAt: number };
export function savedWorkflows(): SavedWorkflow[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem('privatools_pipeline_saved') || '[]');
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is SavedWorkflow => Boolean(item) && typeof item.name === 'string'
      && Array.isArray(item.slugs) && item.slugs.length > 0 && item.slugs.every((slug: unknown) => typeof slug === 'string' && toolBySlug.has(slug))
      && typeof item.savedAt === 'number').slice(0, 10);
  } catch { return []; }
}
export function workflowHref(workflow: SavedWorkflow): string {
  // Merge accepts several source files; the pipeline runner accepts one input.
  // Reopen its dedicated workspace instead of silently filtering out the step.
  if (workflow.slugs.length === 1 && workflow.slugs[0] === 'merge-pdf') return '/tool/merge-pdf';
  const payload = btoa(JSON.stringify({ version: 1, steps: workflow.slugs })).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return '/pipeline?p=' + payload;
}

/** Only destinations with implemented array handoff consumers are offered. */
export function fileSuggestions(files: File[]): ConsumerTool[] {
  if (!files.length) return [];
  const every = (pattern: RegExp) => files.every(file => pattern.test(file.name));
  const slugs = every(/\.pdf$/i) ? ['merge-pdf', 'compress-pdf', 'pdf-to-markdown', 'extract-images']
    : every(/\.(png|jpe?g|webp|bmp|tiff?|gif|svg|heic)$/i) ? ['image-to-pdf']
    : every(/\.docx$/i) ? ['word-to-pdf']
    : every(/\.xlsx$/i) ? ['excel-to-pdf']
    : every(/\.pptx$/i) ? ['pptx-to-pdf-convert']
    : every(/\.(doc|docx|xls|xlsx|ppt|pptx|odt|ods|odp)$/i) ? ['office-to-pdf']
    : files.length === 1 && every(/\.(md|markdown)$/i) ? ['markdown-html', 'markdown-to-pdf']
    : every(/\.txt$/i) ? ['txt-to-pdf']
    : every(/\.json$/i) ? ['json-to-pdf']
    : every(/\.epub$/i) ? ['epub-to-pdf']
    : every(/\.rtf$/i) ? ['rtf-to-pdf'] : [];
  return slugs.map(slug => toolBySlug.get(slug)).filter((tool): tool is ConsumerTool => Boolean(tool));
}
