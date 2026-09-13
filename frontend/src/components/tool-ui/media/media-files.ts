import { useEffect, useState } from "react";
import { previewObjectUrl } from "./preview-url";
export type MediaKind = 'image' | 'video' | 'audio' | 'file';

export function useMediaUrl(file?: Blob | null) {
  const [url, setUrl] = useState('');
  useEffect(() => { if (!file) { setUrl(''); return; } const next = URL.createObjectURL(file); setUrl(next); return () => URL.revokeObjectURL(next); }, [file]);
  return previewObjectUrl(url) ?? '';
}

export function mediaKind(file?: Blob | null, name = ''): MediaKind {
  if (file?.type.startsWith('image/') || /\.(png|jpe?g|webp|gif|svg|bmp|tiff?|heic|heif|ico)$/i.test(name)) return 'image';
  if (file?.type.startsWith('audio/') || /\.(mp3|wav|aac|m4a|flac|ogg)$/i.test(name)) return 'audio';
  if (file?.type.startsWith('video/') || /\.(mp4|mov|webm|avi|mkv|m4v)$/i.test(name)) return 'video';
  return 'file';
}
