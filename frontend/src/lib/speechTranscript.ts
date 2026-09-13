export interface SpeechSegment { start: number; end: number; text: string; }
export function transcriptTime(seconds: number): string {
    const milliseconds = Math.max(0, Math.round(Number.isFinite(seconds) ? seconds * 1000 : 0));
    const pad = (value: number, width = 2) => String(value).padStart(width, "0");
    return `${pad(Math.floor(milliseconds / 3600000))}:${pad(Math.floor(milliseconds / 60000) % 60)}:${pad(Math.floor(milliseconds / 1000) % 60)},${pad(milliseconds % 1000, 3)}`;
}
export function transcriptSrt(segments: SpeechSegment[]): string {
    return segments.map((segment, index) => `${index + 1}\n${transcriptTime(segment.start)} --> ${transcriptTime(segment.end)}\n${segment.text.trim()}\n`).join("\n");
}
