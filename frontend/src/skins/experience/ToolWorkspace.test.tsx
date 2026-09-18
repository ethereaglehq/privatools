import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ToolWorkspace } from "./ToolWorkspace";

vi.mock("../daylight/consumer/ConsumerChrome", () => ({ FavoriteButton: () => null }));
vi.mock("./ToolGuide", () => ({ ToolGuide: ({ slug }: { slug: string }) => <div data-testid="guide">{slug}</div> }));
afterEach(cleanup);

describe("tool processing disclosure", () => {
  it("gives Background Remover a browser/server choice and explains the default upload", async () => {
    await act(async () => { render(<ToolWorkspace tool={{ slug: "remove-background", name: "Background Remover", description: "Make a cutout", category: "image" }} categoryLabel="Images" related={[]} onFindTool={() => undefined}><div>Engine selector</div></ToolWorkspace>); });
    expect(screen.getByText("Browser or server · your choice")).toBeInTheDocument();
    expect(screen.queryByText("Temporary server processing")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "How it works" }));
    expect(screen.getByText(/default server engine uploads images/)).toBeInTheDocument();
    expect(screen.getByText(/Both options work without an account or an AI provider key/)).toBeInTheDocument();
  });
  it("keeps an ordinary server tool’s disclosure unchanged", async () => {
    await act(async () => { render(<ToolWorkspace tool={{ slug: "compress-pdf", name: "Compress PDF", description: "A smaller file", category: "pdf" }} categoryLabel="PDF" related={[]} onFindTool={() => undefined}><div>File picker</div></ToolWorkspace>); });
    expect(screen.getByText("Temporary server processing")).toBeInTheDocument();
    expect(screen.queryByText("Browser or server · your choice")).not.toBeInTheDocument();
    expect(screen.getByTestId("guide")).toHaveTextContent("compress-pdf");
    expect(document.querySelector(".tw-questions")).toBeNull();
  });
});

describe("tool page heading", () => {
  it("uses the search title as the page heading", async () => {
    await act(async () => { render(<ToolWorkspace tool={{ slug: "compress-pdf", name: "Compress PDF", seoTitle: "Compress PDF Online Free – Shrink Files, Keep Quality", description: "A smaller file", category: "pdf" }} categoryLabel="PDF" related={[]} onFindTool={() => undefined}><div>File picker</div></ToolWorkspace>); });
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Compress PDF Online Free – Shrink Files, Keep Quality");
  });
});
