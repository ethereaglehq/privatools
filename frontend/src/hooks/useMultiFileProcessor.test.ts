import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useMultiFileProcessor, type ProcessOptions } from "./useMultiFileProcessor";
import { installNetwork } from "@/test/fake-network";

const RUN_EVENT = "privatools:tool-run";
type Detail = Record<string, unknown>;

function listen(): Detail[] {
  const seen: Detail[] = [];
  window.addEventListener(RUN_EVENT, event => seen.push((event as CustomEvent<Detail>).detail));
  return seen;
}
function file(name: string): File { return new File(["x"], name, { type: "text/plain" }); }
function options(localProcess: ProcessOptions["localProcess"]): ProcessOptions {
  return { endpoint: "noop", outputExt: "txt", outputSuffix: null, localProcess };
}

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe("useMultiFileProcessor usage events", () => {
  it("emits one single-mode tool run with the file count when every file succeeds", async () => {
    const seen = listen();
    const { result } = renderHook(() => useMultiFileProcessor());
    act(() => result.current.addFiles([file("a.txt"), file("b.txt")]));
    await act(() => result.current.run(options(async () => ({ blob: new Blob(["ok"]) }))));
    expect(result.current.doneCount).toBe(2);
    expect(seen).toEqual([{ mode: "single", outcome: "success", files: 2 }]);
  });

  it("reports partial and error outcomes without leaking names or messages", async () => {
    const seen = listen();
    const { result } = renderHook(() => useMultiFileProcessor());
    act(() => result.current.addFiles([file("secret-a.txt"), file("secret-b.txt")]));
    await act(() => result.current.run(options(async f => { if (f.name === "secret-b.txt") throw new Error("boom secret"); return { blob: new Blob(["ok"]) }; })));
    await act(() => result.current.run(options(async () => { throw new Error("boom secret"); }), true));
    // A local processor that throws failed in the browser.
    expect(seen).toEqual([
      { mode: "single", outcome: "partial", files: 2, errorKind: "browser" },
      { mode: "single", outcome: "error", files: 1, errorKind: "browser" },
    ]);
    expect(JSON.stringify(seen)).not.toContain("secret");
  });

  it("reports the category of a server refusal", async () => {
    const seen = listen();
    installNetwork({ uploadMs: 0, answerAfterMs: 0, status: 429, body: "slow down" });
    const { result } = renderHook(() => useMultiFileProcessor());
    act(() => result.current.addFiles([file("secret.txt")]));
    await act(() => result.current.run({ endpoint: "/compress", outputExt: "txt", outputSuffix: null, uploadOptions: { retry: { attempts: 0, backoffMs: 1 } } }));
    expect(seen).toEqual([{ mode: "single", outcome: "error", files: 1, errorKind: "rate_limited" }]);
  });

  it("emits nothing when a run has no files to process", async () => {
    const seen = listen();
    const { result } = renderHook(() => useMultiFileProcessor());
    await act(() => result.current.run(options(async () => ({ blob: new Blob(["ok"]) }))));
    expect(seen).toEqual([]);
  });
});
