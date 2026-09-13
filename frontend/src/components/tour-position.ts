export type Rect = { left: number; top: number; width: number; height: number };

export function positionTourCard(target: Rect | null, viewport: { width: number; height: number }, card: { width: number; height: number }) {
  const margin = 12, gap = 20;
  const width = Math.max(0, Math.min(card.width, viewport.width - margin * 2));
  const height = Math.min(card.height, Math.max(0, viewport.height - margin * 2));
  const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(value, max));
  let left = clamp(target ? target.left + target.width / 2 - width / 2 : (viewport.width - width) / 2, margin, viewport.width - width - margin);
  const below = target ? target.top + target.height + gap : margin;
  const above = target ? target.top - height - gap : margin;
  const side = target && below + height <= viewport.height - margin ? "below" : target && above >= margin ? "above" : target && target.left + target.width + gap + width <= viewport.width - margin ? "right" : target && target.left - gap - width >= margin ? "left" : "floating";
  if (target && side === "right") left = target.left + target.width + gap;
  if (target && side === "left") left = target.left - width - gap;
  const top = side === "below" ? below : side === "above" ? above : side === "left" || side === "right" ? clamp((target?.top ?? 0) - 12, margin, viewport.height - height - margin) : clamp(viewport.height - height - margin, margin, viewport.height - height - margin);
  return { left, top, width, side, arrowLeft: clamp(target ? target.left + target.width / 2 - left : width / 2, 24, width - 24), arrowTop: clamp(target ? target.top + target.height / 2 - top : height / 2, 18, height - 18) };
}
