#!/usr/bin/env python3
"""Build deterministic API starter downloads. Run --check in CI."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "examples/api"
PUBLIC = ROOT / "frontend/public/api-starters"
BASE = "https://api.privatools.me/api/v1"
OPERATIONS = ("merge", "compress", "pdf-to-text")


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def sample_pdf(text):
    content = f"BT /F1 18 Tf 50 740 Td ({text}) Tj ET\n".encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"endstream"]
    result = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return result + f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


DELAY_CODE = """function delay(headers, fallback) {
  const raw = headers?.['retry-after'] ?? headers?.['Retry-After'];
  let seconds = raw == null || raw === '' ? NaN : Number(raw);
  if (!Number.isFinite(seconds) || seconds < 0) {
    const date = Date.parse(raw);
    seconds = Number.isFinite(date) ? Math.max(0, (date - Date.now()) / 1000) : fallback;
  }
  seconds = Math.max(1, seconds);
  if (Date.now() + seconds * 1000 >= config.deadline) throw new Error('Retry delay exceeds deadline. Save the job ID/idempotency key and resume later.');
  return seconds;
}
"""


def n8n_workflow(operation, pdfs):
    nodes, connections = [], {}

    def node(name, kind, version, parameters, position, **extra):
        result = {"id": name.lower().replace(" ", "-"), "name": name,
                  "type": "n8n-nodes-base." + kind, "typeVersion": version,
                  "position": position, "parameters": parameters, **extra}
        nodes.append(result)
        return result

    def code(name, script, position):
        return node(name, "code", 2, {"mode": "runOnceForAllItems", "jsCode": script}, position)

    def edge(source, target, branch=0):
        branches = connections.setdefault(source, {"main": []})["main"]
        while len(branches) <= branch:
            branches.append([])
        branches[branch].append({"node": target, "type": "main", "index": 0})

    def condition(name, field, value, position):
        return node(name, "if", 2.2, {"conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
            "conditions": [{"id": "condition", "leftValue": "={{ $json." + field + " }}", "rightValue": value,
                            "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"}, "options": {}}, position)

    def http(name, method, url, position, response_format="json", **params):
        return node(name, "httpRequest", 4.2, {
            "method": method, "url": url, "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
            "options": {"timeout": 30000, "redirect": {"redirect": {"followRedirects": False}},
                        "response": {"response": {"fullResponse": True, "neverError": response_format == "json",
                                                  "responseFormat": response_format, **({"outputPropertyName": "result"} if response_format == "file" else {})}}}, **params},
            position, notes="Select a Header Auth credential with Name X-API-Key and your key as Value.", notesInFlow=True)

    node("Run sample", "manualTrigger", 1, {}, [0, 0])
    sample_binary = {"pdf": {"data": base64.b64encode(pdfs[0]).decode(), "mimeType": "application/pdf", "fileName": "sample-first.pdf"}}
    if operation == "merge":
        sample_binary["pdf2"] = {"data": base64.b64encode(pdfs[1]).decode(), "mimeType": "application/pdf", "fileName": "sample-second.pdf"}
    code("Sample PDFs", "// Replace this node with your source: one item, binary.pdf" + (" and binary.pdf2" if operation == "merge" else "") + ".\nreturn [{ json: {}, binary: " + json.dumps(sample_binary) + " }];", [220, 0])
    fields = ["pdf", "pdf2"] if operation == "merge" else ["pdf"]
    configure = f"""// The base is explicitly configured here; never take it from an API response.
const baseUrl = '{BASE}';
const operation = '{operation}';
const options = {json.dumps({'level': 'recommended'} if operation == 'compress' else {})};
// To resume, supply json.jobId from the earlier Remember job output.
// To retry a submission in a NEW execution, supply its original json.idempotencyKey.
const source = $input.first();
if ($input.all().length !== 1) throw new Error('Process one logical request/item at a time.');
const jobId = source.json.jobId || '';
const idempotencyKey = source.json.idempotencyKey || 'priva-n8n-' + $execution.id;
if (!/^[A-Za-z0-9_-]{{1,128}}$/.test(idempotencyKey)) throw new Error('Invalid idempotency key.');
if (jobId && !/^[A-Za-z0-9_-]{{1,128}}$/.test(jobId)) throw new Error('Invalid resume job ID.');
if (!jobId) {{
  let bytes = 0;
  for (const field of {json.dumps(fields)}) {{
    if (!source.binary?.[field]) throw new Error('Missing binary.' + field);
    const pdf = await this.helpers.getBinaryDataBuffer(0, field);
    if (pdf.subarray(0, 5).toString() !== '%PDF-') throw new Error('Input must be a PDF.');
    bytes += pdf.length;
  }}
  if (bytes > 50 * 1024 * 1024) throw new Error('Input exceeds 50 MiB.');
}}
return [{{ json: {{ baseUrl, operation, options, idempotencyKey, jobId,
  action: jobId ? 'resume' : 'submit', deadline: Date.now() + 20 * 60 * 1000 }}, binary: source.binary }}];
"""
    code("Configure request", configure, [440, 0])
    condition("Resume existing job", "action", "resume", [660, 0])
    body_fields = [{"parameterType": "formData", "name": "operation", "value": "={{ $json.operation }}"},
                   {"parameterType": "formData", "name": "options", "value": "={{ JSON.stringify($json.options) }}"}]
    body_fields.extend({"parameterType": "formBinaryData", "name": "files", "inputDataFieldName": field} for field in fields)
    http("Submit async job", "POST", "={{ $json.baseUrl + '/jobs' }}", [880, 200],
         sendHeaders=True, headerParameters={"parameters": [{"name": "Idempotency-Key", "value": "={{ $json.idempotencyKey }}"}]},
         sendBody=True, contentType="multipart-form-data", bodyParameters={"parameters": body_fields})
    code("Check submission", """const config = $('Configure request').first().json;
const response = $input.first().json;
if (Date.now() >= config.deadline) throw new Error('Deadline reached. Recover with the same idempotency key.');
""" + DELAY_CODE + """if (response.statusCode === 202) {
  const job = response.body;
  if (!job || !/^[A-Za-z0-9_-]{1,128}$/.test(job.id)) throw new Error('Invalid job response.');
  return [{ json: { ...config, action: 'accepted', jobId: job.id } }];
}
if ([429, 502, 503, 504].includes(response.statusCode) && $runIndex < 4) {
  return [{ json: { ...config, action: 'retry', waitSeconds: delay(response.headers, 2 ** $runIndex) },
    binary: $('Configure request').first().binary }];
}
throw new Error('Submission HTTP ' + response.statusCode + '. Keep the original idempotency key when retrying; correct authentication/input errors first.');
""", [1100, 200])
    condition("Submission accepted", "action", "accepted", [1320, 200])
    node("Wait to resubmit", "wait", 1.1, {"resume": "timeInterval", "amount": "={{ $json.waitSeconds }}", "unit": "seconds"}, [1320, 460])
    code("Remember job", "// Save this jobId and idempotencyKey for later recovery. No API key is in this data.\nreturn [{ json: $input.first().json }];", [1540, 0])
    http("Poll job", "GET", "={{ $('Remember job').first().json.baseUrl + '/jobs/' + $('Remember job').first().json.jobId }}", [1760, 0])
    code("Check status", """const config = $('Remember job').first().json;
const response = $input.first().json;
if (Date.now() >= config.deadline || $runIndex >= 600) throw new Error('Polling budget reached. Resume with saved jobId; result retained.');
""" + DELAY_CODE + """if ([429, 502, 503, 504].includes(response.statusCode)) {
  return [{ json: { action: 'wait', waitSeconds: delay(response.headers, 2) } }];
}
if (response.statusCode !== 200) throw new Error('Status HTTP ' + response.statusCode + '. Result was not deleted.');
const job = response.body;
if (!job || job.id !== config.jobId) throw new Error('Job ID mismatch.');
if (job.state === 'succeeded') {
  const bytes = job.result?.bytes;
  if (!Number.isInteger(bytes) || bytes <= 0 || bytes > 100 * 1024 * 1024) throw new Error('Invalid result size.');
  return [{ json: { action: 'ready', jobId: job.id, bytes, expiresAt: job.expires_at } }];
}
if (['failed', 'canceled', 'expired'].includes(job.state)) throw new Error('Job ' + job.state + '. No automatic deletion was performed.');
if (!['queued', 'running'].includes(job.state)) throw new Error('Unknown job state.');
return [{ json: { action: 'wait', waitSeconds: delay(response.headers, 2) } }];
""", [1980, 0])
    condition("Result ready", "action", "ready", [2200, 0])
    node("Wait before polling", "wait", 1.1, {"resume": "timeInterval", "amount": "={{ $json.waitSeconds }}", "unit": "seconds"}, [2200, 260])
    code("Ready result", "return $input.all();", [2420, 0])
    http("Download result", "GET", "={{ $('Remember job').first().json.baseUrl + '/jobs/' + $('Remember job').first().json.jobId + '/result' }}", [2640, 0], response_format="file")
    code("Result binary", """const item = $input.first();
const ready = $('Ready result').first().json;
if (item.json.statusCode !== 200 || !item.binary?.result) throw new Error('Result download failed; server result retained.');
const data = await this.helpers.getBinaryDataBuffer(0, 'result');
if (data.length !== ready.bytes) throw new Error('Incomplete result; resume to download again.');
// Connect your storage node here. Delete only AFTER that storage node succeeds.
// The supplied manual delete workflow is an explicit separate action.
return [{ json: { jobId: ready.jobId, bytes: data.length, expiresAt: ready.expiresAt,
  serverResultRetained: true }, binary: { result: item.binary.result } }];
""", [2860, 0])
    node("Read before running", "stickyNote", 1, {"content": f"## PrivaTools: {operation}\n1. Select Header Auth (X-API-Key) in all HTTP nodes.\n2. Execute with the synthetic sample, or replace Sample PDFs with binary input.\n3. Save Remember job output to resume. Reuse idempotencyKey only for the same operation/options/ordered file bytes.\n4. Save binary.result to your destination. Results expire one hour after completion.\n5. Run n8n-delete-job.json only after saving, or to cancel deliberately.\n\nUploads/results may also be saved by YOUR n8n execution history. Configure its retention. No credentials are embedded. Network errors stop safely; retry with the same key/job ID.", "height": 380, "width": 620}, [0, -450])
    for left, right in [("Run sample", "Sample PDFs"), ("Sample PDFs", "Configure request"), ("Configure request", "Resume existing job"),
                        ("Submit async job", "Check submission"), ("Check submission", "Submission accepted"),
                        ("Wait to resubmit", "Submit async job"), ("Remember job", "Poll job"), ("Poll job", "Check status"),
                        ("Check status", "Result ready"), ("Wait before polling", "Poll job"), ("Ready result", "Download result"), ("Download result", "Result binary")]:
        edge(left, right)
    edge("Resume existing job", "Remember job", 0)
    edge("Resume existing job", "Submit async job", 1)
    edge("Submission accepted", "Remember job", 0)
    edge("Submission accepted", "Wait to resubmit", 1)
    edge("Result ready", "Ready result", 0)
    edge("Result ready", "Wait before polling", 1)
    return {"name": f"PrivaTools async {operation}", "nodes": nodes, "connections": connections, "active": False,
            "settings": {"executionOrder": "v1", "executionTimeout": 1230, "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False},
            "pinData": {}, "tags": []}


def delete_workflow():
    return {"name": "PrivaTools delete or cancel a saved job", "active": False, "nodes": [
        {"id": "manual", "name": "Delete deliberately", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "parameters": {}},
        {"id": "job", "name": "Set saved job ID", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [220, 0], "parameters": {"mode": "runOnceForAllItems", "jsCode": "const jobId = ''; // Paste the saved job ID. This also cancels running jobs.\nif (!/^[A-Za-z0-9_-]{1,128}$/.test(jobId)) throw new Error('Set a valid jobId after saving the result, or to cancel deliberately.');\nreturn [{ json: { jobId } }];"}},
        {"id": "delete", "name": "Delete server result", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 0],
         "parameters": {"method": "DELETE", "url": "={{ '" + BASE + "/jobs/' + $json.jobId }}", "authentication": "genericCredentialType", "genericAuthType": "httpHeaderAuth",
                        "options": {"timeout": 30000, "redirect": {"redirect": {"followRedirects": False}}, "response": {"response": {"responseFormat": "json"}}}},
         "notes": "Select Header Auth with Name X-API-Key. deletion_pending=true means cancellation is waiting for worker cleanup. Repeated DELETE is safe.", "notesInFlow": True}],
        "connections": {"Delete deliberately": {"main": [[{"node": "Set saved job ID", "type": "main", "index": 0}]]},
                        "Set saved job ID": {"main": [[{"node": "Delete server result", "type": "main", "index": 0}]]}},
        "settings": {"executionOrder": "v1", "executionTimeout": 60, "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none", "saveManualExecutions": False}, "pinData": {}, "tags": []}


def event(when, code):
    return {"listen": when, "script": {"type": "text/javascript", "exec": code.strip().splitlines()}}


def postman_collection():
    items = []
    for operation in OPERATIONS:
        variable = operation.replace("-", "_") + "IdempotencyKey"
        fields = [{"key": "operation", "value": operation, "type": "text"},
                  {"key": "options", "value": json.dumps({"level": "recommended"} if operation == "compress" else {}), "type": "text"},
                  {"key": "files", "type": "file", "src": "sample-first.pdf"}]
        if operation == "merge":
            fields.append({"key": "files", "type": "file", "src": "sample-second.pdf"})
        items.append({"name": "Submit " + operation, "request": {"method": "POST", "url": "{{baseUrl}}/jobs",
                      "header": [{"key": "Idempotency-Key", "value": "{{" + variable + "}}"}], "body": {"mode": "formdata", "formdata": fields},
                      "description": "Select local PDF files in Body before sending. This uses one logical idempotency key until you clear its collection variable. Keep it for identical retries; clear it before new files/options. The scripts save jobId on 202. Use individual requests; this collection does not automatically poll, download to disk, or delete."},
                      "protocolProfileBehavior": {"followRedirects": False}, "event": [
                          event("prerequest", "if (!pm.collectionVariables.get('" + variable + "')) pm.collectionVariables.set('" + variable + "', pm.variables.replaceIn('{{$guid}}'));"),
                          event("test", """pm.test('Accepted or explicit rejection', () => pm.expect([202,400,401,403,409,413,422,429,503]).to.include(pm.response.code));
if (pm.response.code === 202) {
  const job = pm.response.json();
  pm.test('Job ID is safe', () => pm.expect(job.id).to.match(/^[A-Za-z0-9_-]{1,128}$/));
  if (/^[A-Za-z0-9_-]{1,128}$/.test(job.id)) pm.collectionVariables.set('jobId', job.id);
}
// For 429/503, inspect Retry-After. Retry manually with the SAME idempotency key.
""") ]})
    identifier_check = "if (!/^[A-Za-z0-9_-]{1,128}$/.test(pm.variables.get('jobId') || '')) { console.warn('Set jobId from a successful submission.'); pm.execution.skipRequest(); }"
    items.extend([
        {"name": "Get job status", "request": {"method": "GET", "url": "{{baseUrl}}/jobs/{{jobId}}", "description": "Repeat only after Retry-After (normally two seconds). Stop on succeeded, failed, canceled, or expired. Stop after 20 minutes and resume later. Polling spends no processing units."},
         "event": [event("prerequest", identifier_check), event("test", "if (pm.response.code === 200) pm.test('Known state', () => pm.expect(['queued','running','succeeded','failed','canceled','expired']).to.include(pm.response.json().state));")], "protocolProfileBehavior": {"followRedirects": False}},
        {"name": "Download completed result", "request": {"method": "GET", "url": "{{baseUrl}}/jobs/{{jobId}}/result", "description": "After succeeded, use Send and Download to save the PDF (or JSON for pdf-to-text). Check the local file before deleting. The server result remains available for one hour after completion."},
         "event": [event("prerequest", identifier_check)], "protocolProfileBehavior": {"followRedirects": False}},
        {"name": "Delete or cancel job explicitly", "request": {"method": "DELETE", "url": "{{baseUrl}}/jobs/{{jobId}}", "description": "Set confirmDeleteJobId to the SAME jobId only after verifying your saved result, or to cancel deliberately. This request can cancel a running job. Clear confirmation after use. Never run it automatically after an unsaved download."},
         "event": [event("prerequest", identifier_check + "\nif (pm.variables.get('confirmDeleteJobId') !== pm.variables.get('jobId')) { console.warn('Set confirmDeleteJobId to this job ID to explicitly authorize deletion/cancellation.'); pm.execution.skipRequest(); }"),
                   event("test", "if ([200,202].includes(pm.response.code)) pm.collectionVariables.set('confirmDeleteJobId', '');")], "protocolProfileBehavior": {"followRedirects": False}},
        {"name": "Current operation catalog", "request": {"method": "GET", "url": "{{baseUrl}}/operations", "auth": {"type": "noauth"}}, "protocolProfileBehavior": {"followRedirects": False}},
        {"name": "OpenAPI schema", "request": {"method": "GET", "url": "{{baseUrl}}/openapi.json", "auth": {"type": "noauth"}}, "protocolProfileBehavior": {"followRedirects": False}},
    ])
    return {"info": {"name": "PrivaTools async PDF starters", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                     "description": "Import, then create a private environment variable PRIVATOOLS_API_KEY. Choose one Submit recipe, poll status, Send and Download, then delete explicitly. Do not Run collection: requests are interactive recipes. No key is included. Derived from PrivaTools v1 jobs OpenAPI contract; current schema is available in the last request."},
            "auth": {"type": "apikey", "apikey": [{"key": "key", "value": "X-API-Key", "type": "string"}, {"key": "value", "value": "{{PRIVATOOLS_API_KEY}}", "type": "string"}, {"key": "in", "value": "header", "type": "string"}]},
            "variable": [{"key": "baseUrl", "value": BASE}, {"key": "jobId", "value": ""}, {"key": "confirmDeleteJobId", "value": ""}] +
                        [{"key": op.replace("-", "_") + "IdempotencyKey", "value": ""} for op in OPERATIONS], "item": items}


def artifacts():
    pdfs = [sample_pdf("PrivaTools sample one"), sample_pdf("PrivaTools sample two")]
    result = {name: (SOURCE / name).read_bytes() for name in ("README.md", "privatools.py", "privatools.mjs")}
    result.update({"sample-first.pdf": pdfs[0], "sample-second.pdf": pdfs[1], "privatools.postman_collection.json": encoded(postman_collection()), "n8n-delete-job.json": encoded(delete_workflow())})
    result.update({f"n8n-{operation}.json": encoded(n8n_workflow(operation, pdfs)) for operation in OPERATIONS})
    return result


def build(check=False):
    files = artifacts()
    manifest = {"version": 1, "baseUrl": BASE, "operations": list(OPERATIONS), "files": [
        {"name": name, "url": "/api-starters/" + name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(files.items())]}
    files["manifest.json"] = encoded(manifest)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo("privatools-api-starters/" + name, date_time=(2026, 9, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, data)
    files["privatools-api-starters.zip"] = archive.getvalue()
    stale = []
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = PUBLIC / name
        if check:
            if not target.exists() or target.read_bytes() != data:
                stale.append(name)
        else:
            target.write_bytes(data)
    extras = set(path.name for path in PUBLIC.iterdir() if path.is_file()) - set(files)
    if extras or stale:
        raise SystemExit("Starter downloads are stale: " + ", ".join(sorted(extras | set(stale))))
    print(f"{'Checked' if check else 'Built'} {len(files)} starter downloads.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(parser.parse_args().check)
