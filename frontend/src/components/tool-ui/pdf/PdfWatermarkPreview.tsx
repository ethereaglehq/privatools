import { useEffect, useState } from "react";
import { PdfPageStage } from "./PdfPageStage";

/** Placement follows the server's point-based geometry on the actual source page. */
export function PdfWatermarkPreview({ file, mode, text, fontSize, opacity, position, image, imageScale }: {
    file: File; mode: "text" | "image"; text: string; fontSize: number; opacity: number; position: string; image?: File; imageScale: number;
}) {
    const [asset, setAsset] = useState<{ url: string; ratio: number } | null>(null);
    useEffect(() => {
        if (!image) { setAsset(null); return; }
        const url = URL.createObjectURL(image), img = new Image();
        let cancelled = false;
        img.onload = () => { if (!cancelled) setAsset({ url, ratio: img.height / img.width }); };
        img.src = url;
        return () => { cancelled = true; URL.revokeObjectURL(url); };
    }, [image]);
    return <div className="pdf-stage-context"><PdfPageStage file={file} overlay={({ width, height }) => {
        const imageMode = mode === "image";
        if (imageMode && !asset) return null;
        let w = Math.max(20, width * imageScale), h = w * (asset?.ratio || 1);
        if (h > height * .9) { w *= height * .9 / h; h = height * .9; }
        const center = position === "center" || position === "diagonal";
        const left = position.endsWith("left"), right = position.endsWith("right"), top = position.startsWith("top"), bottom = position.startsWith("bottom");
        const x = left ? 10 : right ? width - 10 : width / 2;
        const y = top ? fontSize + 10 : bottom ? height - 10 : height / 2;
        if (imageMode) {
            const ix = left ? 10 : right ? width - w - 10 : (width - w) / 2, iy = top ? 10 : bottom ? height - h - 10 : (height - h) / 2;
            const stamp = (px: number, py: number, key?: string) => <image key={key} href={asset!.url} x={px} y={py} width={w} height={h} opacity={opacity} />;
            if (position === "tile") return <g pointerEvents="none">{Array.from({ length: Math.ceil(width / Math.max(50, Math.floor(w * 1.6))) }, (_, col) => Array.from({ length: Math.ceil(height / Math.max(40, Math.floor(h * 1.6))) }, (_, row) => stamp(col * Math.max(50, Math.floor(w * 1.6)), height - h - row * Math.max(40, Math.floor(h * 1.6)), `${col}-${row}`)))}</g>;
            return <g pointerEvents="none" transform={position === "diagonal" ? `rotate(-45 ${width / 2} ${height / 2})` : undefined}>{stamp(ix, iy)}</g>;
        }
        const stamp = (px: number, py: number, anchor: "start" | "middle" | "end", rotate: boolean, key?: string) => <text key={key} x={px} y={py} textAnchor={anchor} fontFamily="Arial, Helvetica, sans-serif" fontSize={fontSize} fill="#808080" opacity={opacity} transform={rotate ? `rotate(-45 ${px} ${py})` : undefined}>{text}</text>;
        if (position === "tile") return <g pointerEvents="none">{Array.from({ length: Math.ceil(width / Math.max(40, Math.floor(fontSize * Math.max(text.length, 1) * .7))) }, (_, col) => Array.from({ length: Math.ceil(height / Math.max(30, Math.floor(fontSize * 3))) }, (_, row) => stamp(col * Math.max(40, Math.floor(fontSize * Math.max(text.length, 1) * .7)), height - row * Math.max(30, Math.floor(fontSize * 3)), "start", true, `${col}-${row}`)))}</g>;
        return <g pointerEvents="none">{stamp(x, y, left ? "start" : right ? "end" : "middle", center)}</g>;
    }} /><p className="pdf-preview-context-note">Placement preview on your first file. Text spacing may differ slightly in the PDF. These settings apply to every selected file.</p></div>;
}
