import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToolGuide } from "./ToolGuide";

vi.mock("@/lib/tool-guide", () => ({ loadToolGuide: vi.fn(async (slug: string) => slug === "merge-pdf"
  ? { howto: [{ name: "Add PDF files", text: "Drop two or more PDFs." }, { name: "Merge", text: "Download the combined file." }], faq: [{ q: "Is there a limit?", a: "Server capacity limits apply to each request." }] }
  : null) }));
vi.mock("@/data/blog", () => ({ postsForTool: (slug: string) => slug === "merge-pdf" ? [{ slug: "merge-pdf-files-online-free", title: "How to merge PDF files in the right order" }] : [] }));
afterEach(cleanup);

describe("ToolGuide", () => {
  it("renders visible steps, questions and guide links for the tool", async () => {
    await act(async () => { render(<ToolGuide slug="merge-pdf" name="Merge PDF" />); });
    expect(screen.getByRole("heading", { level: 2, name: "How to use Merge PDF" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map(item => item.textContent)).toEqual(expect.arrayContaining([expect.stringContaining("Add PDF files")]));
    expect(screen.getByRole("heading", { level: 3, name: "Is there a limit?" })).toBeVisible();
    expect(screen.getByText("Server capacity limits apply to each request.")).toBeVisible();
    expect(screen.getByRole("link", { name: /How to merge PDF files in the right order/ })).toHaveAttribute("href", "/blog/merge-pdf-files-online-free");
    expect(document.querySelector("details")).toBeNull();
  });
  it("renders nothing for a tool without a guide", async () => {
    const { container } = render(<ToolGuide slug="unknown" name="Unknown" />);
    await act(async () => {});
    expect(container).toBeEmptyDOMElement();
  });
});
