import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OnboardingTour } from "./OnboardingTour";
import { positionTourCard } from "./tour-position";
import { START_TOUR_EVENT } from "@/lib/events";
const scroll = vi.fn();
beforeEach(() => {
  localStorage.clear();
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function () {
    const hidden = (this as HTMLElement).style.display === "none";
    return { x: 20, y: 20, left: 20, top: 20, width: hidden ? 0 : 120, height: hidden ? 0 : 36, right: hidden ? 20 : 140, bottom: hidden ? 20 : 56, toJSON: () => ({}) };
  });
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scroll });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); scroll.mockClear(); });
function fixture(search = true) {
  return render(<MemoryRouter><header className="pt-header"><nav className="pt-top-links">{["tools", "pipeline", "batch", "ai", "vault", "mystuff", "api"].map(id => <a key={id} href={`/${id}`} data-destination={id}>{id}</a>)}</nav><button className="pt-search-trigger" style={search ? {} : { display: "none" }}>Search</button><div className="pt-style-switch"><button>Air</button><button>Play</button></div><button className="pt-theme-toggle">Dark</button></header><button onClick={() => window.dispatchEvent(new Event(START_TOUR_EVENT))}>Quick tour</button><OnboardingTour/></MemoryRouter>);
}
describe("Tour anchored to real controls", () => {
  it("stays closed for returning visitors until they explicitly replay it", async () => {
    localStorage.setItem("privatools_onboarding_done", "1"); fixture();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Quick tour" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("Find your next little helper.");
    expect(document.querySelector('[data-tour-target="tools"]')).toBe(screen.getByRole("link", { name: "tools" }));
    expect(scroll).toHaveBeenCalledWith({ block: "nearest", inline: "center", behavior: "instant" });
  });
  it("moves forward and back over actual anchors, skipping hidden controls", async () => {
    fixture(false); await userEvent.click(screen.getByRole("button", { name: "Quick tour" }));
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(document.querySelector('[data-tour-target="pipeline"]')).toBe(screen.getByRole("link", { name: "pipeline" }));
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemax", "9");
    expect(document.querySelector('[data-tour-target="tools"]')).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(document.querySelector('[data-tour-target="tools"]')).not.toBeNull();
  });
  it("traps focus and Escape restores the replay control", async () => {
    fixture(); const replay = screen.getByRole("button", { name: "Quick tour" });
    await userEvent.click(replay); const next = screen.getByRole("button", { name: "Next" });
    await waitFor(() => expect(next).toHaveFocus());
    await userEvent.tab(); expect(screen.getByRole("button", { name: "Close tour" })).toHaveFocus();
    await userEvent.tab({ shift: true }); expect(next).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(); expect(replay).toHaveFocus();
    expect(localStorage.getItem("privatools_onboarding_done")).toBe("1");
    expect(document.querySelector("[data-tour-target]")).toBeNull();
  });
  it("completes every step without changing saved work", async () => {
    localStorage.setItem("saved-work", "unchanged"); fixture();
    await userEvent.click(screen.getByRole("button", { name: "Quick tour" }));
    for (let step = 0; step < 9; step++) await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Morning Mist and Graphite");
    await userEvent.click(screen.getByRole("button", { name: "All set" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(localStorage.getItem("saved-work")).toBe("unchanged");
  });
  it("does not invent a target when controls are missing", () => {
    render(<MemoryRouter><OnboardingTour/></MemoryRouter>);
    act(() => window.dispatchEvent(new Event(START_TOUR_EVENT)));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
describe("Tour geometry", () => {
  it("fits narrow and short viewports and points toward the target", () => {
    const narrow = positionTourCard({ left: 280, top: 90, width: 30, height: 35 }, { width: 320, height: 640 }, { width: 360, height: 280 });
    expect(narrow).toMatchObject({ left: 12, top: 145, width: 296, side: "below" });
    expect(narrow.left + narrow.width).toBeLessThanOrEqual(308);
    const bottom = positionTourCard({ left: 20, top: 500, width: 60, height: 40 }, { width: 390, height: 640 }, { width: 360, height: 280 });
    expect(bottom.side).toBe("above"); expect(bottom.top).toBe(200);
    const short = positionTourCard(null, { width: 320, height: 240 }, { width: 360, height: 310 });
    expect(short).toMatchObject({ left: 12, top: 12, width: 296, side: "floating" });
  });
});
