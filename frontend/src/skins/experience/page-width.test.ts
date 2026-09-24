import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import postcss, { type AtRule, type Container, type Rule } from "postcss";
import { afterEach, describe, expect, it } from "vitest";

/*
 * Long-form pages must fit the screen from 320px up. jsdom does no layout, so
 * these tests read every stylesheet in the app and check the declarations
 * whose selectors reach the elements that decide the widths, in a DOM with the
 * pages' real structure. The rule that matters is not always in the
 * component's own stylesheet. The browser check measures scroll width and text
 * edges at 320, 390, 768 and 1280px.
 */
const SRC = resolve(__dirname, "../..");
const files = readdirSync(SRC, { recursive: true, encoding: "utf8" });
const sheets = files.filter(file => file.endsWith(".css")).map(file => ({ file, root: postcss.parse(readFileSync(join(SRC, file), "utf8")) }));
const EXPERIENCES = ["air", "play"] as const;

type Found = { rule: Rule; where: string; value: string };

/** The at-rules around a rule, innermost last. */
function context(rule: Rule): AtRule[] {
  const out: AtRule[] = [];
  for (let parent: Container | undefined = rule.parent; parent && parent.type !== "root"; parent = parent.parent as Container | undefined) {
    if (parent.type === "atrule") out.unshift(parent as AtRule);
  }
  return out;
}

/** Declarations of `property` in on-screen rules with a selector that matches `element` in the current document. */
function reaching(element: Element, property: RegExp): Found[] {
  const found: Found[] = [];
  for (const { file, root } of sheets) {
    root.walkDecls(property, decl => {
      const rule = decl.parent as Rule;
      if (rule?.type !== "rule") return;
      const at = context(rule);
      if (at.some(a => a.name === "media" && /^\s*print\b/.test(a.params))) return;
      for (const selector of rule.selectors) {
        let hit = false;
        try { hit = element.matches(selector); } catch { /* pseudo-elements match no element */ }
        if (hit) found.push({ rule, value: decl.value, where: `${file}: ${at.map(a => `@${a.name} ${a.params} `).join("")}${selector} { ${decl.prop}: ${decl.value} }` });
      }
    });
  }
  return found;
}

function mount(experience: string, page: string): void {
  document.documentElement.setAttribute("data-experience", experience);
  document.body.innerHTML = `<div class="dl-root consumer-app"><div class="pt-shell pt-studio-shell"><main id="dl-main" class="pt-main"><div class="pt-page-host">${page}</div></main></div></div>`;
}
const $ = (selector: string): Element => {
  const element = document.querySelector(selector);
  if (!element) throw new Error(`no ${selector}`);
  return element;
};

afterEach(() => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-experience");
});

/** Top-level tracks of a track list, with `repeat()` unwrapped: "235px minmax(0,1fr)" gives ["235px", "minmax(0,1fr)"]. */
function tracks(value: string): string[] {
  const out: string[] = [];
  let depth = 0, current = "";
  for (const ch of `${value.trim()} `) {
    if (ch === "(") depth++;
    if (ch === ")") depth--;
    if (/\s/.test(ch) && depth === 0) {
      if (current) out.push(...(/^repeat\(/.test(current) ? tracks(current.slice(current.indexOf(",") + 1, -1)) : [current]));
      current = "";
    } else current += ch;
  }
  return out;
}

/*
 * The reader behind Privacy, Terms and Security once laid its text out 895px
 * wide on a 390px phone. A bare `1fr` column keeps an automatic minimum, so
 * the contents strip (one row of section buttons) set the column's width, and
 * `overflow:hidden` on the page cut the text off at the screen edge. The
 * clipping also kept the page's scroll width equal to the screen's, so a
 * sideways-scroll check alone passed.
 */
const READER = `<div class="pt-studio-page pt-document-page"><div class="pt-document-layout">
  <aside class="pt-document-contents"><div class="pt-document-contents-label"></div><div class="pt-document-progress"><div></div></div><nav aria-label="Table of contents"><button type="button">Section</button></nav></aside>
  <article class="pt-document-paper"><div class="pt-document-body"></div></article>
</div></div>`;

describe.each(EXPERIENCES)("document reader in %s", experience => {
  it("gives every flexible column a zero minimum, so no content can widen it past the screen", () => {
    mount(experience, READER);
    const columns = [...reaching($(".pt-document-layout"), /^grid-template-columns$/), ...reaching($(".pt-document-contents"), /^grid-template-columns$/)];
    expect(columns.length).toBeGreaterThan(0);
    const unbounded = columns.filter(({ value }) => tracks(value).some(track => /\d*\.?\d+fr\b/.test(track) && !/^minmax\(\s*0(px)?\s*,/.test(track)));
    expect(unbounded.map(found => found.where)).toEqual([]);
  });

  it("lets the contents column shrink below the width of its strip", () => {
    mount(experience, READER);
    const minimums = reaching($(".pt-document-contents"), /^min-width$/);
    expect(minimums.length).toBeGreaterThan(0);
    expect(minimums.filter(found => !/^0(px)?$/.test(found.value)).map(found => found.where)).toEqual([]);
  });

  it("scrolls the contents strip inside itself wherever it is a single row", () => {
    mount(experience, READER);
    const rows = reaching($(".pt-document-contents nav"), /^display$/).filter(found => /flex/.test(found.value));
    const stuck = rows.filter(({ rule }) => !rule.nodes.some(node => node.type === "decl" && (
      (/^overflow(-x)?$/.test(node.prop) && /auto|scroll/.test(node.value)) || (node.prop === "flex-wrap" && /^wrap/.test(node.value)))));
    expect(stuck.map(found => found.where)).toEqual([]);
  });

  it("never clips the page or its text column, which hides overflowing text instead of fitting it", () => {
    mount(experience, READER);
    const clipped = [".pt-document-page", ".pt-document-layout", ".pt-document-paper"]
      .flatMap(selector => reaching($(selector), /^overflow(-x)?$/)).filter(found => /hidden|clip/.test(found.value));
    expect(clipped.map(found => found.where)).toEqual([]);
  });
});

/*
 * Trust, Status, the API page and the comparison directory scrolled sideways
 * at tablet widths. Their header art has a fixed width (185-235px). The slot
 * holding it had a fixed 130px minimum, and on comparison pages a page-wide
 * `min-width:0` reset overrode the slot's minimum, so the slot shrank and the
 * art spilled past the screen.
 */
const WRAPPERS = [...new Set(files.filter(file => file.endsWith(".tsx"))
  .flatMap(file => [...readFileSync(join(SRC, file), "utf8").matchAll(/<StudioPage className="([^"]+)"/g)].map(match => match[1])))];

describe.each(EXPERIENCES)("studio header in %s", experience => {
  it("finds the pages that use a studio header", () => {
    expect(WRAPPERS).toEqual(expect.arrayContaining(["pt-trust-page", "pt-status-page", "pt-api-page", "pt-comparison-page cmp-directory"]));
  });

  it.each(WRAPPERS)("never lets the art's slot on %s become narrower than the art", wrapper => {
    mount(experience, `<div class="pt-studio-page ${wrapper}"><header class="pt-studio-header"><div class="pt-studio-heading"><h1>Title</h1></div><div class="pt-studio-header-visual" aria-hidden="true"><div></div></div></header></div>`);
    const minimums = reaching($(".pt-studio-header-visual"), /^min-width$/);
    expect(minimums.length).toBeGreaterThan(0);
    expect(minimums.filter(found => !/^(min|max|fit)-content$/.test(found.value)).map(found => found.where)).toEqual([]);
  });
});
