import { useReverification } from "@clerk/react";
import { useCallback } from "react";
import { AccountSecurityError } from "./securityActions";

export type AccountSecurityRunner = <T>(action: () => Promise<T>) => Promise<T>;
export const runAccountAction: AccountSecurityRunner = action => action();

/** Mounted only under ClerkProvider. A server hint is never a successful mutation. */
export function useAccountReverification(): AccountSecurityRunner {
    const verify = useReverification((action: () => Promise<void>) => action());
    return useCallback(async <T,>(action: () => Promise<T>): Promise<T> => {
        let completed = false;
        let value: T | undefined;
        await verify(async () => {
            // Calling before any await also preserves the initial WebAuthn click.
            value = await action();
            completed = true;
        });
        // The installed SDK can return a second reverification hint after retry.
        if (!completed) throw new AccountSecurityError("verification_incomplete");
        return value as T;
    }, [verify]);
}
