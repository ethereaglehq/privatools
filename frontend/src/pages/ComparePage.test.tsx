import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ComparePage from "./ComparePage";
import { comparisons, type ProductComparison } from "@/data/comparisons";
import { TOTAL_TOOL_COUNT } from "@/data/site-stats";

const ownCopy = (item: ProductComparison) => [
  item.summary, ...item.overview, ...item.features.flatMap(feature => [feature.label, feature.privatools, feature.competitor]),
  ...item.sections.flatMap(section => [section.heading, ...section.body]), ...item.chooseCompetitor, ...item.choosePrivaTools, ...item.tradeoffs,
];
const wordCount = (texts: string[]) => texts.join(" ").split(/\s+/).filter(Boolean).length;
const sentences = (text: string) => text.split(/(?<=[.!?])\s+/).map(sentence => sentence.trim()).filter(sentence => sentence.split(/\s+/).length >= 12);

describe("Sourced product comparisons", () => {
  it("preserves published routes and attaches every feature to a listed primary source", () => {
    expect(comparisons.map(item => item.slug).sort()).toEqual(["ilovepdf", "smallpdf", "adobe-acrobat", "sejda", "pdf24", "foxit", "lightpdf", "stirling-pdf", "dochub", "pdfescape", "nitro-pdf", "tinywow", "ihatepdf", "remove-bg"].sort());
    const today = new Date().toISOString().slice(0, 10);
    for (const item of comparisons) {
      expect(item.chooseCompetitor.length).toBeGreaterThan(0);
      expect(item.tradeoffs.length).toBeGreaterThan(0);
      expect(item.reviewedAt).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(item.reviewedAt <= today).toBe(true);
      expect(item.sources.length).toBeGreaterThan(0);
      for (const feature of item.features) expect(item.sources.map(source => source.url)).toContain(feature.sourceUrl);
      for (const source of item.sources) expect(new URL(source.url).protocol).toBe("https:");
      for (const link of item.relatedLinks ?? []) expect(link.url).toMatch(/^\/(?!\/)/);
    }
  });

  it("gives every comparison unique search copy within budget", () => {
    const titles = comparisons.map(item => item.title);
    const descriptions = comparisons.map(item => item.description);
    expect(new Set(titles.map(title => title.toLowerCase())).size).toBe(titles.length);
    expect(new Set(descriptions.map(description => description.toLowerCase())).size).toBe(descriptions.length);
    for (const item of comparisons) {
      expect(item.title.startsWith(`PrivaTools vs ${item.name}`), item.title).toBe(true);
      expect(item.title.length, item.title).toBeLessThanOrEqual(60);
      expect(item.description.length, item.description).toBeGreaterThanOrEqual(120);
      expect(item.description.length, item.description).toBeLessThanOrEqual(160);
      expect(item.description.endsWith("."), item.description).toBe(true);
    }
  });

  it("keeps each comparison substantive and distinct instead of a shared template", () => {
    const seen = new Map<string, string>();
    for (const item of comparisons) {
      expect(item.overview.length, item.slug).toBeGreaterThanOrEqual(2);
      expect(item.features.length, item.slug).toBeGreaterThanOrEqual(6);
      expect(item.sections.length, item.slug).toBeGreaterThanOrEqual(2);
      expect(item.chooseCompetitor.length, item.slug).toBeGreaterThanOrEqual(3);
      expect(item.choosePrivaTools.length, item.slug).toBeGreaterThanOrEqual(3);
      expect(item.highlights.length, item.slug).toBeGreaterThanOrEqual(2);
      expect(item.highlights.length, item.slug).toBeLessThanOrEqual(3);
      expect(wordCount(ownCopy(item)), item.slug).toBeGreaterThanOrEqual(600);
      // The tool total comes from the registry; a literal drifts (CLAUDE.md).
      expect(ownCopy(item).join(" "), item.slug).not.toMatch(new RegExp(`\\b${TOTAL_TOOL_COUNT}\\b`));
      for (const sentence of ownCopy(item).flatMap(sentences)) {
        const other = seen.get(sentence);
        expect(other === undefined || other === item.slug, `"${sentence}" repeats on ${other} and ${item.slug}`).toBe(true);
        seen.set(sentence, item.slug);
      }
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

  it("lists what sets each product apart in the directory", () => {
    render(<MemoryRouter><ComparePage/></MemoryRouter>);
    for (const item of comparisons) {
      const entry = screen.getByRole("link", { name: `Read PrivaTools vs ${item.name}` });
      for (const point of item.highlights) expect(entry).toHaveTextContent(point);
    }
  });

  it("renders both choices, the dated facts and directly linked evidence", () => {
    const item = comparisons.find(comparison => comparison.slug === "ihatepdf")!;
    render(<MemoryRouter><ComparePage competitorSlug="ihatepdf"/></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("ihatepdf");
    const choice = screen.getByRole("region", { name: "Reasons to choose each product" });
    expect(within(choice).getByRole("heading", { name: /Choose ihatepdf\.cv/ })).toBeInTheDocument();
    expect(within(choice).getByRole("heading", { name: /Choose PrivaTools/ })).toBeInTheDocument();
    expect(screen.getAllByText(/Gemini/).length).toBeGreaterThan(0);
    expect(screen.getByText(/self-hostable on your own infrastructure/)).toBeInTheDocument();
    expect(screen.getByText(/checked on/)).toBeInTheDocument();
    expect(screen.getByText(/we did not benchmark speed, output quality or accuracy/)).toBeInTheDocument();
    for (const section of item.sections) expect(screen.getByRole("heading", { name: section.heading })).toBeInTheDocument();
    for (const feature of item.features) expect(screen.getByRole("heading", { name: feature.label })).toBeInTheDocument();
    const sources = screen.getByRole("region", { name: "Official sources." });
    for (const source of item.sources) expect(within(sources).getByRole("link", { name: new RegExp(source.label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")) })).toHaveAttribute("href", source.url);
  });

  it("links the remove.bg decision to a real tool and background-removal guidance", () => {
    render(<MemoryRouter><ComparePage competitorSlug="remove-bg"/></MemoryRouter>);
    const related = screen.getByRole("navigation", { name: "Related tools and guides" });
    expect(within(related).getByRole("link", { name: "Try Background Remover" })).toHaveAttribute("href", "/tools/remove-background");
    expect(within(related).getByRole("link", { name: "Plan a background-removal workflow" })).toHaveAttribute("href", "/blog/remove-bg-canva-alternative");
    expect(within(related).getByRole("link", { name: "Choose the processing engine" })).toHaveAttribute("href", "/blog/remove-background-without-uploading");
  });
});
