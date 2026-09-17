import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PrivacyPage from "./PrivacyPage";
import { readAnalyticsPrivacyPreference, setAnalyticsOptOut } from "@/lib/analyticsPrivacy";

beforeEach(() => {
  localStorage.clear();
  setAnalyticsOptOut(false);
  Object.defineProperty(navigator, "doNotTrack", { configurable: true, value: undefined });
  Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: false });
  vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
});
afterEach(() => {
  cleanup(); vi.restoreAllMocks();
  Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: false });
  setAnalyticsOptOut(false); localStorage.clear();
});

describe("Privacy disclosures match the hosted runtime", () => {
  it("describes Clerk identity, temporary cleanup, local storage and real provider data paths", () => {
    const { container } = render(<PrivacyPage/>);
    expect(screen.getByRole("heading", { name: "4. Optional Accounts" })).toBeInTheDocument();
    expect(screen.getByText(/Clerk manages the hosted site’s identity/)).toBeInTheDocument();
    expect(screen.getByText(/Security or verification messages may be sent to your email address/)).toBeInTheDocument();
    expect(screen.getByText(/A background sweep also removes older files/)).toBeInTheDocument();
    expect(screen.getByText(/does not clear browser-local Vault items/)).toBeInTheDocument();
    expect(screen.getByText(/BYOK requests go from your browser to the provider/)).toBeInTheDocument();
    expect(screen.getByText(/Background Remover’s U²-Net-P model and runtime are served from this site/)).toBeInTheDocument();
    const text = container.textContent || "";
    for (const stale of ["scrypt hash", "We do not send email", "free, unlimited and anonymous", "less than one second", "We never read, analyze", "Since we collect no user data", "Once deleted, they are unrecoverable"]) expect(text).not.toContain(stale);
  });

  it("scopes analytics exclusions and explains each enabled and disabled collection path", () => {
    const { container } = render(<PrivacyPage/>);
    expect(screen.getByText("These exclusions describe analytics.")).toBeInTheDocument();
    expect(screen.getByText(/Scroll depth, outbound-link clicks and supported embedded-video engagement/)).toBeInTheDocument();
    expect(screen.getByText(/destination URL and domain/)).toBeInTheDocument();
    expect(screen.getByText(/Form interactions, file downloads, site search and browser-history page views/)).toBeInTheDocument();
    expect(screen.getByText(/automatic detection and snippet-based collection are disabled/)).toBeInTheDocument();
    expect(container).toHaveTextContent("without URL queries or fragments");
    expect(container).toHaveTextContent("Analytics is on by default");
    expect(container).toHaveTextContent("tool you run");
    expect(container).not.toHaveTextContent("Do Not Track");
    expect(container).not.toHaveTextContent("regional policy");
    expect(screen.getByRole("link", { name: "Google’s event and parameter documentation" })).toHaveAttribute("href", "https://support.google.com/analytics/answer/9216061?hl=en");
  });

  it("shows analytics on by default and lets a visitor turn it off and back on", () => {
    render(<PrivacyPage/>);
    const control = screen.getByRole("switch", { name: "Allow Google Analytics" });
    expect(control).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText(/Google Analytics is on in this browser/)).toBeInTheDocument();
    fireEvent.click(control);
    expect(control).toHaveAttribute("aria-checked", "false");
    expect(readAnalyticsPrivacyPreference()).toEqual({ localOptOut: true, effectiveDisabled: true });
    expect(screen.getByText(/Google Analytics is off in this browser/)).toBeInTheDocument();
    fireEvent.click(control);
    expect(control).toHaveAttribute("aria-checked", "true");
    expect(readAnalyticsPrivacyPreference()).toEqual({ localOptOut: false, effectiveDisabled: false });
  });

  it("does not let a browser privacy signal override the default or lock the switch", () => {
    Object.defineProperty(navigator, "globalPrivacyControl", { configurable: true, value: true });
    Object.defineProperty(navigator, "doNotTrack", { configurable: true, value: "1" });
    render(<PrivacyPage/>);
    const control = screen.getByRole("switch", { name: "Allow Google Analytics" });
    expect(control).toBeEnabled();
    expect(control).toHaveAttribute("aria-checked", "true");
    expect(screen.queryByText(/privacy signal/)).not.toBeInTheDocument();
  });
});
