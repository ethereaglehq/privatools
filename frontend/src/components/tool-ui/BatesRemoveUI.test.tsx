/**
 * What Remove Bates Numbers tells the visitor after a run.
 *
 * The server answers with how many stamps left the file (X-Bates-Removed) and
 * how many it found but could not take out (X-Bates-Remaining). The page read
 * only the first and then said the text was gone from the file, so a stamp
 * redaction cannot reach was reported as removed to someone about to share
 * the document.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ upload: vi.fn(), download: vi.fn() }));
vi.mock("@/lib/api", async (original) => ({
    ...(await original<object>()),
    uploadFile: mocks.upload,
    downloadBlob: mocks.download,
}));

import { BatesRemoveUI } from "./BatesRemoveUI";

beforeEach(() => {
    mocks.upload.mockReset();
    mocks.download.mockReset();
});

function answer(removed: number, remaining: number): Response {
    return new Response(new Blob(["%PDF-1.7"]), {
        headers: { "X-Bates-Removed": String(removed), "X-Bates-Remaining": String(remaining) },
    });
}

/** Runs the tool on one file per answer and returns the result's heading. */
async function run(...answers: Response[]) {
    for (const a of answers) mocks.upload.mockResolvedValueOnce(a);
    const view = render(<BatesRemoveUI />);
    const files = answers.map((_, i) => new File(["%PDF-1.7"], `production-${i + 1}.pdf`, { type: "application/pdf" }));
    fireEvent.change(view.container.querySelector("input[type=file]")!, { target: { files } });
    fireEvent.click(screen.getByRole("button", { name: /Remove Bates numbers/ }));
    return screen.findByRole("heading", { level: 2 }, { timeout: 5000 });
}

describe("Remove Bates Numbers' result", () => {
    it("says a stamp is still in the file instead of calling it gone", async () => {
        const heading = await run(answer(2, 1));
        expect(heading).toHaveTextContent(/^1 stamp could not be removed$/);
        expect(screen.getByText(/is still in the file/)).toHaveTextContent(/2 other stamps were removed/);
        expect(screen.queryByText(/gone from the file/)).toBeNull();
        expect(screen.queryByText("Bates removed")).toBeNull();
    });

    it("adds up what is left across files", async () => {
        const heading = await run(answer(1, 0), answer(0, 2));
        expect(heading).toHaveTextContent(/^2 stamps could not be removed/);
        expect(screen.getByText(/are still in the files/)).toHaveTextContent(/1 other stamp was removed/);
        expect(screen.queryByText(/gone from the file/)).toBeNull();
    });

    it("claims no removal when none was removed", async () => {
        const heading = await run(answer(0, 3));
        expect(heading).toHaveTextContent(/^3 stamps could not be removed$/);
        expect(screen.queryByText(/other stamps? w(as|ere) removed/)).toBeNull();
    });

    it("says the stamps are gone when every one left the file", async () => {
        const heading = await run(answer(3, 0));
        expect(heading).toHaveTextContent(/^3 stamps removed$/);
        expect(screen.getByText(/the text is gone from the file/)).toBeInTheDocument();
    });

    it("says nothing matched when nothing was found", async () => {
        const heading = await run(answer(0, 0));
        expect(heading).toHaveTextContent("No Bates numbers found");
    });
});
