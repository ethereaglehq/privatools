import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PrivacyPage from "./PrivacyPage";
import TermsPage from "./TermsPage";
import SecurityPage from "./SecurityPage";
import { policySectionUrl, readPolicySection } from "@/lib/policyNavigation";

const scrollIntoView = vi.fn();
const cases = [
  { path: "/privacy", Page: PrivacyPage, id: "third-party", button: "6. Third-Party Services" },
  { path: "/terms", Page: TermsPage, id: "no-warranty", button: "5. No Warranty" },
  { path: "/security", Page: SecurityPage, id: "threat-model", button: "2. Threat Model" },
];

beforeEach(() => {
  scrollIntoView.mockClear();
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scrollIntoView });
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  Object.defineProperty(window, "scrollY", { configurable: true, value: 0 });
  window.history.replaceState(null, "", "/");
});

describe.each(cases)("$path section navigation", ({ path, Page, id, button }) => {
  it("keeps a hash-host route and router state when using the table of contents", () => {
    const routerState = { idx: 3, key: "existing-location", usr: { source: "footer" } };
    window.history.replaceState(routerState, "", `/?appearance=dark#${path}`);
    render(<MemoryRouter><Page /></MemoryRouter>);
    fireEvent.click(screen.getAllByRole("button", { name: button })[0]);
    expect(window.location.pathname).toBe("/");
    expect(window.location.hash).toBe(`#${path}`);
    expect(new URLSearchParams(window.location.search).get("section")).toBe(id);
    expect(new URLSearchParams(window.location.search).get("appearance")).toBe("dark");
    expect(window.history.state).toEqual(routerState);
    expect(document.getElementById(id)?.contains(document.activeElement)).toBe(true);
  });

  it.each(["path", "hash"])("restores a %s permalink on a fresh mount", async host => {
    const href = host === "path" ? `${path}?section=${id}` : `/?section=${id}#${path}`;
    window.history.replaceState(null, "", href);
    render(<MemoryRouter><Page /></MemoryRouter>);
    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
    expect(scrollIntoView.mock.instances[0]).toBe(document.getElementById(id));
    expect(window.location.hash).toBe(host === "path" ? "" : `#${path}`);
    // Restoring a shared URL does not steal keyboard focus from the page.
    expect(document.activeElement).toBe(document.body);
  });

  it("honors reduced motion for section and back-to-top actions", () => {
    vi.spyOn(window, "matchMedia").mockReturnValue({ matches: true } as MediaQueryList);
    Object.defineProperty(window, "scrollY", { configurable: true, value: 1000 });
    window.history.replaceState(null, "", path);
    render(<MemoryRouter><Page /></MemoryRouter>);
    fireEvent.click(screen.getAllByRole("button", { name: button })[0]);
    expect(scrollIntoView).toHaveBeenLastCalledWith({ behavior: "auto", block: "start" });
    fireEvent.click(screen.getByRole("button", { name: /^(Scroll|Back) to top$/ }));
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: "auto" });
  });
});

describe("policy section URLs", () => {
  const sections = [{ id: "third-party" }];
  it("supports both query locations and ordinary document fragments", () => {
    expect(readPolicySection(sections, "https://privatools.example/privacy?section=third-party")).toBe("third-party");
    expect(readPolicySection(sections, "https://privatools.example/#/privacy?section=third-party")).toBe("third-party");
    expect(readPolicySection(sections, "https://privatools.example/privacy#third-party")).toBe("third-party");
    expect(policySectionUrl("third-party", "https://privatools.example/privacy#third-party")).toBe("https://privatools.example/privacy?section=third-party");
  });

  it("ignores unknown or malformed fragments", () => {
    expect(readPolicySection(sections, "https://privatools.example/privacy?section=missing")).toBeNull();
    expect(readPolicySection(sections, "https://privatools.example/privacy#%E0%A4%A")).toBeNull();
  });
});
