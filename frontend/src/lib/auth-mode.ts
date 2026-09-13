import { isClerkEnabled } from './clerk/instance';

/** Hosted identity is the default. Legacy local accounts require an explicit opt-in. */
export function usesClerkAccounts(): boolean {
  return isClerkEnabled() || import.meta.env.VITE_AUTH_PROVIDER !== 'local';
}
export function accountsConfigured(): boolean {
  return !usesClerkAccounts() || isClerkEnabled();
}
export function configuredSocialProviders(): string[] {
  return (import.meta.env.VITE_CLERK_SOCIAL_PROVIDERS || 'github').split(',').map(value => value.trim()).filter(Boolean);
}

/** Deployment flags must match the enabled Clerk instance. */
export function usernameAccountsEnabled(): boolean {
  return usesClerkAccounts() && import.meta.env.VITE_CLERK_USERNAME_ENABLED !== 'false';
}
export function passkeyAccountsEnabled(): boolean {
  return isClerkEnabled() && import.meta.env.VITE_CLERK_PASSKEYS_ENABLED === 'true';
}
