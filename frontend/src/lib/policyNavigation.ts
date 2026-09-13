/** Section links must not replace the hash used by the site's page router. */
export function policySectionUrl(id: string, href = window.location.href): string {
  const url = new URL(href);
  url.searchParams.set("section", id);
  // Migrate an ordinary document fragment when this page is mounted outside
  // the hash router. Route hashes such as #/privacy remain untouched.
  if (url.hash === `#${id}` || url.hash === `#${encodeURIComponent(id)}`) url.hash = "";
  return url.href;
}

export function readPolicySection(
  sections: ReadonlyArray<{ id: string }>,
  href = window.location.href,
): string | null {
  const url = new URL(href);
  let fragment = "";
  try { fragment = decodeURIComponent(url.hash.slice(1)); } catch { /* malformed fragment */ }
  const hashQuery = fragment.includes("?") ? fragment.slice(fragment.indexOf("?") + 1) : "";
  const candidates = [url.searchParams.get("section"), new URLSearchParams(hashQuery).get("section"), fragment];
  return candidates.find(id => id && sections.some(section => section.id === id)) ?? null;
}

export function rememberPolicySection(id: string) {
  // React Router keeps its history index and location key in history.state.
  window.history.replaceState(window.history.state, "", policySectionUrl(id));
}

export function policyScrollBehavior(): ScrollBehavior {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches
    ? "auto"
    : "smooth";
}

export function focusPolicySection(element: HTMLElement) {
  const heading = element.matches("h1,h2,h3") ? element : element.querySelector<HTMLElement>("h1,h2,h3") ?? element;
  if (!heading.hasAttribute("tabindex")) heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
}
