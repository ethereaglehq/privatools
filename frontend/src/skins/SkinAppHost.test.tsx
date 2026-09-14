import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { BrowserRouter, useLocation } from "react-router-dom";
import { SkinAppHost } from "./SkinAppHost";

vi.mock("./extensions/daylight", () => ({ default: function TestDaylight() {
  const location = useLocation();
  return <><a href="/tools">Tools</a><a href="/pipeline">Pipeline</a><a href="/batch">Batch</a>
    <a href="/tools?cat=image">Images</a><a href="/tools" target="_blank">New tab</a>
    <output aria-label="Current route">{location.pathname + location.search}</output></>;
} }));
vi.mock("@/components/BackendStatusBanner", () => ({ BackendStatusBanner: () => null }));
vi.mock("@/components/BatchResumeBanner", () => ({ BatchResumeBanner: () => null }));

beforeEach(() => {
  window.history.replaceState(null, "", "/ai");
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("opens Tools, Pipeline and Batch at clean paths and updates React Router", () => {
  render(<BrowserRouter><SkinAppHost /></BrowserRouter>);
  for (const [label, path] of [["Tools", "/tools"], ["Pipeline", "/pipeline"], ["Batch", "/batch"]]) {
    fireEvent.click(screen.getByText(label));
    expect(window.location.pathname).toBe(path);
    expect(window.location.hash).toBe("");
    expect(screen.getByLabelText("Current route").textContent).toBe(path);
  }
});

it("keeps category queries during in-app navigation", () => {
  render(<BrowserRouter><SkinAppHost /></BrowserRouter>);
  fireEvent.click(screen.getByText("Images"));
  expect(window.location.pathname + window.location.search).toBe("/tools?cat=image");
  expect(screen.getByLabelText("Current route").textContent).toBe("/tools?cat=image");
});

it("leaves modified clicks and new-tab links to the browser", () => {
  render(<BrowserRouter><SkinAppHost /></BrowserRouter>);
  // Cancel jsdom's unimplemented navigation after checking the app left it alone.
  const browserDefault = (event: MouseEvent) => {
    expect(event.defaultPrevented).toBe(false);
    event.preventDefault();
  };
  document.addEventListener("click", browserDefault);
  try {
    fireEvent.click(screen.getByText("Tools"), { ctrlKey: true });
    fireEvent.click(screen.getByText("New tab"));
  } finally { document.removeEventListener("click", browserDefault); }
  expect(window.location.pathname).toBe("/ai");
});
