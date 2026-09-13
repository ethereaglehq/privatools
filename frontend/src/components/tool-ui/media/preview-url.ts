/** Only local object URLs belong in uploaded-file image and media previews. */
export function previewObjectUrl(value: string | null | undefined): string | undefined {
  if (!value || /["'&<>]/.test(value)) return undefined;
  if (Array.from(value).some(character => character.charCodeAt(0) <= 32 || character.charCodeAt(0) === 127)) return undefined;
  try {
    const url = new URL(value);
    return url.protocol === "blob:" && url.origin === window.location.origin ? value : undefined;
  } catch {
    return undefined;
  }
}
