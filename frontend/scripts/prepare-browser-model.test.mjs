import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { downloadModel, MODEL_URL, MODEL_SHA256, prepareBrowserModel, verifyModel } from './prepare-browser-model.mjs';

// No network or large model dependency: failure paths must reject untrusted
// bytes before any runtime download, and missing explicit paths stay explicit.
test('rejects tampered model bytes', () => {
  assert.throws(() => verifyModel(Buffer.from('not the published model')), /integrity check failed/);
  assert.match(MODEL_SHA256, /^[a-f0-9]{64}$/);
});

test('downloads only the fixed upstream artifact and rejects a replacement', async () => {
  let url;
  await assert.rejects(downloadModel(async value => {
    url = value;
    return new Response('replacement weights', { status: 200 });
  }), /integrity check failed/);
  assert.equal(url, MODEL_URL);
});

test('reports upstream download failure rather than staging an error page', async () => {
  await assert.rejects(downloadModel(async () => new Response('unavailable', { status: 503 })), /download failed \(503\)/);
});

test('rejects oversized remote response before reading its body', async () => {
  await assert.rejects(downloadModel(async () => ({
    ok: true,
    headers: new Headers({ 'content-length': '20000000' }),
    arrayBuffer() { throw new Error('body must not be read'); },
  })), /exceeded the expected size/);
});

test('offline cache selection fails explicitly without falling back to the network', async () => {
  const root = mkdtempSync(join(tmpdir(), 'privatools-model-test-'));
  try {
    await assert.rejects(prepareBrowserModel({ root, explicitModel: join(root, 'missing.onnx'), fetchImpl() { throw new Error('network must not run'); } }), /does not identify an existing/);
    const corrupt = join(root, 'corrupt.onnx');
    writeFileSync(corrupt, 'corrupt');
    await assert.rejects(prepareBrowserModel({ root, explicitModel: corrupt, fetchImpl() { throw new Error('network must not run'); } }), /integrity check failed/);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('staged generated cache cannot silently ship corrupt model bytes', async () => {
  const root = mkdtempSync(join(tmpdir(), 'privatools-model-test-'));
  try {
    mkdirSync(join(root, 'public/models'), { recursive: true });
    writeFileSync(join(root, 'public/models/u2netp.onnx'), 'corrupt cached file');
    await assert.rejects(prepareBrowserModel({ root, fetchImpl() { throw new Error('network must not run'); } }), /integrity check failed/);
    assert.equal(readFileSync(join(root, 'public/models/u2netp.onnx'), 'utf8'), 'corrupt cached file');
  } finally { rmSync(root, { recursive: true, force: true }); }
});
