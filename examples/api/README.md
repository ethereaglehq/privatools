# PrivaTools API starters

Merge, compress, and extract text from PDFs using the free hosted API. Python and
JavaScript starters complete the asynchronous lifecycle: upload, poll, save a
complete result locally, then delete the server copy. Use `--retain` to keep it
available for another download until **one hour after completion**.

**Your PDFs are uploaded to PrivaTools.** The CLI state file contains job IDs,
idempotency keys, options, file sizes, and SHA-256 hashes; it never contains your
API key, document contents, or input filenames. Treat state files as private
metadata. Use only state files you created, since they contain the API base URL.
The API key is required again to resume or delete. Local outputs/state files
remain until you remove them.

These are small, editable starter clients, not an installed SDK. Python 3.10+
and Node.js 22+ require **no additional packages**. Uploads are buffered locally
(up to 50 MiB total); downloads stream to a temporary file and are published
only after the byte count matches the API's result metadata. Existing output
files are never overwritten. A failed save/download leaves the server result
available until its normal expiry.

## First successful conversion

Create an API key from your PrivaTools account. Set `PRIVATOOLS_API_KEY` in your
shell without putting its value into command history:

```sh
read -r -s PRIVATOOLS_API_KEY
export PRIVATOOLS_API_KEY
```

Paste the key at the hidden prompt and press Enter. Run these commands from the
extracted starter directory. The included PDFs contain harmless sample text.

```sh
python3 privatools.py merge sample-first.pdf sample-second.pdf \
  --output merged.pdf --state merge-job.json

python3 privatools.py compress sample-first.pdf \
  --level recommended --output compressed.pdf --state compress-job.json

python3 privatools.py pdf-to-text sample-first.pdf \
  --output extracted.json --state text-job.json
```

The equivalent JavaScript commands are:

```sh
node privatools.mjs merge sample-first.pdf sample-second.pdf \
  --output merged-node.pdf --state merge-node-job.json

node privatools.mjs compress sample-first.pdf \
  --output compressed-node.pdf --state compress-node-job.json

node privatools.mjs pdf-to-text sample-first.pdf \
  --output extracted-node.json --state text-node-job.json
```

Text extraction produces JSON with `text`, `pages`, and `characters` fields.
It extracts an existing text layer; scanned PDFs may require OCR, which these
async recipes do not yet support. Compression might not reduce every PDF.
Merge accepts 2–10 ordered PDFs; the other recipes each accept one PDF.

## Resume, retry, retain, delete

Each new state file creates one logical idempotency key **before submission**.
The CLI prints its state path and, once accepted, its job ID. Each automatic
submission retry uses the same operation/options/ordered file contents and
idempotency key. An accepted job is never submitted again when its ID is saved.

```sh
# Keep the server copy for another download, until its normal expiry.
python3 privatools.py compress sample-first.pdf --output first-copy.pdf \
  --state retained-job.json --retain

# Resume polling or download a second copy; either runtime can read the state.
node privatools.mjs resume --state retained-job.json \
  --output second-copy.pdf --retain

# Delete deliberately, or cancel an unfinished job.
python3 privatools.py delete --state retained-job.json
```

If the connection fails before the job ID is saved, repeat the original file
command with the **same `--state` path and unchanged inputs/options**. The CLI
checks hashes before reusing its idempotency key. Changing inputs requires a
new state path. Omitting `--state` generates a unique path and prints it; save
that path for recovery. Deduplication records can be cleaned up 24 hours after
completion, so do not reuse old state files for new work or rely on indefinite
deduplication. Keep the same account-issued API key for the job lifecycle.

The default deadline is 20 minutes, with at most five attempts per request and
600 status polls. Each HTTP attempt has a 30-second timeout bounded by the
remaining deadline, including the response body. `Retry-After` supports both
seconds and HTTP dates. A delay
that exceeds the remaining deadline stops the client so it can be resumed
later. Network failures and HTTP 429/502/503/504 can be retried within that
budget. Other HTTP errors stop immediately. Terminal `failed`, `canceled`, and
`expired` jobs stop polling. Use `--deadline-seconds 1800` for a longer wait
(maximum 3600). There is no automatic retry of synchronous conversions.

A failed DELETE does not undo a saved local output. Repeat `delete` with the
state file to retry cleanup. `deletion_pending` means the server is terminating
active processing before cleanup completes. Server expiry still applies if
you close a client or lose the state file.

The hosted base is `https://api.privatools.me/api/v1`. Use `--base-url` only for
a server you trust. HTTPS is required except on localhost; redirects are
disabled. Clients construct status/result routes locally and never follow a
server-provided URL with your key.

## Import an n8n workflow

Import `n8n-merge.json`, `n8n-compress.json`, or `n8n-pdf-to-text.json` into your
existing n8n instance. They use built-in HTTP Request 4.2, Code 2, If 2.2, and
Wait 1.1 nodes. No community node or extra server is needed.

1. In **every HTTP Request node**, choose a generic **Header Auth** credential.
   Its Name is `X-API-Key`; its Value is your key. Store it in n8n credentials,
   never in a Code node or exported workflow. No credential ID/key is included.
2. Execute the workflow with its synthetic sample PDFs. It uploads repeated
   multipart `files` fields, waits between polls, and returns the actual PDF or
   JSON file in **`binary.result`**. JSON extraction is deliberately delivered
   as a file, so it can be saved just like a PDF.
3. Replace **Sample PDFs** with your file source for real work. Supply **one
   item** with `binary.pdf`; merge also requires `binary.pdf2`. Extend the merge
   form fields and validation if you need more than two input PDFs.
4. Save the **Remember job** output (`jobId` and `idempotencyKey`) in your own
   workflow state. To resume, supply `json.jobId` on the input item. To retry a
   submission in a new execution before obtaining a job ID, supply the original
   `json.idempotencyKey` and identical file bytes/options. A fresh execution
   without those values represents new work and can consume units again.
5. Connect **Result binary** to your storage/destination node. Confirm that
   destination succeeded before removing the server copy. These workflows
   **retain results by default**. To delete or cancel explicitly, import
   `n8n-delete-job.json`, set its saved job ID, select the same Header Auth
   credential, and execute it. Do not connect DELETE directly to a download
   before your destination has saved the output.

Submission retries use the same idempotency key, honor `Retry-After`, and stop
after five attempts. Polling honors `Retry-After` and stops at 600 checks or
20 minutes. Authentication/validation/terminal-job errors stop; network errors
stop with recoverable IDs in earlier node outputs. Redirects are disabled.

**n8n has its own data retention.** Its execution storage can contain input
and result documents independently of PrivaTools. These imports disable saved
successful/failed/manual execution data, but review your instance's binary
storage, logging, backups, and execution settings before processing private
documents. Save needed job IDs/output in your intended destination before
leaving the execution. A downstream save failure does not delete the server
result.

## Import the Postman collection

Import `privatools.postman_collection.json`. Create a private Postman
environment variable named `PRIVATOOLS_API_KEY`, mark it secret, and put your
key in its local value. This is a Postman variable; Postman does not
automatically read your shell environment variable. Keep it out of shared
environments, collections, and exports.

Use **individual requests**, not **Run collection**:

1. Choose one **Submit** recipe. Reselect the local PDF files under **Body**
   (the included sample filenames are placeholders for your local files).
2. Send it. A pre-request script creates and persists that recipe's logical
   idempotency key; a successful response saves `jobId`. For 429/503, wait the
   response's `Retry-After` and send again with the same key. For new work,
   clear that recipe's `*IdempotencyKey` variable first. Do not change files
   or options while reusing a key.
3. Send **Get job status**, waiting at least `Retry-After` between checks.
   Stop on a terminal state or after 20 minutes. Resume later if necessary.
4. Once succeeded, use **Send and Download** on **Download completed result**.
   Verify that the saved byte count matches `result.bytes` from status.
5. To delete after saving (or cancel deliberately), set `confirmDeleteJobId`
   to that job ID, then send **Delete or cancel job explicitly**. The collection
   skips the request when confirmation is missing and clears the confirmation
   after a successful response. It never deletes
   automatically after a download.

Redirect following is disabled per request. Base URLs are explicit collection
variables; result/status URLs from responses are never used. The collection
includes discovery requests for the current operation catalog and OpenAPI.

## Availability and limits

The hosted API is free. Default per-key limits are 500 units and 250 MiB of
HTTP request bodies per UTC day, including multipart overhead. Initial async
limits are 50 MiB input, 100 MiB output, and three outstanding jobs per key.
One background worker runs at a time. Polling/download/delete do not spend
processing units. Limits and temporary availability can change; check
[the current operation catalog](https://api.privatools.me/api/v1/operations)
and [the API reference](https://privatools.me/api). Avoid polling a daily-quota
rejection as though it were a brief concurrency limit.

## Maintainers: generate and verify

Source clients and this README live in `examples/api/`. The deterministic
generator creates the samples, integrations, manifest with SHA-256 checksums,
and ZIP under `frontend/public/api-starters/`.

```sh
python3 scripts/api-starters-build.py
python3 scripts/api-starters-build.py --check
python3 scripts/api-starters-test.py
node --test scripts/api-starters-artifacts.test.mjs
```

Tests use a local mock API and synthetic files; they do not use customer keys
or upload customer documents. n8n code/expressions and graph branches are
exercised with mocked native node responses; this does not constitute a full
n8n server execution. Import and smoke-test your configured credentials and
destination before using real documents.

Integration formats were checked against the primary
[n8n HTTP Request documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/),
[Wait documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/),
[n8n node source](https://github.com/n8n-io/n8n/tree/master/packages/nodes-base/nodes),
and [Postman collection v2.1 schema](https://schema.postman.com/json/collection/v2.1.0/docs/index.html).
Deletion guards use Postman's documented
[skipRequest method](https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-execution/)
to prevent the request from being sent when confirmation is missing.
