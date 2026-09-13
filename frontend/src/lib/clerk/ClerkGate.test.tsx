import { cleanup, render } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import ClerkGate from "./ClerkGate";
const mark = vi.hoisted(() => vi.fn());
vi.mock("@clerk/react", () => ({ ClerkProvider: ({ children }: { children: ReactNode }) => children }));
vi.mock("./ClerkBridge", () => ({ ClerkBridge: () => null }));
vi.mock("./instance", () => ({ markClerkLoadFailed: mark }));
afterEach(() => { cleanup(); mark.mockClear(); });
it("reports a blocked Clerk script from its non-bubbling resource error", () => {
  render(<ClerkGate publishableKey="synthetic"><div>Account</div></ClerkGate>);
  const script = document.createElement("script");
  script.src = "https://identity.example.test/npm/@clerk/clerk-js@6/dist/clerk.browser.js";
  document.body.append(script); script.dispatchEvent(new Event("error"));
  expect(mark).toHaveBeenCalledOnce(); script.remove();
});
it("does not mistake other failed resources for a blocked sign-in service", () => {
  render(<ClerkGate publishableKey="synthetic"><div>Account</div></ClerkGate>);
  const script = document.createElement("script"); script.src = "/unrelated.js";
  document.body.append(script); script.dispatchEvent(new Event("error"));
  expect(mark).not.toHaveBeenCalled(); script.remove();
});
