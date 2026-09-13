import { afterEach, describe, expect, it, vi } from "vitest";
import { withPathRoutes } from "./withPathRoutes";

class Base {}
// The mixin's public React type intentionally hides its class internals.
const Routed = withPathRoutes(Base) as unknown as new (props: object) => {
  _syncHashFromPath(): void;
  _ensureScopedPath(): boolean;
};

afterEach(() => vi.unstubAllGlobals());

function environment(pathname: string, search = "", hash = "") {
  const location = { pathname, search, hash, href: `https://privatools.me${pathname}${search}${hash}`, replace: vi.fn() };
  const history = { state: { preserved: true }, replaceState: vi.fn() };
  const dispatchEvent = vi.fn();
  vi.stubGlobal("window", { location, history, dispatchEvent });
  return { location, history, dispatchEvent };
}

describe("production path bridge", () => {
  it.each(["/ai", "/api", "/trust", "/account/sign-in", "/account/sign-up", "/account/settings"])("bridges %s without adding browser history", path => {
    const { history, dispatchEvent } = environment(path);
    new Routed({})._syncHashFromPath();
    expect(history.replaceState).toHaveBeenCalledExactlyOnceWith({ preserved: true }, "", "#" + path);
    expect(dispatchEvent).toHaveBeenCalledTimes(1);
  });

  it("loads account settings through a real request so its account CSP applies", () => {
    const { location, history } = environment("/settings/", "?section=appearance");
    new Routed({})._syncHashFromPath();
    expect(location.replace).toHaveBeenCalledExactlyOnceWith("/account/settings?section=appearance");
    expect(history.replaceState).not.toHaveBeenCalled();
  });

  it("preserves an existing in-app route", () => {
    const { history } = environment("/tool/merge-pdf", "", "#/batch");
    new Routed({})._syncHashFromPath();
    expect(history.replaceState).not.toHaveBeenCalled();
  });

  it("turns a programmatic AI hash into a real request without adding another history entry", () => {
    const { location, history } = environment("/", "", "#/tool/image-ocr");
    expect(new Routed({})._ensureScopedPath()).toBe(true);
    expect(location.replace).toHaveBeenCalledExactlyOnceWith("/tools/image-ocr");
    expect(history.replaceState).not.toHaveBeenCalled();
  });

  it("keeps normal and compatible AI programmatic navigation mounted", () => {
    const ordinary = environment("/", "", "#/tool/merge-pdf");
    expect(new Routed({})._ensureScopedPath()).toBe(false);
    expect(ordinary.location.replace).not.toHaveBeenCalled();
    const compatible = environment("/tool/summarize-pdf", "", "#/tool/translate-pdf");
    expect(new Routed({})._ensureScopedPath()).toBe(false);
    expect(compatible.location.replace).not.toHaveBeenCalled();
  });

  it("keeps the tools category query and declines unknown paths", () => {
    const { history } = environment("/tools", "?cat=image");
    new Routed({})._syncHashFromPath();
    expect(history.replaceState).toHaveBeenCalledWith({ preserved: true }, "", "#/tools?cat=image");
    const unknown = environment("/unknown", "?cat=image");
    new Routed({})._syncHashFromPath();
    expect(unknown.history.replaceState).not.toHaveBeenCalled();
  });
});
