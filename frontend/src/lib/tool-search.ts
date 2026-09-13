/** Search vocabulary shared by the command menu, catalogue and favorites. */
export interface SearchableTool {
  slug: string; name: string; description: string; category: string;
  synonyms?: string; accepts?: string; popularity?: number;
}
const aliases: Record<string, string[]> = {
  img: ['image', 'photo', 'picture'], imgs: ['image', 'photo', 'picture'], images: ['image'], photo: ['photo', 'image'], pics: ['image', 'photo'],
  md: ['markdown'], markdown: ['markdown'], jpg: ['jpg', 'jpeg'], jpeg: ['jpg', 'jpeg'],
  doc: ['doc', 'word', 'document'], docx: ['docx', 'word'], docs: ['document', 'word'],
  xls: ['excel', 'spreadsheet', 'xls'], xlsx: ['excel', 'spreadsheet', 'xlsx'], ppt: ['powerpoint', 'presentation', 'ppt'], pptx: ['powerpoint', 'presentation', 'pptx'],
  txt: ['text', 'txt'], vid: ['video'], vids: ['video'], aud: ['audio'], snd: ['audio', 'sound'],
  bg: ['background'], bkg: ['background'], rm: ['remove'], del: ['delete', 'remove'],
  b64: ['base64'], qr: ['qr'], pw: ['password'], pwd: ['password'], passwd: ['password'],
  zip: ['zip', 'archive'], unzip: ['extract archive', 'unzip'], epub: ['epub', 'ebook'],
  jsn: ['json'], yml: ['yaml', 'yml'], regex: ['regex', 'regular expression'], re: ['regular expression'],
};
export function normalizeToolQuery(value: string): string {
  return value.normalize('NFKC').toLowerCase().trim()
    .replace(/\b(pdf|img|image|md|markdown|docx?|txt|jpg|jpeg|png|webp|mp[34]|wav|csv|json|html|xml|xlsx?|pptx?)2(?=[a-z0-9])/g, '$1 to ')
    .replace(/(?:→|->|=>)/g, ' to ').replace(/^[.]+/, '').replace(/[_-]+/g, ' ').replace(/\s+/g, ' ');
}
export function toolSearchScore(tool: SearchableTool, query: string): number {
  const normalized = normalizeToolQuery(query);
  const terms = normalized.split(' ').filter(word => word && !['to', 'for', 'and', '&'].includes(word));
  if (!terms.length) return 0;
  const name = normalizeToolQuery(tool.name);
  const title = `${name} ${normalizeToolQuery(tool.slug)}`;
  const haystack = `${title} ${tool.description} ${tool.synonyms || ''} ${tool.category} ${tool.accepts || ''}`.toLowerCase();
  let score = 0;
  for (const term of terms) {
    const alternatives = aliases[term] || [term];
    if (!alternatives.some(word => haystack.includes(word))) return -1;
    if (alternatives.some(word => title.includes(word))) score += 10;
  }
  if (name === normalized) score += 100;
  if (name.startsWith(normalized)) score += 40;
  if (title.includes(terms.map(term => aliases[term]?.[0] || term).join(' to '))) score += 20;
  return score;
}
export function searchToolList<T extends SearchableTool>(list: T[], query: string): T[] {
  return list.map(tool => ({ tool, score: toolSearchScore(tool, query) })).filter(item => item.score >= 0)
    .sort((a, b) => b.score - a.score || (a.tool.popularity ?? 999) - (b.tool.popularity ?? 999))
    .map(item => item.tool);
}
