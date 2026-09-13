/** Browser U²-Net-P inference. Weights and WASM come from this site; images never upload. */
import type { InferenceSession, Tensor as OrtTensor } from "onnxruntime-web";

export const BG_MODEL_ID = "PrivaTools/u2netp";
export const BG_MODEL_URL = "/models/u2netp.onnx";
export const BG_MODEL_SHA256 = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8";
const CACHE = "transformers-cache";
const MODEL_BYTES = 4574861;
const SIDE = 320;
const MAX_PIXELS = 40_000_000;
type Loaded = { session: InferenceSession; Tensor: typeof OrtTensor };
let loadedPromise: Promise<Loaded> | null = null;

async function readModel(onProgress?: (pct: number) => void): Promise<Uint8Array> {
    const url = new URL(BG_MODEL_URL, location.origin).href;
    const cache = typeof caches === "undefined" ? null : await caches.open(CACHE).catch(() => null);
    const cached = await cache?.match(url);
    let bytes: Uint8Array;
    if (cached) bytes = new Uint8Array(await cached.arrayBuffer());
    else {
        const response = await fetch(url, { credentials: "omit" });
        if (!response.ok) throw new Error("The browser model is unavailable. Retry, or choose server processing.");
        const reader = response.body?.getReader();
        if (!reader) bytes = new Uint8Array(await response.arrayBuffer());
        else {
            const chunks: Uint8Array[] = [];
            let received = 0;
            for (;;) {
                const { done, value } = await reader.read();
                if (done) break;
                received += value.byteLength;
                if (received > 6 * 1024 * 1024) { await reader.cancel(); throw new Error("The model download was not valid. Please retry."); }
                chunks.push(value);
                onProgress?.(Math.min(95, Math.round(received / MODEL_BYTES * 95)));
            }
            bytes = new Uint8Array(received);
            let offset = 0;
            for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
        }
    }
    const digest = await crypto.subtle.digest("SHA-256", bytes as Uint8Array<ArrayBuffer>);
    const hash = [...new Uint8Array(digest)].map(n => n.toString(16).padStart(2, "0")).join("");
    if (hash !== BG_MODEL_SHA256) {
        await cache?.delete(url);
        throw new Error("The model download did not pass its integrity check. Please retry.");
    }
    if (!cached) await cache?.put(url, new Response(bytes as Uint8Array<ArrayBuffer>, { headers: { "Content-Length": String(bytes.length), "Content-Type": "application/octet-stream" } })).catch(() => undefined);
    return bytes;
}

export function loadBgModel(onProgress?: (pct: number) => void): Promise<Loaded> {
    if (!loadedPromise) {
        loadedPromise = (async () => {
            onProgress?.(0);
            const ort = await import("onnxruntime-web");
            // One WASM thread works without cross-origin isolation and avoids
            // competing with the other local AI tools for all CPU cores.
            ort.env.wasm.numThreads = 1;
            ort.env.wasm.wasmPaths = { wasm: new URL("/models/ort-wasm-simd-threaded.wasm", location.origin).href, mjs: new URL("/models/ort-wasm-simd-threaded.mjs", location.origin).href };
            const bytes = await readModel(onProgress);
            const session = await ort.InferenceSession.create(bytes, { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
            onProgress?.(100);
            return { session, Tensor: ort.Tensor };
        })();
        loadedPromise.catch(() => { loadedPromise = null; });
    }
    return loadedPromise;
}

/** Match rembg U²-Net-P normalization; preserve source transparency when compositing. */
export function normalizeBgPixels(rgba: Uint8ClampedArray): Float32Array {
    const count = rgba.length / 4;
    let maximum = 1;
    for (let i = 0; i < count; i++) for (let c = 0; c < 3; c++) maximum = Math.max(maximum, rgba[i * 4 + c]);
    const output = new Float32Array(count * 3);
    const mean = [.485, .456, .406], std = [.229, .224, .225];
    for (let c = 0; c < 3; c++) for (let i = 0; i < count; i++) output[c * count + i] = (rgba[i * 4 + c] / maximum - mean[c]) / std[c];
    return output;
}

export function normalizeBgMask(values: ArrayLike<number>): Uint8ClampedArray {
    let low = Infinity, high = -Infinity;
    for (let i = 0; i < values.length; i++) { low = Math.min(low, values[i]); high = Math.max(high, values[i]); }
    if (!Number.isFinite(low) || !Number.isFinite(high)) throw new Error("The model returned an invalid mask. Try another image.");
    const mask = new Uint8ClampedArray(values.length);
    const range = high - low;
    for (let i = 0; i < values.length; i++) mask[i] = range > 1e-8 ? (values[i] - low) / range * 255 : Math.max(0, Math.min(1, values[i])) * 255;
    return mask;
}

export async function removeBackgroundLocal(file: File, onProgress?: (pct: number) => void): Promise<{ blob: Blob; outName: string }> {
    // Decode and validate before starting a model download.
    const bitmap = await createImageBitmap(file).catch(() => { throw new Error("This image could not be read. Try a JPG, PNG or WebP image."); });
    try {
        if (!bitmap.width || !bitmap.height || bitmap.width * bitmap.height > MAX_PIXELS) throw new Error("Browser processing supports images up to 40 megapixels. Resize this image first.");
        const canvas = document.createElement("canvas"); canvas.width = SIDE; canvas.height = SIDE;
        const ctx = canvas.getContext("2d");
        if (!ctx) throw new Error("This browser cannot prepare images. Try another browser or server processing.");
        ctx.drawImage(bitmap, 0, 0, SIDE, SIDE);
        const input = normalizeBgPixels(ctx.getImageData(0, 0, SIDE, SIDE).data);
        const { session, Tensor } = await loadBgModel(onProgress);
        const result = await session.run({ [session.inputNames[0]]: new Tensor("float32", input, [1, 3, SIDE, SIDE]) });
        const prediction = result[session.outputNames[0]];
        if (!prediction || prediction.data.length !== SIDE * SIDE) throw new Error("The model returned an unexpected image mask.");
        const mask = normalizeBgMask(prediction.data as Float32Array);
        const maskCanvas = document.createElement("canvas"); maskCanvas.width = SIDE; maskCanvas.height = SIDE;
        const maskCtx = maskCanvas.getContext("2d")!;
        const pixels = maskCtx.createImageData(SIDE, SIDE);
        for (let i = 0; i < mask.length; i++) { pixels.data[i * 4] = 255; pixels.data[i * 4 + 1] = 255; pixels.data[i * 4 + 2] = 255; pixels.data[i * 4 + 3] = mask[i]; }
        maskCtx.putImageData(pixels, 0, 0);
        canvas.width = bitmap.width; canvas.height = bitmap.height;
        ctx.drawImage(bitmap, 0, 0);
        ctx.globalCompositeOperation = "destination-in";
        ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
        ctx.drawImage(maskCanvas, 0, 0, bitmap.width, bitmap.height);
        const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(b => b ? resolve(b) : reject(new Error("PNG export failed. Please retry.")), "image/png"));
        return { blob, outName: `nobg_${file.name.replace(/\.[^.]+$/, "") || "image"}.png` };
    } finally { bitmap.close(); }
}
