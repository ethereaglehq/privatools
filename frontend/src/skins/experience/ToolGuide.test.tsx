import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToolGuide } from "./ToolGuide";

vi.mock("@/lib/tool-guide", () => ({ loadToolGuide: vi.fn(async (slug: string) => slug === "merge-pdf"
  ? { howto: [{ name: "Add PDF files", text: "Drop two or more PDFs." }, { name: "Merge", text: "Download the combined file." }], faq: [{ q: "Is there a limit?", a: "Server capacity limits apply to each request." }] }
  : null) }));
vi.mock("@/data/tool-blog-links.json", () => ({ default: { "merge-pdf": [{ slug: "merge-pdf-files-online-free", title: "How to merge PDF files in the right order" }] } }));
// The blog module is article HTML for every post. A tool page reads the
// generated index above, so evaluating this factory at all is the regression.
const blogModuleLoaded = vi.hoisted(() => vi.fn());
vi.mock("@/data/blog", () => { blogModuleLoaded(); return { postsForTool: () => [] }; });
afterEach(cleanup);

describe("ToolGuide", () => {
  it("renders visible steps, questions and guide links for the tool", async () => {
    await act(async () => { render(<ToolGuide slug="merge-pdf" name="Merge PDF" />); });
    expect(screen.getByRole("heading", { level: 2, name: "How to use Merge PDF" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map(item => item.textContent)).toEqual(expect.arrayContaining([expect.stringContaining("Add PDF files")]));
    expect(screen.getByRole("heading", { level: 3, name: "Is there a limit?" })).toBeVisible();
    expect(screen.getByText("Server capacity limits apply to each request.")).toBeVisible();
    // The index is its own chunk and can arrive after act() has returned, so wait for it.
    expect(await screen.findByRole("link", { name: /How to merge PDF files in the right order/ })).toHaveAttribute("href", "/blog/merge-pdf-files-online-free");
    expect(document.querySelector("details")).toBeNull();
  });
  it("takes its guide links from the generated index without loading the blog module", async () => {
    await act(async () => { render(<ToolGuide slug="merge-pdf" name="Merge PDF" />); });
    // Wait for the links first: until they render the import chain is still
    // running and "not loaded" would pass without proving anything.
    expect(await screen.findByRole("heading", { level: 2, name: "Mentioned in our guides" })).toBeVisible();
    expect(blogModuleLoaded).not.toHaveBeenCalled();
  });
  it("renders nothing for a tool without a guide", async () => {
    const { container } = render(<ToolGuide slug="unknown" name="Unknown" />);
    await act(async () => {});
    expect(container).toBeEmptyDOMElement();
  });
  it("marks the steps list as an accessible list with stable per-step ids", async () => {
    await act(async () => { render(<ToolGuide slug="merge-pdf" name="Merge PDF" />); });
    const steps = document.querySelector("ol");
    // The steps <ol> has its list styling removed by CSS, which strips the
    // implicit "list" role in some browsers/AT — role="list" restores it.
    expect(steps).toHaveAttribute("role", "list");
    const items = steps!.querySelectorAll("li");
    expect(items[0]).toHaveAttribute("id", "step-1");
    expect(items[1]).toHaveAttribute("id", "step-2");
  });
});
