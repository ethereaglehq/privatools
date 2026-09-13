import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createElement, StrictMode } from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { consumeFileHandoff, consumeFileHandoffs, clearFileHandoffs, FILE_HANDOFF_KEY, storeFileHandoff, storeFileHandoffs } from "@/lib/file-handoff";
import { GenericUI } from "@/components/tool-ui/GenericUI";
import { SimpleConvertUI } from "@/components/tool-ui/SimpleConvertUI";
import { MultiFileUI } from "@/components/tool-ui/MultiFileUI";

function readText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error || new Error("Failed to read file"));
    reader.onload = () => resolve(String(reader.result || ""));
    reader.readAsText(file);
  });
}

describe("file handoff", () => {
  beforeEach(() => {
    clearFileHandoffs();
    sessionStorage.clear();
  });

  afterEach(() => {
    cleanup();
    clearFileHandoffs();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("round-trips a single file without persisting its contents", async () => {
    const writes = vi.spyOn(Storage.prototype, "setItem");
    const source = new File(["hello"], "sample.pdf", { type: "application/pdf", lastModified: 1234 });

    await expect(storeFileHandoff(source, "compress-pdf")).resolves.toBe(true);

    const wrongTool = await consumeFileHandoff("merge-pdf");
    expect(wrongTool).toBeNull();
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).toBeNull();

    const restored = await consumeFileHandoff("compress-pdf");
    expect(restored).toBeInstanceOf(File);
    expect(restored?.name).toBe("sample.pdf");
    expect(restored?.type).toBe("application/pdf");
    expect(restored?.lastModified).toBe(1234);
    expect(restored).toBe(source);
    await expect(readText(restored as File)).resolves.toBe("hello");
    expect(writes).not.toHaveBeenCalled();
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).toBeNull();
    await expect(consumeFileHandoff("compress-pdf")).resolves.toBeNull();
  });

  it("preserves order and distinct bytes when names, sizes and dates match", async () => {
    const first = new File(["first"], "same.pdf", { type: "application/pdf", lastModified: 1234 });
    const second = new File(["other"], "same.pdf", { type: "application/pdf", lastModified: 1234 });
    const selection = [second, first];
    await storeFileHandoffs(selection, "merge-pdf");
    selection.reverse();

    await expect(consumeFileHandoffs("compress-pdf")).resolves.toEqual([]);
    await expect(consumeFileHandoffs()).resolves.toEqual([]);
    const restored = await consumeFileHandoffs("merge-pdf");
    expect(restored).toEqual([second, first]);
    expect(await Promise.all(restored.map(readText))).toEqual(["other", "first"]);
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual([]);
  });

  it("refuses to give a single-file consumer part of a batch", async () => {
    const files = [new File(["a"], "a.pdf"), new File(["b"], "b.pdf")];
    await storeFileHandoffs(files, "merge-pdf");
    await expect(consumeFileHandoff("merge-pdf")).resolves.toBeNull();
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual(files);
  });

  it("carries files larger than the old storage cap even when storage is disabled", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("disabled"); });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => { throw new Error("disabled"); });
    const file = new File([new Uint8Array(4 * 1024 * 1024)], "large.pdf", { type: "application/pdf" });
    await expect(storeFileHandoffs([file], "merge-pdf")).resolves.toBe(true);
    const restored = await consumeFileHandoffs("merge-pdf");
    expect(restored[0]).toBe(file);
    expect(restored[0].size).toBe(4 * 1024 * 1024);
  });

  it("replaces an entire batch and clears legacy payloads", async () => {
    const old = new File(["old"], "old.pdf");
    const fresh = new File(["new"], "new.png");
    await storeFileHandoffs([old, old], "merge-pdf");
    sessionStorage.setItem(FILE_HANDOFF_KEY, JSON.stringify({ name: "legacy.pdf", data: "data:application/pdf;base64,YQ==", createdAt: Date.now() }));
    await storeFileHandoff(fresh, "image-to-pdf");
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).toBeNull();
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual([]);
    await expect(consumeFileHandoffs("image-to-pdf")).resolves.toEqual([fresh]);
  });

  it("clears a pending batch on cancellation or an empty new selection", async () => {
    const file = new File(["a"], "a.pdf");
    await storeFileHandoffs([file], "merge-pdf");
    clearFileHandoffs();
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual([]);
    await storeFileHandoffs([file], "merge-pdf");
    await expect(storeFileHandoffs([], "merge-pdf")).resolves.toBe(false);
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual([]);
  });

  it("expires memory after ten minutes and resets the timer for replacements", async () => {
    vi.useFakeTimers();
    const file = new File(["a"], "a.pdf");
    await storeFileHandoffs([file], "merge-pdf");
    vi.advanceTimersByTime(9 * 60 * 1000);
    await storeFileHandoffs([file], "compress-pdf");
    vi.advanceTimersByTime(60 * 1000);
    await expect(consumeFileHandoffs("compress-pdf")).resolves.toEqual([file]);
    await storeFileHandoffs([file], "merge-pdf");
    vi.advanceTimersByTime(10 * 60 * 1000);
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual([]);
  });

  it("accepts the previous release's single-file session payload exactly once", async () => {
    sessionStorage.setItem(FILE_HANDOFF_KEY, JSON.stringify({
      name: "legacy.pdf", type: "application/pdf", data: "data:application/pdf;base64,aGVsbG8=",
      targetSlug: "merge-pdf", createdAt: Date.now(),
    }));
    await expect(consumeFileHandoffs("compress-pdf")).resolves.toEqual([]);
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).not.toBeNull();
    const [file] = await consumeFileHandoffs("merge-pdf");
    expect(file.name).toBe("legacy.pdf");
    expect(file.type).toBe("application/pdf");
    await expect(readText(file)).resolves.toBe("hello");
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).toBeNull();
  });

  it.each(["not json", "null", JSON.stringify({ name: "a.pdf", data: "data:;base64,%%%", createdAt: Date.now() }), JSON.stringify({ name: "a.pdf", data: "data:,hello" })])("discards malformed legacy payloads safely: %s", async raw => {
    sessionStorage.setItem(FILE_HANDOFF_KEY, raw);
    await expect(consumeFileHandoffs("merge-pdf")).resolves.toEqual([]);
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).toBeNull();
  });

  it("drops stale handoffs instead of pre-filling old files", async () => {
    sessionStorage.setItem(FILE_HANDOFF_KEY, JSON.stringify({
      name: "stale.pdf",
      type: "application/pdf",
      data: "data:application/pdf;base64,Zm9v",
      targetSlug: "compress-pdf",
      createdAt: Date.now() - 11 * 60 * 1000,
    }));

    await expect(consumeFileHandoff("compress-pdf")).resolves.toBeNull();
    expect(sessionStorage.getItem(FILE_HANDOFF_KEY)).toBeNull();
  });

  it.each(["generic", "simple"])("loads every same-named file once into %s under StrictMode", async kind => {
    const files = [new File(["first"], "same.pdf"), new File(["other"], "same.pdf")];
    await storeFileHandoffs(files, "flatten-pdf");
    const ui = kind === "generic"
      ? createElement(GenericUI, { toolName: "Flatten PDF", outputLabel: "flattened.pdf", accepts: ".pdf", slug: "flatten-pdf" })
      : createElement(SimpleConvertUI, { label: "Flatten PDF", outputFilename: "flattened.pdf", outputExt: "pdf", acceptFileTypes: ".pdf", description: "Flatten forms", slug: "flatten-pdf" });
    render(createElement(StrictMode, null, ui));
    await waitFor(() => expect(screen.getAllByText("same.pdf")).toHaveLength(2));
    await expect(consumeFileHandoffs("flatten-pdf")).resolves.toEqual([]);
  });

  it.each(["generic", "simple"])("reports the exact overflow instead of silently omitting files in %s", async kind => {
    const files = Array.from({ length: 27 }, (_, i) => new File([String(i)], `selection-${i}.pdf`));
    await storeFileHandoffs(files, "flatten-pdf");
    const ui = kind === "generic"
      ? createElement(GenericUI, { toolName: "Flatten PDF", outputLabel: "flattened.pdf", accepts: ".pdf", slug: "flatten-pdf" })
      : createElement(SimpleConvertUI, { label: "Flatten PDF", outputFilename: "flattened.pdf", outputExt: "pdf", acceptFileTypes: ".pdf", description: "Flatten forms", slug: "flatten-pdf" });
    render(createElement(StrictMode, null, ui));
    await waitFor(() => expect(screen.getByText(/2 files were not added because the queue holds 25 files/)).toBeInTheDocument());
    expect(screen.getAllByText(/^selection-\d+\.pdf$/)).toHaveLength(25);
  });

  it("uses MultiFileUI's public handoff slug instead of its API endpoint", async () => {
    const files = [new File(["a"], "a.pdf"), new File(["b"], "b.pdf")];
    await storeFileHandoffs(files, "public-merge-route");
    render(createElement(StrictMode, null, createElement(MultiFileUI, {
      endpoint: "/internal-merge", handoffSlug: "public-merge-route", accepts: ".pdf", outputFilename: "merged.pdf", fileLabel: "PDFs",
    })));
    await waitFor(() => expect(screen.getByText("a.pdf")).toBeInTheDocument());
    expect(screen.getByText("b.pdf")).toBeInTheDocument();
  });
});
