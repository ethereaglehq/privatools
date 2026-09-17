import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { test } from 'node:test';
import vm from 'node:vm';
import { Client, StarterError, retryDelay } from '../../../examples/api/privatools.mjs';

const root = resolve(fileURLToPath(new URL('../../..', import.meta.url)));
const publicDir = resolve(root, 'frontend/public/api-starters');
const readJson = async (name) => JSON.parse(await readFile(resolve(publicDir, name), 'utf8'));
const base = 'https://api.privatools.me/api/v1';
const resultBytes = Buffer.from('%PDF-1.4\nsynthetic converted result');
const jobId = 'synthetic-job-001';

function expression(value, item, outputs) {
  if (typeof value !== 'string' || !value.startsWith('={{')) return value;
  return vm.runInNewContext(value.slice(3, -2).trim(), {
    $json: item.json,
    $: (name) => ({ first: () => outputs.get(name)[0] }),
    JSON,
  });
}

// Executes Code scripts and expressions with the same data contract used by
// native HTTP/If/Wait nodes. It intentionally does not claim a real n8n runtime.
async function runWorkflow(workflow, scenario = {}) {
  const nodes = new Map(workflow.nodes.map((node) => [node.name, node]));
  const outputs = new Map();
  const visits = new Map();
  const calls = [];
  let now = Date.parse('2026-09-14T00:00:00Z');
  class Clock extends Date { static now() { return now; } }
  let current = 'Run sample';
  let items = [{ json: {} }];
  let statusCount = 0;
  let submitCount = 0;
  for (let steps = 0; current && steps < 10000; steps++) {
    const node = nodes.get(current);
    assert.ok(node, `Missing target node ${current}`);
    const runIndex = visits.get(current) || 0;
    visits.set(current, runIndex + 1);
    let branch = 0;
    if (node.type === 'n8n-nodes-base.code') {
      if (current === 'Configure request' && scenario.resume) items[0].json.jobId = jobId;
      if (current === 'Configure request' && scenario.idempotencyKey) items[0].json.idempotencyKey = scenario.idempotencyKey;
      const context = {
        $input: { first: () => items[0], all: () => items },
        $: (name) => ({ first: () => outputs.get(name)[0] }),
        $execution: { id: 'mock-execution-001' }, $runIndex: runIndex,
        Date: Clock, Buffer,
      };
      const script = vm.runInNewContext(`(async function() { ${node.parameters.jsCode}\n })`, context);
      const helper = { helpers: { getBinaryDataBuffer: async (index, field) => Buffer.from(items[index].binary[field].data, 'base64') } };
      items = await script.call(helper);
    } else if (node.type === 'n8n-nodes-base.if') {
      const condition = node.parameters.conditions.conditions[0];
      branch = expression(condition.leftValue, items[0], outputs) === condition.rightValue ? 0 : 1;
    } else if (node.type === 'n8n-nodes-base.wait') {
      const seconds = expression(node.parameters.amount, items[0], outputs);
      assert.ok(Number.isFinite(seconds) && seconds >= 1, 'Wait amount is bounded and valid');
      now += seconds * 1000;
    } else if (node.type === 'n8n-nodes-base.httpRequest') {
      const method = node.parameters.method;
      const url = expression(node.parameters.url, items[0], outputs);
      const request = { method, url };
      assert.ok(url.startsWith(`${base}/jobs`), 'Ignore response-supplied origins');
      assert.equal(node.parameters.options.redirect.redirect.followRedirects, false);
      if (method === 'POST') {
        request.idempotencyKey = expression(node.parameters.headerParameters.parameters[0].value, items[0], outputs);
        request.form = node.parameters.bodyParameters.parameters.map((field) => [field.name,
          field.parameterType === 'formBinaryData'
            ? Buffer.from(items[0].binary[field.inputDataFieldName].data, 'base64').toString('base64')
            : expression(field.value, items[0], outputs)]);
        submitCount++;
        const statusCode = scenario.submissionAlways429 || scenario.submissionRetry && submitCount === 1 ? 429 : 202;
        items = [{ json: { statusCode, headers: { 'retry-after': scenario.dailyQuota ? '3600' : '2' }, body: {
          id: jobId, state: 'queued', status_url: 'https://attacker.invalid/key',
        } } }];
      } else if (url.endsWith('/result')) {
        assert.equal(node.parameters.options.response.response.responseFormat, 'file');
        assert.equal(node.parameters.options.response.response.outputPropertyName, 'result');
        items = [{ json: { statusCode: 200 }, binary: { result: {
          data: (scenario.truncated ? resultBytes.subarray(0, 3) : resultBytes).toString('base64'), mimeType: 'application/pdf',
        } } }];
      } else {
        statusCount++;
        const state = scenario.terminal || (statusCount < 2 ? 'running' : 'succeeded');
        const statusCode = scenario.pollRetry && statusCount === 1 ? 503 : 200;
        items = [{ json: { statusCode, headers: { 'retry-after': scenario.deadline ? '3600' : '2' }, body: {
          id: jobId, state, result: { bytes: resultBytes.length, url: 'https://attacker.invalid/key' }, expires_at: '2026-09-14T01:00:00Z',
        } } }];
      }
      calls.push(request);
    }
    outputs.set(current, items);
    const links = workflow.connections[current]?.main?.[branch] || [];
    assert.ok(links.length <= 1, 'This starter routes one item without fan-out');
    current = links[0]?.node;
  }
  assert.equal(current, undefined, 'Workflow has a bounded terminating route');
  return { items, calls, outputs, visits };
}

test('download manifest hashes match and build is deterministic', async () => {
  const manifest = await readJson('manifest.json');
  assert.deepEqual(manifest.operations, ['merge', 'compress', 'pdf-to-text']);
  for (const file of manifest.files) {
    const bytes = await readFile(resolve(publicDir, file.name));
    assert.equal(bytes.length, file.bytes);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), file.sha256);
    assert.equal(file.url, `/api-starters/${file.name}`);
  }
  const check = spawnSync(process.env.PYTHON || 'python3', [resolve(root, 'scripts/api/starters/build.py'), '--check'], { encoding: 'utf8' });
  assert.equal(check.status, 0, check.stderr + check.stdout);
});

test('Node retry parser respects HTTP-date and daily-quota delays', () => {
  assert.equal(retryDelay(new Headers({ 'Retry-After': '3600' }), 1), 3600);
  const future = new Date(Date.now() + 60000).toUTCString();
  const seconds = retryDelay(new Headers({ 'Retry-After': future }), 1);
  assert.ok(seconds >= 58 && seconds <= 60);
  assert.equal(retryDelay(new Headers(), 4), 4);
  assert.equal(retryDelay(new Headers({ 'Retry-After': 'nonsense' }), 4), 4);
  assert.throws(() => new Client('https://api.privatools.me/api/v1?key=x', 'synthetic'), StarterError);
  assert.throws(() => new Client('http://elsewhere.invalid/api/v1', 'synthetic'), StarterError);
});

for (const operation of ['merge', 'compress', 'pdf-to-text']) {
  test(`n8n ${operation} uploads real binary, polls, and returns verified result`, async () => {
    const workflow = await readJson(`n8n-${operation}.json`);
    const executed = await runWorkflow(workflow, { submissionRetry: true, pollRetry: true });
    const submits = executed.calls.filter((call) => call.method === 'POST');
    assert.equal(submits.length, 2);
    assert.deepEqual(submits[0], submits[1]);
    assert.equal(submits[0].form.find(([field]) => field === 'operation')[1], operation);
    const uploads = submits[0].form.filter(([field]) => field === 'files');
    assert.equal(uploads.length, operation === 'merge' ? 2 : 1);
    uploads.forEach(([, file]) => assert.match(Buffer.from(file, 'base64').toString(), /^%PDF-1\.4/));
    assert.deepEqual(Buffer.from(executed.items[0].binary.result.data, 'base64'), resultBytes);
    assert.equal(executed.items[0].json.serverResultRetained, true);
    assert.equal(executed.calls.filter((call) => call.method === 'DELETE').length, 0);
    assert.equal(workflow.active, false);
    assert.equal(workflow.settings.saveManualExecutions, false);
    assert.equal(workflow.settings.saveDataSuccessExecution, 'none');
    for (const node of workflow.nodes.filter((node) => node.type.endsWith('httpRequest'))) {
      assert.equal(node.parameters.authentication, 'genericCredentialType');
      assert.equal(node.parameters.genericAuthType, 'httpHeaderAuth');
      assert.equal(node.credentials, undefined, 'Import contains no account-specific credential');
    }
  });
}

test('n8n resume bypasses submission and preserves caller logical key', async () => {
  const workflow = await readJson('n8n-compress.json');
  const executed = await runWorkflow(workflow, { resume: true, idempotencyKey: 'original-logical-key' });
  assert.equal(executed.calls.filter((call) => call.method === 'POST').length, 0);
  assert.equal(executed.outputs.get('Remember job')[0].json.idempotencyKey, 'original-logical-key');
});

test('n8n terminal states, exhausted retries, long delays and truncated output stop', async () => {
  const workflow = await readJson('n8n-compress.json');
  for (const terminal of ['failed', 'canceled', 'expired']) {
    await assert.rejects(runWorkflow(workflow, { terminal }), new RegExp(`Job ${terminal}`));
  }
  await assert.rejects(runWorkflow(workflow, { submissionAlways429: true }), /Submission HTTP 429/);
  await assert.rejects(runWorkflow(workflow, { submissionAlways429: true, dailyQuota: true }), /delay exceeds deadline/);
  await assert.rejects(runWorkflow(workflow, { deadline: true }), /delay exceeds deadline/);
  await assert.rejects(runWorkflow(workflow, { truncated: true }), /Incomplete result/);
});

test('n8n explicit delete requires a deliberately supplied job ID', async () => {
  const workflow = await readJson('n8n-delete-job.json');
  const node = workflow.nodes.find((node) => node.name === 'Set saved job ID');
  assert.throws(() => vm.runInNewContext(`(() => { ${node.parameters.jsCode} })()`), /Set a valid jobId/);
  const deleteNode = workflow.nodes.find((node) => node.name === 'Delete server result');
  assert.equal(deleteNode.parameters.method, 'DELETE');
  assert.equal(deleteNode.parameters.options.redirect.redirect.followRedirects, false);
});

function executePostman(item, when, variables, response) {
  const collectionVariables = {
    get: (key) => variables.get(key),
    set: (key, value) => variables.set(key, value),
  };
  function expect(value) {
    return { to: { match: (regex) => assert.match(value, regex), include: (entry) => assert.ok(value.includes(entry)) } };
  }
  const pm = {
    collectionVariables,
    variables: { ...collectionVariables, replaceIn: (value) => value === '{{$guid}}' ? 'generated-logical-id' : value },
    response: { code: response?.code, json: () => response?.body },
    test: (_name, check) => check(), expect,
    execution: { skipRequest: () => { throw new Error('Postman request skipped'); } },
  };
  for (const event of item.event || []) {
    if (event.listen === when) vm.runInNewContext(event.script.exec.join('\n'), { pm });
  }
}

test('Postman recipe scripts create once, persist job IDs, and require deletion confirmation', async () => {
  const collection = await readJson('privatools.postman_collection.json');
  assert.equal(collection.info.schema, 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json');
  assert.equal(collection.auth.type, 'apikey');
  assert.equal(collection.auth.apikey.find((item) => item.key === 'value').value, '{{PRIVATOOLS_API_KEY}}');
  const variables = new Map(collection.variable.map(({ key, value }) => [key, value]));
  assert.equal(variables.has('PRIVATOOLS_API_KEY'), false, 'No secret in exported collection variables');
  for (const operation of ['merge', 'compress', 'pdf-to-text']) {
    const item = collection.item.find((item) => item.name === `Submit ${operation}`);
    const variable = operation.replaceAll('-', '_') + 'IdempotencyKey';
    executePostman(item, 'prerequest', variables);
    assert.equal(variables.get(variable), 'generated-logical-id');
    variables.set(variable, 'same-logical-key');
    executePostman(item, 'prerequest', variables);
    assert.equal(variables.get(variable), 'same-logical-key');
    executePostman(item, 'test', variables, { code: 202, body: { id: jobId } });
    assert.equal(variables.get('jobId'), jobId);
    const files = item.request.body.formdata.filter((field) => field.key === 'files');
    assert.equal(files.length, operation === 'merge' ? 2 : 1);
    files.forEach((field) => assert.equal(field.type, 'file'));
  }
  const deletion = collection.item.find((item) => item.name.startsWith('Delete or cancel'));
  assert.throws(() => executePostman(deletion, 'prerequest', variables), /Postman request skipped/);
  variables.set('confirmDeleteJobId', jobId);
  executePostman(deletion, 'prerequest', variables);
  executePostman(deletion, 'test', variables, { code: 200 });
  assert.equal(variables.get('confirmDeleteJobId'), '');
  collection.item.forEach((item) => assert.equal(item.protocolProfileBehavior.followRedirects, false));
});

test('published starter files contain no real credential or external result URL expression', async () => {
  for (const name of await readdir(publicDir)) {
    if (!/\.(?:json|mjs|py|md)$/.test(name)) continue;
    const text = await readFile(resolve(publicDir, name), 'utf8');
    assert.doesNotMatch(text, /\bpk_[A-Za-z0-9]{20,}/);
    if (name.startsWith('n8n-')) {
      const workflow = JSON.parse(text);
      for (const node of workflow.nodes.filter((node) => node.type.endsWith('httpRequest'))) {
        assert.doesNotMatch(node.parameters.url, /status_url|result\.url/);
      }
    }
  }
});
