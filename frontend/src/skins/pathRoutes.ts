/**
 * Public routes recognized by application navigation.
 *
 * Shared by the route shells. Tests compare this registry with App.tsx so new
 * public routes remain reachable through the same navigation helpers.
 */

/** Route prefixes that carry a parameter — `/tool/merge-pdf`, `/blog/some-post`. */
export const PARAM_ROUTE_PREFIXES: readonly string[] = [
    "/tool",
    "/tools",
    "/blog",
    "/compare",
];

/** Routes that stand alone. */
export const EXACT_ROUTES: readonly string[] = [
    "/about",
    "/privacy",
    "/security",
    "/terms",
    "/pipeline",
    "/batch",
    "/status",
    "/support",
    "/account",
    "/my-stuff",
    "/ai",
    "/api",
    "/trust",
    "/settings",
];

/**
 * Route prefixes ordered from most specific to least specific.
 */
export const PATH_ROUTE_PREFIXES: readonly string[] = [
    ...PARAM_ROUTE_PREFIXES,
    ...EXACT_ROUTES,
].slice().sort((a, b) => b.length - a.length);
