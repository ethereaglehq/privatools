const securityMessages = {
    account_changed: "Your sign-in has changed. Reload this page before managing account security.",
    current_password_required: "Enter your current password before choosing a new one.",
    enrollment_ready: "Verification complete. Click Add a passkey again to open your browser’s prompt.",
    verification_incomplete: "Your identity could not be verified. Try again to complete the security check.",
    passkey_missing: "This passkey is no longer on your account. Refresh the list to continue.",
} as const;

/** Only local, fixed messages from this class may reach account-security UI. */
export class AccountSecurityError extends Error {
    constructor(public code: keyof typeof securityMessages) { super(securityMessages[code]); }
}

export function verificationCancelled(error: unknown): boolean {
    return (error as { code?: string } | null)?.code === "reverification_cancelled";
}

export function securityErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof AccountSecurityError) return error.message;
    if (verificationCancelled(error)) return "Verification was cancelled. Nothing was changed. Try again when you’re ready.";
    return fallback;
}

export const ACCOUNT_CLEANUP_PENDING = "Your sign-in account was deleted. API data cleanup could not be confirmed yet. Contact support if your API access remains available.";
