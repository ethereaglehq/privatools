import { useEffect } from "react";
import { useAccountReverification, type AccountSecurityRunner } from "@/lib/clerk/useAccountReverification";

/** Lets the legacy class controller use the same public Clerk verification hook. */
export default function AccountReverificationBridge({ onReady }: { onReady: (runner: AccountSecurityRunner | null) => void }) {
    const run = useAccountReverification();
    useEffect(() => { onReady(run); return () => onReady(null); }, [onReady, run]);
    return null;
}
