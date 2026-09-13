import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, renderHook } from '@testing-library/react';
import { previewObjectUrl } from './preview-url';
import { useMediaUrl } from './media-files';
import { ImageComparison, MediaPreview } from './MediaStudio';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const objectUrl = (id: string) => `blob:${window.location.origin}/${id}`;

describe('uploaded-file preview boundary', () => {
  it('accepts only same-origin blob URLs without markup, control characters or URL entities', () => {
    const safe = objectUrl('d4ec10f1-4cfe-4ff9-a5be-9e24b5ecee50');
    expect(previewObjectUrl(safe)).toBe(safe);
    for (const value of [null, undefined, '', 'javascript:alert(1)', 'data:image/svg+xml,<svg onload=alert(1)>', 'https://example.com/image.png', 'blob:https://example.com/other', objectUrl('x" onerror="alert(1)'), objectUrl('<svg>'), objectUrl('x&y'), objectUrl('x\ny')]) {
      expect(previewObjectUrl(value), String(value)).toBeUndefined();
    }
  });
  it('revokes the previous object URL on replacement and the current one on unmount', () => {
    const first = new Blob(['one']), next = new Blob(['two']);
    const create = vi.spyOn(URL, 'createObjectURL').mockReturnValueOnce(objectUrl('one')).mockReturnValueOnce(objectUrl('two'));
    const revoke = vi.spyOn(URL, 'revokeObjectURL');
    const { result, rerender, unmount } = renderHook(({ file }) => useMediaUrl(file), { initialProps: { file: first } });
    expect(result.current).toBe(objectUrl('one'));
    expect(create).toHaveBeenCalledWith(first);
    rerender({ file: next });
    expect(result.current).toBe(objectUrl('two'));
    expect(revoke).toHaveBeenCalledWith(objectUrl('one'));
    unmount();
    expect(revoke).toHaveBeenCalledWith(objectUrl('two'));
  });
  it('keeps hostile filenames as accessible text and prevents invalid preview URLs reaching image sinks', () => {
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('javascript:alert(1)');
    const file = new File(['<svg onload=alert(1)>'], '"><img onerror=alert(1)>.svg', { type: 'image/svg+xml' });
    const { container } = render(<><MediaPreview file={file} name={file.name} /><ImageComparison before={file} after={file} name={file.name} /></>);
    expect(container.querySelectorAll('img')).toHaveLength(3);
    for (const image of container.querySelectorAll('img')) {
      expect(image.getAttribute('src') || '').toBe('');
      expect(image).not.toHaveAttribute('onerror');
    }
    expect(container.querySelector('img')?.alt).toBe(`Preview of ${file.name}`);
    expect(container.querySelector('svg[onload],script')).toBeNull();
  });
});
