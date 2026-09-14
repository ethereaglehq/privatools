import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import ApiReference from "./ApiReference";

export const catalogFixture = {
    schema_version: "1", api_version: "v1", base_path: "/api/v1", openapi_url: "/api/v1/openapi.json",
    limits: { daily_units: 500, daily_bytes: 262144000, concurrent_requests_per_key: 3, global_concurrent_requests: 6, requests_per_minute: 30, request_burst: 6, bytes_definition: "Actual request-body bytes, including multipart overhead." },
    components: { schemas: { Merge: { type: "object", required: ["files"], properties: { files: { type: "array", minItems: 2, maxItems: 100, items: { type: "string", format: "binary" } }, page_ranges: { type: "string" } } } } },
    operations: [
        { id: "v1_post_merge", method: "POST", path: "/api/v1/merge", summary: "Merge PDFs", description: "Merge your PDF files in order.", category: "PDF processing", request_body: { content: { "multipart/form-data": { schema: { $ref: "#/components/schemas/Merge" } } } }, parameters: [], responses: { "200": { description: "A merged PDF", content: { "application/pdf": { schema: { type: "string", format: "binary" } } } } }, cost: { units: 1, mode: "fixed", description: "1 processing unit per admitted request." }, async: { supported: false }, constraints: ["Upload 2–100 PDFs using repeated files fields."] },
        { id: "v1_get_usage", method: "GET", path: "/api/v1/usage", summary: "Current usage", description: "Read current usage.", category: "Key and usage", request_body: null, parameters: [], responses: { "200": { description: "Usage", content: { "application/json": { schema: {} } } } }, cost: { units: 0, mode: "fixed", description: "No processing units." }, async: { supported: false }, constraints: [] },
    ], unavailable_tools: [{ slug: "chat-with-pdf", name: "Chat with PDF", reason: "No v1 HTTP endpoint." }],
};
afterEach(() => vi.unstubAllGlobals());

it("loads public metadata without a key and searches exact request and output details", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => catalogFixture });
    vi.stubGlobal("fetch", fetcher);
    render(<ApiReference />);
    expect(await screen.findByText("2 operations available")).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledWith("/api/v1/operations", expect.objectContaining({ credentials: "omit" }));
    expect(fetcher.mock.calls[0][1].headers).toBeUndefined();
    fireEvent.change(screen.getByRole("searchbox", { name: "Search API operations" }), { target: { value: "merge" } });
    expect(screen.queryByText("Current usage")).not.toBeInTheDocument();
    const operation = screen.getByTestId("api-operation-v1_post_merge");
    fireEvent.click(within(operation).getByText("Merge PDFs"));
    expect(await within(operation).findByText("application/pdf")).toBeVisible();
    expect(within(operation).getByText("files")).toBeVisible();
    expect(within(operation).getByText("required")).toBeVisible();
    expect(within(operation).getByText("Upload 2–100 PDFs using repeated files fields.")).toBeVisible();
    expect(screen.getByText("Chat with PDF")).toBeInTheDocument();
});

it("shows a recoverable reference error for malformed data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ operations: [{}] }) }));
    render(<ApiReference />);
    expect(await screen.findByRole("alert")).toHaveTextContent("reference could not be loaded");
    expect(screen.getByRole("button", { name: "Retry reference" })).toBeInTheDocument();
});

it("keeps empty searches understandable and shows HTTP workflow guidance", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => catalogFixture }));
    render(<ApiReference />);
    await screen.findByText("2 operations available");
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "not-an-operation" } });
    expect(screen.getByText("No operations match. Try another name, path, or category.")).toBeInTheDocument();
    expect(screen.getByText(/In n8n/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "OpenAPI JSON" })).toHaveAttribute("href", "/api/v1/openapi.json");
});

it("builds multipart templates with repeated files and omits unspecified optional fields", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => catalogFixture }));
    render(<ApiReference />);
    fireEvent.click(await screen.findByText("Merge PDFs"));
    const code = await screen.findByLabelText("curl request template");
    expect(code).toHaveTextContent("files=@first.pdf");
    expect(code).toHaveTextContent("files=@second.pdf");
    expect(code).toHaveTextContent("Do not automatically retry processing POSTs.");
    expect(code).not.toHaveTextContent("page_ranges=REPLACE_ME");
    const operation = screen.getByTestId("api-operation-v1_post_merge");
    fireEvent.click(within(operation).getByRole("button", { name: "Python" }));
    expect(screen.getByLabelText("Python request template")).toHaveTextContent("stack.enter_context(open(\"first.pdf\", 'rb'))");
    fireEvent.click(within(operation).getByRole("button", { name: "JavaScript" }));
    expect(screen.getByLabelText("JavaScript request template")).toHaveTextContent('body.append("files", new Blob');
});

it("reports background availability and retention from the deployment", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...catalogFixture, async: { enabled: true, available: true, operations: ["merge"], result_retention_seconds: 3600 } }) }));
    render(<ApiReference />);
    expect(await screen.findByText(/Background processing is available for: merge/)).toBeInTheDocument();
    expect(screen.getByText(/Completed results remain available for 60 minutes/)).toBeInTheDocument();
});

it("distinguishes per-key and global HTTP limits, burst capacity, and exemptions", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
        ...catalogFixture,
        limits: { ...catalogFixture.limits, concurrent_requests_per_key: 2, global_concurrent_requests: 8, requests_per_minute: 40, request_burst: 5 },
    }) }));
    render(<ApiReference />);
    expect(await screen.findByText(/Up to 2 simultaneous admitted HTTP processing requests per key/)).toHaveTextContent("8 across all keys");
    expect(screen.getByText(/40 processing requests per minute per key/)).toHaveTextContent("burst capacity of 5");
    expect(screen.getByText(/Information calls, including key and usage checks/)).toHaveTextContent("job polling, result downloads, and deletion");
    expect(screen.getByText(/Information calls, including key and usage checks/)).toHaveTextContent("do not consume processing units, processing request slots, or the shared per-key request burst");
});

it("includes schema-required Idempotency-Key in every job submission template", async () => {
    const submit = {
        ...catalogFixture.operations[0], id: "submit_async_job", path: "/api/v1/jobs", summary: "Submit an async job", category: "Jobs",
        parameters: [{ in: "header", name: "Idempotency-Key", required: true, schema: { type: "string", minLength: 1, maxLength: 128 } }],
        request_body: { content: { "multipart/form-data": { schema: { type: "object", required: ["operation", "files"], properties: {
            operation: { type: "string", enum: ["grayscale", "compress", "merge", "pdf-to-text"] },
            options: { type: "string", default: "{}" },
            files: { type: "array", items: { type: "string", format: "binary" }, minItems: 1, maxItems: 10 },
        } } } } },
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...catalogFixture, operations: [submit] }) }));
    render(<ApiReference />);
    fireEvent.click(await screen.findByText("Submit an async job"));
    const curl = await screen.findByLabelText("curl request template");
    expect(curl).toHaveTextContent("-H 'Idempotency-Key: REPLACE_ME'");
    expect(curl).toHaveTextContent("files=@input.pdf");
    expect(curl).toHaveTextContent("Retry a job submission only with the identical Idempotency-Key and payload.");
    expect(curl).not.toHaveTextContent("Do not automatically retry processing POSTs.");
    expect(screen.queryByText(/async submission is not available for this operation/)).not.toBeInTheDocument();
    const operation = screen.getByTestId("api-operation-submit_async_job");
    fireEvent.click(within(operation).getByRole("button", { name: "Python" }));
    expect(screen.getByLabelText("Python request template")).toHaveTextContent('headers["Idempotency-Key"] = \'REPLACE_ME\'');
    expect(screen.getByLabelText("Python request template")).toHaveTextContent("Retry a job submission only with the identical Idempotency-Key and payload.");
    fireEvent.click(within(operation).getByRole("button", { name: "JavaScript" }));
    expect(screen.getByLabelText("JavaScript request template")).toHaveTextContent('headers["Idempotency-Key"] = \'REPLACE_ME\';');
    expect(screen.getByLabelText("JavaScript request template")).toHaveTextContent("Retry a job submission only with the identical Idempotency-Key and payload.");
});

it.each(["/api/v1/jobs/{job_id}", "/api/v1/jobs/{job_id}/result"])("does not describe job endpoint %s as an unavailable async adapter", async path => {
    const operation = { ...catalogFixture.operations[1], id: "job_status", path, summary: "Job status" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...catalogFixture, operations: [operation] }) }));
    render(<ApiReference />);
    fireEvent.click(await screen.findByText("Job status"));
    await screen.findByLabelText("curl request template");
    expect(screen.queryByText(/async submission is not available for this operation/)).not.toBeInTheDocument();
    expect(screen.getByText("No processing units.")).toBeVisible();
});

it("does not repeat a constraint already present in the operation description", async () => {
    const operation = catalogFixture.operations[0];
    const constraint = operation.constraints[0];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({
        ...catalogFixture, operations: [{ ...operation, description: constraint }],
    }) }));
    render(<ApiReference />);
    fireEvent.click(await screen.findByText("Merge PDFs"));
    await screen.findByText("application/pdf");
    expect(screen.getAllByText(constraint)).toHaveLength(1);
});
