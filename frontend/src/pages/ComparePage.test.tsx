import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ComparePage from "./ComparePage";
import { comparisons } from "@/data/comparisons";

describe("Sourced product comparisons", () => {
  it("preserves published routes and attaches every feature to a listed primary source", () => {
    expect(comparisons.map(item => item.slug).sort()).toEqual(["ilovepdf", "smallpdf", "adobe-acrobat", "sejda", "pdf24", "foxit", "lightpdf", "stirling-pdf", "dochub", "pdfescape", "nitro-pdf", "tinywow", "ihatepdf", "remove-bg"].sort());
    for (const item of comparisons) {
      expect(item.chooseCompetitor.length).toBeGreaterThan(0);
      expect(item.tradeoffs.length).toBeGreaterThan(0);
      expect(item.reviewedAt).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(item.sources.length).toBeGreaterThan(0);
      for (const feature of item.features) expect(item.sources.map(source => source.url)).toContain(feature.sourceUrl);
      for (const source of item.sources) expect(new URL(source.url).protocol).toBe("https:");
    }
  });

  it("filters the real directory and clears an empty search without losing routes", async () => {
    render(<MemoryRouter><ComparePage/></MemoryRouter>);
    const search = screen.getByRole("searchbox", { name: "Search comparisons" });
    await userEvent.type(search, "Smallpdf");
    expect(await screen.findByRole("link", { name: "Read PrivaTools vs Smallpdf" })).toHaveAttribute("href", "/compare/smallpdf");
    expect(screen.queryByRole("link", { name: "Read PrivaTools vs iLovePDF" })).not.toBeInTheDocument();
    await userEvent.clear(search);
    await userEvent.type(search, "no-matching-product");
    await userEvent.click(await screen.findByRole("button", { name: "Show all comparisons" }));
    expect(screen.getAllByRole("link", { name: /^Read PrivaTools vs/ })).toHaveLength(14);
    await userEvent.click(screen.getByRole("button", { name: "Everyday PDF" }));
    expect(screen.getAllByRole("link", { name: /^Read PrivaTools vs/ })).toHaveLength(comparisons.filter(item => item.category === "Everyday PDF").length);
  });

  it("renders competitor benefits, editorial disclosure and directly linked evidence", () => {
    render(<MemoryRouter><ComparePage competitorSlug="ihatepdf"/></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("ihatepdf");
    const choice = screen.getByRole("region", { name: "Reasons to choose each product" });
    expect(within(choice).getByRole("heading", { name: /Consider ihatepdf/ })).toBeInTheDocument();
    expect(screen.getAllByText(/Gemini/).length).toBeGreaterThan(0);
    expect(screen.getByText(/self-hostable on your own infrastructure/)).toBeInTheDocument();
    expect(screen.getByText(/pricing, access and performance were not benchmarked/)).toBeInTheDocument();
    const sources = screen.getByRole("region", { name: "Official sources." });
    for (const source of comparisons.find(item => item.slug === "ihatepdf")!.sources) expect(within(sources).getByRole("link", { name: new RegExp(source.label) })).toHaveAttribute("href", source.url);
  });

  it("links the remove.bg decision to a real tool and dated migration guidance", () => {
    render(<MemoryRouter><ComparePage competitorSlug="remove-bg"/></MemoryRouter>);
    expect(screen.getByText(/does not specify a shutdown date/)).toBeInTheDocument();
    const related = screen.getByRole("navigation", { name: "Related tools and guides" });
    expect(within(related).getByRole("link", { name: "Try Background Remover" })).toHaveAttribute("href", "/tools/remove-background");
    expect(within(related).getByRole("link", { name: "Plan a background-removal workflow" })).toHaveAttribute("href", "/blog/remove-bg-canva-alternative");
    expect(within(related).getByRole("link", { name: "Choose the processing engine" })).toHaveAttribute("href", "/blog/remove-background-without-uploading");
  });
});
