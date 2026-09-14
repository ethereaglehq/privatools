/** The response headers belong to this path, even after client-side navigation. */
export const documentPath = typeof window === "undefined" ? "/" : window.location.pathname;
