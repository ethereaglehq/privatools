import { describe, expect, it } from "vitest";
import { toolSeo } from "./tool-seo";

describe("toolSeo", () => {
  it("uses the registry search title for both the tab and the heading", () => {
    const seo = toolSeo({ name: "Merge PDF", seoTitle: "Merge PDF Files Online Free – Combine PDFs Privately", metaDescription: "Combine PDFs in order. Free, no sign-up." });
    expect(seo.title).toBe("Merge PDF Files Online Free – Combine PDFs Privately");
    expect(seo.h1).toBe("Merge PDF Files Online Free – Combine PDFs Privately");
    expect(seo.description).toBe("Combine PDFs in order. Free, no sign-up.");
  });
  it("falls back to the tool name for registries without search copy", () => {
    const seo = toolSeo({ name: "Merge PDF", longDescription: "Long text." });
    expect(seo).toEqual({ title: "Merge PDF — Free Online | PrivaTools", h1: "Merge PDF", description: "Long text." });
  });
});
