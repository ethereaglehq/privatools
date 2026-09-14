#!/usr/bin/env node
/** PrivaTools async PDF starter. Node.js 22+, no packages required. */
import { createHash, randomUUID } from 'node:crypto';
import { open, readFile, stat, rename, unlink, link } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

export const DEFAULT_BASE = 'https://api.privatools.me/api/v1';
const MAX_INPUT = 50 * 1024 * 1024;
const MAX_RESULT = 100 * 1024 * 1024;
const OPERATIONS = ['merge', 'compress', 'pdf-to-text'];
const LEVELS = ['light', 'recommended', 'extreme', 'email', 'print', 'archive', 'web'];
const ID = /^[A-Za-z0-9_-]{1,128}$/;
export class StarterError extends Error {}

export function baseUrl(value) {
  let url;
  try { url = new URL(value); } catch { throw new StarterError('Invalid API base URL.'); }
  if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password || url.search || url.hash
      || (url.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname))) {
    throw new StarterError('Use HTTPS without credentials, query, or fragment (HTTP is allowed only on loopback).');
  }
  return value.replace(/\/+$/, '');
}

function jobId(value, key) {
  if (typeof value !== 'string' || !ID.test(value) || key && value.includes(key)) throw new StarterError('The API returned an invalid job ID.');
  return value;
}

export function retryDelay(headers, fallback) {
  const raw = headers.get('retry-after');
  if (raw !== null && raw.trim() !== '') {
    const seconds = Number(raw);
    if (Number.isFinite(seconds) && seconds >= 0) return seconds;
    const timestamp = Date.parse(raw);
    if (Number.isFinite(timestamp)) return Math.max(0, (timestamp - Date.now()) / 1000);
  }
  return fallback;
}

export class Client {
  constructor(base, key, deadlineSeconds = 1200) {
    this.base = baseUrl(base);
    if (!key || !/^[\x21-\x7e]+$/.test(key)) throw new StarterError('Set PRIVATOOLS_API_KEY to your API key.');
    this.key = key;
    this.deadline = performance.now() + deadlineSeconds * 1000;
  }
  remaining() {
    const remaining = (this.deadline - performance.now()) / 1000;
    if (remaining <= 0) throw new StarterError('Deadline reached. Resume using the saved state; the result was not deleted.');
    return remaining;
  }
  async pause(seconds) {
    if (seconds >= this.remaining()) throw new StarterError('Retry-After exceeds the remaining deadline. Resume later using your saved state.');
    await new Promise((done) => setTimeout(done, Math.max(50, seconds * 1000)));
  }
  async request(method, route, body, headers = {}) {
    // Ignore every URL in API responses. Build authenticated routes locally.
    if (!/^jobs(?:\/[A-Za-z0-9_-]{1,128}(?:\/result)?)?$/.test(route)) throw new StarterError('Invalid local API route.');
    for (let attempt = 0; attempt < 5; attempt++) {
      let response;
      let delay = 2 ** attempt + Math.random() / 4;
      const timeout = Math.max(1, Math.ceil(Math.min(30, this.remaining()) * 1000));
      try {
        response = await fetch(`${this.base}/${route}`, {
          method, body, headers: { 'X-API-Key': this.key, ...headers },
          redirect: 'manual', signal: AbortSignal.timeout(timeout),
        });
      } catch {
        if (attempt === 4) throw new StarterError('Network retry budget exhausted. Resume using the saved state.');
      }
      if (response) {
        if (response.ok) return response;
        delay = retryDelay(response.headers, delay);
        await response.body?.cancel();
        if (![429, 502, 503, 504].includes(response.status) || attempt === 4) {
          const requestId = response.headers.get('x-request-id') || '';
          const suffix = ID.test(requestId) && !requestId.includes(this.key) ? ` Request ID: ${requestId}` : '';
          throw new StarterError(`API HTTP ${response.status}.${suffix} Saved state is available for recovery.`);
        }
      }
      await this.pause(delay);
    }
    throw new StarterError('Retry budget exhausted.');
  }
  async json(method, route, body, headers) {
    const response = await this.request(method, route, body, headers);
    const chunks = [];
    let count = 0;
    for await (const chunk of response.body) {
      this.remaining();
      count += chunk.length;
      if (count > 1024 * 1024) throw new StarterError('Unexpectedly large API metadata response.');
      chunks.push(chunk);
    }
    let value;
    try { value = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
    catch { throw new StarterError('Invalid JSON metadata response. Resume using the saved state.'); }
    return [value, response.headers];
  }
}

async function exists(path) {
  try { await stat(path); return true; } catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}

export async function saveState(path, state, isNew = false) {
  // No API key, document filenames, or filesystem input paths are persisted.
  const destination = isNew ? path : resolve(dirname(path), `.priva-state-${randomUUID()}`);
  const handle = await open(destination, 'wx', 0o600);
  try {
    await handle.writeFile(JSON.stringify(state, null, 2) + '\n');
    await handle.sync();
  } finally { await handle.close(); }
  if (!isNew) {
    try { await rename(destination, path); }
    finally { await unlink(destination).catch((error) => { if (error.code !== 'ENOENT') throw error; }); }
  }
}

async function loadState(path) {
  let state;
  try { state = JSON.parse(await readFile(path, 'utf8')); }
  catch { throw new StarterError('Cannot read state JSON.'); }
  if (state?.version !== 1 || !OPERATIONS.includes(state.operation) || !ID.test(state.idempotencyKey)) throw new StarterError('Invalid state file.');
  baseUrl(state.baseUrl);
  if (state.jobId) jobId(state.jobId);
  return state;
}

async function prepareUpload(operation, filenames, level) {
  const [minimum, maximum] = operation === 'merge' ? [2, 10] : [1, 1];
  if (filenames.length < minimum || filenames.length > maximum) throw new StarterError(`${operation} requires ${minimum}–${maximum} PDF inputs.`);
  let size = 0;
  for (const name of filenames) size += (await stat(name)).size;
  if (size > MAX_INPUT) throw new StarterError('Total PDF input exceeds 50 MiB.');
  const blobs = await Promise.all(filenames.map((name) => readFile(name)));
  if (blobs.reduce((sum, blob) => sum + blob.length, 0) > MAX_INPUT || blobs.some((blob) => blob.subarray(0, 5).toString() !== '%PDF-')) {
    throw new StarterError('Inputs must be PDF files totaling at most 50 MiB.');
  }
  const options = operation === 'compress' ? { level } : {};
  const hashes = blobs.map((blob) => ({ sha256: createHash('sha256').update(blob).digest('hex'), bytes: blob.length }));
  const form = new FormData();
  form.append('operation', operation);
  form.append('options', JSON.stringify(options));
  blobs.forEach((blob, index) => form.append('files', new Blob([blob], { type: 'application/pdf' }), `input-${index + 1}.pdf`));
  return { form, options, hashes };
}

export async function waitForJob(client, identifier) {
  for (let count = 0; count < 600; count++) {
    const [job, headers] = await client.json('GET', `jobs/${jobId(identifier)}`);
    if (job.id !== identifier) throw new StarterError('Job ID mismatch.');
    if (job.state === 'succeeded') return job;
    if (['failed', 'canceled', 'expired'].includes(job.state)) {
      const code = job.error?.code;
      const suffix = typeof code === 'string' && /^[a-z0-9_]{1,100}$/.test(code) && !code.includes(client.key) ? ` (${code})` : '';
      throw new StarterError(`Job ${job.state}${suffix}. No result was deleted by this client.`);
    }
    if (!['queued', 'running'].includes(job.state)) throw new StarterError('Unknown job state.');
    await client.pause(Math.max(0.1, retryDelay(headers, 2)));
  }
  throw new StarterError('Polling budget exhausted. Resume using your saved state.');
}

export async function download(client, job, output) {
  const expected = job.result?.bytes;
  if (!Number.isInteger(expected) || expected <= 0 || expected > MAX_RESULT) throw new StarterError('Invalid result size metadata.');
  if (await exists(output)) throw new StarterError('Output already exists. Choose another output path; the server result is retained.');
  const temporary = resolve(dirname(output), `.priva-download-${randomUUID()}`);
  const handle = await open(temporary, 'wx', 0o600);
  try {
    const response = await client.request('GET', `jobs/${jobId(job.id)}/result`);
    let count = 0;
    for await (const chunk of response.body) {
      client.remaining();
      count += chunk.length;
      if (count > expected) throw new StarterError('Result exceeds expected size. The server result is retained.');
      await handle.writeFile(chunk);
    }
    if (count !== expected) throw new StarterError('Result download is incomplete. Resume to download again.');
    await handle.sync();
    // A hard link publishes complete bytes atomically and never replaces a file.
    await link(temporary, output);
  } finally {
    await handle.close();
    await unlink(temporary).catch((error) => { if (error.code !== 'ENOENT') throw error; });
  }
}

export async function main(args = process.argv.slice(2)) {
  const { values, positionals } = parseArgs({ args, allowPositionals: true, options: {
    output: { type: 'string', short: 'o' }, state: { type: 'string' },
    'base-url': { type: 'string' }, level: { type: 'string', default: 'recommended' },
    retain: { type: 'boolean', default: false }, 'deadline-seconds': { type: 'string', default: '1200' },
    help: { type: 'boolean', short: 'h' },
  } });
  if (values.help) {
    console.log('node privatools.mjs <merge|compress|pdf-to-text> FILE... --output FILE [--state JOB.json] [--retain]\nnode privatools.mjs resume --state JOB.json --output FILE [--retain]\nnode privatools.mjs delete --state JOB.json\nSet PRIVATOOLS_API_KEY. Options: --base-url URL --level recommended --deadline-seconds 1200');
    return;
  }
  const [command, ...files] = positionals;
  if (![...OPERATIONS, 'resume', 'delete'].includes(command)) throw new StarterError('Choose merge, compress, pdf-to-text, resume, or delete. Use --help.');
  if (!LEVELS.includes(values.level)) throw new StarterError('Invalid compression level.');
  const deadline = Number(values['deadline-seconds']);
  if (!Number.isFinite(deadline) || deadline <= 0 || deadline > 3600) throw new StarterError('Deadline must be positive and at most 3600 seconds.');
  if (command !== 'delete' && !values.output) throw new StarterError('Provide --output (use a .json filename for pdf-to-text).');
  if (['resume', 'delete'].includes(command) && (!values.state || files.length)) throw new StarterError('Resume/delete requires --state and no file arguments.');
  const statePath = values.state || `privatools-job-${randomUUID().replaceAll('-', '')}.json`;
  const existing = await exists(statePath);
  if (['resume', 'delete'].includes(command) && !existing) throw new StarterError('State file does not exist.');
  let state = existing ? await loadState(statePath) : null;
  const base = baseUrl(values['base-url'] || state?.baseUrl || DEFAULT_BASE);
  if (state && base !== state.baseUrl) throw new StarterError('The API base differs from the saved request. Use new state for a different server.');
  const client = new Client(base, process.env.PRIVATOOLS_API_KEY, deadline);
  if (OPERATIONS.includes(command)) {
    const { form, options, hashes } = await prepareUpload(command, files, values.level);
    if (state) {
      if (state.operation !== command || JSON.stringify(state.options) !== JSON.stringify(options) || JSON.stringify(state.inputs) !== JSON.stringify(hashes)) {
        throw new StarterError('This state belongs to different input/options. Use a new state file for new work.');
      }
    } else {
      state = { version: 1, baseUrl: base, operation: command, options, inputs: hashes,
        idempotencyKey: randomUUID().replaceAll('-', ''), jobId: null };
      await saveState(statePath, state, true);
    }
    console.log(`State: ${statePath}\nIdempotency key: ${state.idempotencyKey}`);
    if (!state.jobId) {
      const [job] = await client.json('POST', 'jobs', form, { 'Idempotency-Key': state.idempotencyKey });
      state.jobId = jobId(job.id, client.key);
      console.log(`Job ID: ${state.jobId}`);
      await saveState(statePath, state);
    }
  }
  if (!state?.jobId) throw new StarterError('Submission was interrupted before saving a job ID. Repeat the original file command with this --state path.');
  jobId(state.jobId, client.key);
  console.log(`Job ID: ${state.jobId}`);
  if (command === 'delete') {
    const [deleted] = await client.json('DELETE', `jobs/${state.jobId}`);
    console.log(deleted.deletion_pending ? 'Cancellation requested; poll to confirm cleanup.' : 'Server result deleted.');
    return;
  }
  const job = await waitForJob(client, state.jobId);
  await download(client, job, values.output);
  console.log(`Saved: ${values.output}`);
  if (values.retain) console.log('Server result retained until its normal expiry (one hour after completion). Use delete to remove it sooner.');
  else {
    const [deleted] = await client.json('DELETE', `jobs/${state.jobId}`);
    console.log(deleted.deletion_pending ? 'Deletion pending.' : 'Server result deleted after successful save.');
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch((error) => {
    // Never log fetch errors, request objects, headers, or reflected response bodies.
    console.error(`Error: ${error instanceof StarterError ? error.message : 'Local IO/response error. The server result was not automatically deleted; use saved state to recover.'}`);
    process.exitCode = 1;
  });
}
