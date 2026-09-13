export interface ZipEntry { name: string; bytes: number; compressedBytes: number; directory: boolean; }
export interface ZipDirectory { total: number; entries: ZipEntry[]; truncated: boolean; }
/** Read metadata only: never inflate a file or trust an entry as a filesystem path. */
export async function readZipDirectory(blob: Blob): Promise<ZipDirectory> {
    const tailOffset = Math.max(0, blob.size - 65_557);
    const tail = new DataView(await blob.slice(tailOffset).arrayBuffer());
    let end = -1;
    for (let i = tail.byteLength - 22; i >= 0; i--) if (tail.getUint32(i, true) === 0x06054b50 && i + 22 + tail.getUint16(i + 20, true) === tail.byteLength) { end = i; break; }
    if (end < 0) throw new Error("Archive directory unavailable.");
    const total = tail.getUint16(end + 10, true), size = tail.getUint32(end + 12, true), offset = tail.getUint32(end + 16, true);
    if (total === 65535 || size === 0xffffffff || offset === 0xffffffff || offset + size > blob.size || size > 8 * 1024 * 1024) throw new Error("This ZIP is too large to list here. The complete download is still available.");
    const bytes = new Uint8Array(await blob.slice(offset, offset + size).arrayBuffer()), view = new DataView(bytes.buffer);
    const entries: ZipEntry[] = []; let cursor = 0;
    for (let i = 0; i < Math.min(total, 1000); i++) {
        if (cursor + 46 > view.byteLength || view.getUint32(cursor, true) !== 0x02014b50) throw new Error("Archive directory unavailable.");
        const nameLength = view.getUint16(cursor + 28, true), extraLength = view.getUint16(cursor + 30, true), commentLength = view.getUint16(cursor + 32, true);
        const next = cursor + 46 + nameLength + extraLength + commentLength;
        if (next > view.byteLength) throw new Error("Archive directory is incomplete.");
        const utf8 = Boolean(view.getUint16(cursor + 8, true) & 0x800);
        // Our server emits UTF-8 names where needed; ASCII is identical in both encodings.
        const name = new TextDecoder(utf8 ? "utf-8" : "windows-1252").decode(bytes.slice(cursor + 46, cursor + 46 + nameLength));
        entries.push({name, bytes: view.getUint32(cursor + 24, true), compressedBytes: view.getUint32(cursor + 20, true), directory: name.endsWith("/")});
        cursor = next;
    }
    return {total, entries, truncated: entries.length < total};
}
