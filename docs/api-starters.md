# API starter integrations

The API page links to `/api-starters/privatools-api-starters.zip`. It contains
Python and JavaScript CLI starters, three n8n PDF workflows, an explicit n8n
deletion workflow, an interactive Postman collection, and synthetic sample
PDFs. All run against the existing versioned API; no new server or runtime
service is introduced.

The complete user guide is [examples/api/README.md](../examples/api/README.md).
Its generated public copy is `/api-starters/README.md`. Run
`python3 scripts/api-starters-build.py` after changes and its `--check` mode
to detect stale downloads. The manifest records each payload's size and
SHA-256, and the ZIP uses fixed timestamps for reproducible output.

CLI files share a versioned state format: API base, operation/options, ordered
input hashes and sizes, logical idempotency key, and job ID. No API key or
document filename is saved. State is written before submission and updated
atomically after acceptance. Existing state prevents accidental resubmission
or reuse with different inputs. Both languages read the same format.

Clients and workflows construct authenticated job URLs from the configured
base and a validated job ID. They reject/disable redirects and ignore URLs in
API responses. No API credential is embedded in the shipped artifacts.

CLI default cleanup follows a successful, exact-size, atomic local save.
Interrupted/truncated downloads, existing destinations, terminal jobs, and
filesystem failures preserve the remote result until normal expiry. n8n and
Postman retain results until explicit deletion because a successful HTTP
download alone does not prove that the user's destination saved the file.

Validation commands:

```sh
python3 scripts/api-starters-build.py --check
python3 scripts/api-starters-test.py
node --test scripts/api-starters-artifacts.test.mjs
```

The local HTTP tests exercise actual Python and Node CLI processes, including
multipart uploads, idempotent retries, resume, quota delays, terminal states,
truncation/save failures, and safe deletion. Integration tests evaluate n8n
Code nodes and native-node wiring with mock responses, and Postman scripts
with a mocked `pm` context. They do not claim an installed n8n/Postman runtime
test. Do not describe fixture tests as Oracle throughput measurements.
