// Stage the reviewed CPU-only model/runtime on the same origin. Generated
// binaries stay out of git; production/dev fail early if integrity is wrong.
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, mkdirSync, writeFileSync, renameSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const MODEL_URL = 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx';
export const MODEL_SHA256 = '309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8';
export const MODEL_BYTES = 4574861;
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

export function verifyModel(bytes) {
  if (hash(bytes) !== MODEL_SHA256) throw new Error('U²-Net-P model integrity check failed. The bytes do not match the reviewed SHA-256.');
  return bytes;
}

export async function downloadModel(fetchImpl = fetch) {
  const response = await fetchImpl(MODEL_URL, { signal: AbortSignal.timeout(90_000), redirect: 'follow' });
  if (!response.ok) throw new Error(`U²-Net-P download failed (${response.status}).`);
  const advertisedSize = Number(response.headers.get('content-length') || 0);
  if (advertisedSize > 10_000_000) throw new Error('U²-Net-P download exceeded the expected size.');
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length > 10_000_000) throw new Error('U²-Net-P download exceeded the expected size.');
  return verifyModel(bytes);
}

function writeAtomic(path, bytes) {
  if (existsSync(path) && hash(readFileSync(path)) === hash(bytes)) return;
  const temporary = `${path}.${process.pid}.tmp`;
  writeFileSync(temporary, bytes, { mode: 0o644 });
  renameSync(temporary, path);
}

export async function prepareBrowserModel({ root = ROOT, fetchImpl = fetch, explicitModel = process.env.PRIVATOOLS_U2NETP_PATH } = {}) {
  const output = join(root, 'public/models');
  mkdirSync(output, { recursive: true });
  const candidates = explicitModel ? [resolve(explicitModel)] : [
    join(output, 'u2netp.onnx'),
    join(root, '../data/local/models/models/u2netp/u2netp.onnx'),
  ];
  let model;
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      // Do not silently trust or replace a damaged explicitly selected cache.
      model = verifyModel(readFileSync(candidate));
      break;
    }
  }
  if (explicitModel && !model) throw new Error('PRIVATOOLS_U2NETP_PATH does not identify an existing model file.');
  if (!model) model = await downloadModel(fetchImpl);
  writeAtomic(join(output, 'u2netp.onnx'), model);

  const runtime = join(root, 'node_modules/onnxruntime-web');
  const version = JSON.parse(readFileSync(join(runtime, 'package.json'), 'utf8')).version;
  const assets = [{ file: 'u2netp.onnx', bytes: model.length, sha256: MODEL_SHA256, source: MODEL_URL }];
  // ORT needs both its CPU WASM bytes and the matching JavaScript bootstrap.
  // Explicit runtime paths prevent the larger JSEP/CDN fallback from loading.
  for (const file of ['ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs']) {
    const bytes = readFileSync(join(runtime, 'dist', file));
    writeAtomic(join(output, file), bytes);
    assets.push({ file, bytes: bytes.length, sha256: hash(bytes), source: `onnxruntime-web@${version}` });
  }
  writeAtomic(join(output, 'asset-manifest.json'), JSON.stringify({ model: 'U²-Net-P', runtimeVersion: version, assets }, null, 2) + '\n');
  console.log(`[browser-model] U²-Net-P verified; CPU runtime ${version} staged on /models/`);
  return assets;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await prepareBrowserModel();
}
