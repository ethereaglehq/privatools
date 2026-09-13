/**
 * Parks the Clerk instance where non-React code can reach it.
 *
 * Renders nothing. Mounted inside <ClerkProvider> in main.tsx; see
 * ./instance.ts for why this indirection exists at all.
 */

import { useEffect } from "react";
import { useClerk } from "@clerk/react";
import { setClerkInstance } from "./instance";

export function ClerkBridge(): null {
    const clerk = useClerk();

    useEffect(() => {
        setClerkInstance(clerk);
        // useClerk returns a stable object. Session changes do not rerun this
        // effect, so subscribe to resources rather than checking only at mount.
        const publish = () => setClerkInstance(clerk);
        const unsubscribe = clerk.addListener(publish);
        // Resource emission can precede loaded=true during initial startup.
        clerk.on("status", publish, { notify: true });
        // Clearing on unmount matters in tests, where several trees mount in
        // one process and a stale instance from a torn-down tree would be
        // handed to the next one.
        return () => { unsubscribe(); clerk.off("status", publish); setClerkInstance(null); };
    }, [clerk]);

    return null;
}
