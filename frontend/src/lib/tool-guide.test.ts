import { describe, expect, it } from "vitest";
import { loadToolGuide } from "./tool-guide";

describe("loadToolGuide", () => {
  it("loads the exported steps and questions for a registered slug", async () => {
    const guide = await loadToolGuide("merge-pdf");
    expect(guide?.howto.length).toBeGreaterThan(1);
    expect(guide?.howto[0]).toEqual(expect.objectContaining({ name: expect.any(String), text: expect.any(String) }));
    expect(guide?.faq[0]).toEqual(expect.objectContaining({ q: expect.any(String), a: expect.any(String) }));
  });
  it("resolves null for an unknown slug instead of throwing", async () => {
    await expect(loadToolGuide("../secret")).resolves.toBeNull();
    await expect(loadToolGuide("not-a-tool")).resolves.toBeNull();
  });
});
