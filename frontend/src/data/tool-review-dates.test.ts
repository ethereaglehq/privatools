import { describe, expect, it } from "vitest";
import { getToolLastReviewed } from "./tool-review-dates";
import { toolBySlug } from "@/data/tools";

describe("getToolLastReviewed", () => {
  it("reads the date from the tool registry, not a separate mirror", () => {
    expect(getToolLastReviewed("merge-pdf")).toBe(toolBySlug["merge-pdf"].lastReviewed);
  });

  it("returns undefined for a slug in neither registry", () => {
    expect(getToolLastReviewed("not-a-real-tool-slug")).toBeUndefined();
  });
});
