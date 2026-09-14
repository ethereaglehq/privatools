import { act, render, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import AccountReverificationBridge from "./AccountReverificationBridge";
import type { AccountSecurityRunner } from "@/lib/clerk/useAccountReverification";

vi.mock("@clerk/react", () => ({ useReverification: (callback: (action: () => Promise<void>) => Promise<void>) => callback }));

it("publishes a working verifier to the class controller and clears it on unmount", async () => {
    const ready = vi.fn();
    const view = render(<AccountReverificationBridge onReady={ready} />);
    await waitFor(() => expect(ready).toHaveBeenCalledWith(expect.any(Function)));
    const run: AccountSecurityRunner = ready.mock.calls[0][0];
    const action = vi.fn().mockResolvedValue({ ok: true });
    await act(async () => expect(await run(action)).toEqual({ ok: true }));
    expect(action).toHaveBeenCalledTimes(1);
    view.unmount();
    expect(ready).toHaveBeenLastCalledWith(null);
});
