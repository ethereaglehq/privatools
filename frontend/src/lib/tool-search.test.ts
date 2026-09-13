import { describe, expect, it } from 'vitest';
import { searchTools, fileSuggestions } from '@/skins/daylight/consumer/catalogue';
import { normalizeToolQuery } from './tool-search';
describe('human shorthand tool search', () => {
  it.each([
    ['img', 'image-converter'], ['img2pdf', 'image-to-pdf'], ['pdf2md', 'pdf-to-markdown'],
    ['.md', 'markdown-html'], ['md to pdf', 'markdown-to-pdf'], ['vid', 'video-converter'],
    ['b64', 'base64'], ['jpg', 'jpg-to-pdf'], ['docx to pdf', 'word-to-pdf'],
  ])('finds %s without requiring the formal name', (query, slug) => {
    expect(searchTools(query).map(tool => tool.slug)).toContain(slug);
  });
  it('keeps every query term meaningful and ranks the requested direction first', () => {
    expect(searchTools('md2pdf')[0].slug).toBe('markdown-to-pdf');
    expect(searchTools('img unicorn nonexistent')).toEqual([]);
    expect(normalizeToolQuery('PDF → MD')).toBe('pdf to md');
  });
  it('offers file-preserving Markdown destinations for one document', () => {
    const file = new File(['# Hello'], 'notes.md', { type: 'text/markdown' });
    expect(fileSuggestions([file]).map(tool => tool.slug)).toEqual(['markdown-html', 'markdown-to-pdf']);
    expect(fileSuggestions([file, new File(['# Second'], 'two.md')])).toEqual([]);
  });
});
