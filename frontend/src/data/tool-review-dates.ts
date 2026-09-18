// The `lastReviewed` field on each tool's registry entry (tools.ts,
// non-pdf-tools.ts) is the authoritative last-reviewed date — it also
// drives the sitemap lastmod on the backend. This module used to carry its
// own mirrored dict, which could and did drift from the registries; now it
// just looks the date up. Returns undefined for a slug in neither registry
// (both current callers only render the "Last reviewed" line when defined).
import { toolBySlug } from "@/data/tools";
import { nonPdfToolBySlug } from "@/data/non-pdf-tools";

export function getToolLastReviewed(slug: string): string | undefined {
  return toolBySlug[slug]?.lastReviewed ?? nonPdfToolBySlug[slug]?.lastReviewed;
}

export function formatReviewedDate(isoDate: string) {
  const date = new Date(`${isoDate}T00:00:00Z`);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}
