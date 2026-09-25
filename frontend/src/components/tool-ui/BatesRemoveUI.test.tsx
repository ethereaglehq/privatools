/**
 * What Remove Bates Numbers tells the visitor after a run.
 *
 * The server answers with how many stamps left the file (X-Bates-Removed),
 * how many it found but could not take out (X-Bates-Remaining), and how many
 * other matches for the prefix or suffix it found elsewhere and left in place
 * (X-Bates-Elsewhere). The page read only the first and then said the text was
 * gone from the file, so a stamp redaction cannot reach was reported as
 * removed to someone about to share the document; and a stamp left outside
 * the margins was reported as "No Bates numbers found".
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
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

function answer(removed: number, remaining: number, elsewhere = 0): Response {
    return new Response(new Blob(["%PDF-1.7"]), {
        headers: {
            "X-Bates-Removed": String(removed),
            "X-Bates-Remaining": String(remaining),
            "X-Bates-Elsewhere": String(elsewhere),
        },
    });
}

/** Runs the tool on one file per answer, with `prefix` typed first, and
 *  returns the result's heading. */
async function run(answers: Response[], prefix = "") {
    for (const a of answers) mocks.upload.mockResolvedValueOnce(a);
    const view = render(<BatesRemoveUI />);
    const files = answers.map((_, i) => new File(["%PDF-1.7"], `production-${i + 1}.pdf`, { type: "application/pdf" }));
    fireEvent.change(view.container.querySelector("input[type=file]")!, { target: { files } });
    if (prefix) fireEvent.change(screen.getByLabelText("Prefix"), { target: { value: prefix } });
    fireEvent.click(screen.getByRole("button", { name: /Remove Bates numbers/ }));
    return screen.findByRole("heading", { level: 2 }, { timeout: 5000 });
}

describe("Remove Bates Numbers' result", () => {
    it("says a stamp is still in the file instead of calling it gone", async () => {
        const heading = await run([answer(2, 1)]);
        expect(heading).toHaveTextContent(/^1 stamp could not be removed$/);
        expect(screen.getByText(/is still in the file/)).toHaveTextContent(/2 other stamps were removed/);
        expect(screen.queryByText(/gone from the file/)).toBeNull();
        expect(screen.queryByText("Bates removed")).toBeNull();
    });

    it("adds up what is left across files", async () => {
        const heading = await run([answer(1, 0), answer(0, 2)]);
        expect(heading).toHaveTextContent(/^2 stamps could not be removed/);
        expect(screen.getByText(/are still in the files/)).toHaveTextContent(/1 other stamp was removed/);
        expect(screen.queryByText(/gone from the file/)).toBeNull();
    });

    it("claims no removal when none was removed", async () => {
        const heading = await run([answer(0, 3)]);
        expect(heading).toHaveTextContent(/^3 stamps could not be removed$/);
        expect(screen.queryByText(/other stamps? w(as|ere) removed/)).toBeNull();
    });

    it("says the stamps are gone when every one left the file", async () => {
        const heading = await run([answer(3, 0)]);
        expect(heading).toHaveTextContent(/^3 stamps removed$/);
        expect(screen.getByText(/the text is gone from the file/)).toBeInTheDocument();
    });

    it("says nothing matched when nothing was found", async () => {
        const heading = await run([answer(0, 0)]);
        expect(heading).toHaveTextContent("No Bates numbers found");
        expect(screen.getByText(/top or bottom inch/)).toBeInTheDocument();
    });

    it("says nothing in the file matched the prefix when one was given", async () => {
        const heading = await run([answer(0, 0)], "PROD");
        expect(heading).toHaveTextContent("No Bates numbers found");
        expect(screen.getByText(/Nothing in the file matched the prefix or suffix/)).toBeInTheDocument();
    });

    it("reports matches left in place instead of saying nothing was found", async () => {
        const heading = await run([answer(0, 0, 1)], "PROD");
        expect(heading).toHaveTextContent(/^1 match left in place$/);
        expect(screen.getByText(/found elsewhere in the file/)).toHaveTextContent(/Check before you share/);
        expect(screen.queryByText("No Bates numbers found")).toBeNull();
        expect(screen.queryByText(/gone from the file/)).toBeNull();
    });

    it("says how many stamps went when matches were left in place", async () => {
        const heading = await run([answer(3, 0, 2)], "PROD");
        expect(heading).toHaveTextContent(/^2 matches left in place$/);
        expect(screen.getByText(/found elsewhere in the file/)).toHaveTextContent(/3 stamps in the margins were removed/);
    });

    it("mentions the matches left in place when stamps could not be removed", async () => {
        const heading = await run([answer(2, 1, 1)], "PROD");
        expect(heading).toHaveTextContent(/^1 stamp could not be removed$/);
        expect(screen.getByText(/is still in the file/)).toHaveTextContent(
            /2 other stamps were removed\. 1 more match for the prefix or suffix was found elsewhere in the file/,
        );
    });

    it("names the files in a batch that still hold a stamp or a match", async () => {
        await run([answer(1, 0), answer(0, 1), answer(2, 0, 3)], "PROD");
        const list = screen.getByRole("list", { name: "Files to check" });
        const rows = within(list).getAllByRole("listitem").map(item => item.textContent);
        expect(rows).toEqual(["production-2.pdf1 could not be removed", "production-3.pdf3 left in place"]);
    });

    it("names no files for a single file", async () => {
        await run([answer(0, 1)]);
        expect(screen.queryByRole("list", { name: "Files to check" })).toBeNull();
    });
});
