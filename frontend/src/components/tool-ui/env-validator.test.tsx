import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { validateEnv } from "./dev-formatters";
import { EnvValidatorUI } from "./DevMicroTools";

// A PEM key pasted without quotes. The base64 is made up for the test, but it
// has the shape of a real key: 64-character lines, one of them ending in "="
// after a "+" and a "/", and a short last line ending in padding.
const PEM_BODY = [
  "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj",
  "MzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu",
  "NMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyC/GeJ=",
  "AgMBAAE=",
];

const ENV = [
  "DATABASE_URL=postgres://app:s3cr3t-Pa55@db.internal:5432/app",
  "PRIVATE_KEY=-----BEGIN PRIVATE KEY-----",
  ...PEM_BODY,
  "-----END PRIVATE KEY-----",
  "API_TOKEN=tok_9f8e7d",
  "API_TOKEN=tok_second_value_123",
  "GREETING=hello world",
  "EMPTY_ONE=",
  "export STRIPE_SECRET=sk_live_abcdefghijklmnop",
].join("\n");

const EXPECTED = [
  "[WARN] Line 2: quote values that contain spaces",
  "[ERROR] Line 3: not a KEY=value line (no = sign)",
  "[ERROR] Line 4: not a KEY=value line (no = sign)",
  "[ERROR] Line 5: not a KEY=value line (invalid variable name)",
  "[WARN] Line 6: empty value",
  "[ERROR] Line 7: not a KEY=value line (no = sign)",
  "[WARN] Line 8: value looks short for a secret",
  "[WARN] Line 9: duplicate key, first set on line 8",
  "[WARN] Line 10: quote values that contain spaces",
  "[WARN] Line 11: empty value",
  "[ERROR] Line 12: not a KEY=value line (invalid variable name)",
];

// Every finding is one of these, with only line numbers filled in.
const TEMPLATES = [
  /^Line \d+: not a KEY=value line \(no = sign\)$/,
  /^Line \d+: not a KEY=value line \(invalid variable name\)$/,
  /^Line \d+: duplicate key, first set on line \d+$/,
  /^Line \d+: empty value$/,
  /^Line \d+: quote values that contain spaces$/,
  /^Line \d+: value looks short for a secret$/,
  /^No obvious \.env issues found\.$/,
];

const SECRETS = [
  "s3cr3t-Pa55", "DATABASE_URL", "PRIVATE_KEY", "BEGIN PRIVATE", ...PEM_BODY.map(line => line.replace(/=+$/, "")),
  "tok_9f8e7d", "tok_second", "API_TOKEN", "GREETING", "hello world", "EMPTY_ONE", "STRIPE_SECRET", "sk_live",
];

function expectNoInputText(report: string) {
  for (const secret of SECRETS) {
    for (let start = 0; start + 6 <= secret.length; start++) expect(report).not.toContain(secret.slice(start, start + 6));
  }
}

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe(".env Validator report", () => {
  it("names line numbers but never the names, values or PEM lines it checked", () => {
    const issues = validateEnv(ENV);
    expect(issues.map(item => `[${item.level.toUpperCase()}] ${item.text}`)).toEqual(EXPECTED);
    for (const item of issues) expect(TEMPLATES.some(template => template.test(item.text))).toBe(true);
    expectNoInputText(issues.map(item => item.text).join("\n"));
  });

  it("finds nothing to report in a clean file", () => {
    expect(validateEnv("# comment\n\nAPI_URL=https://privatools.me\nNAME=\"two words\"\r\nSECRET_KEY=long-enough-value")).toEqual([
      { level: "ok", text: "No obvious .env issues found." },
    ]);
  });

  it("copies and shows the same report without any of the pasted text", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    const { container } = render(<EnvValidatorUI />);
    fireEvent.change(screen.getByRole("textbox", { name: ".env input" }), { target: { value: ENV } });
    const shown = Array.from(container.querySelectorAll(".pt-lab-issue"), node => node.textContent ?? "");
    expect(shown).toEqual(EXPECTED.map(line => line.replace(/^\[\w+\] /, "")));
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    const copied = writeText.mock.calls[0][0] as string;
    expect(copied).toBe(EXPECTED.join("\n"));
    expectNoInputText(copied);
  });
});
