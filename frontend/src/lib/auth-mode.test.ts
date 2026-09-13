import { afterEach, describe, expect, it, vi } from 'vitest';
const enabled=vi.hoisted(()=>({value:false}));
vi.mock('./clerk/instance',()=>({isClerkEnabled:()=>enabled.value}));
import { accountsConfigured, configuredSocialProviders, usesClerkAccounts } from './auth-mode';
afterEach(()=>{vi.unstubAllEnvs();enabled.value=false;});
describe('account provider selection',()=>{
  it('uses Clerk by default without silently offering recovery-code signup',()=>{vi.stubEnv('VITE_AUTH_PROVIDER',undefined);expect(usesClerkAccounts()).toBe(true);expect(accountsConfigured()).toBe(false);});
  it('only enables native recovery when a deployment deliberately opts in',()=>{vi.stubEnv('VITE_AUTH_PROVIDER','local');expect(usesClerkAccounts()).toBe(false);expect(accountsConfigured()).toBe(true);});
  it('keeps a configured Clerk instance authoritative',()=>{enabled.value=true;vi.stubEnv('VITE_AUTH_PROVIDER','local');expect(usesClerkAccounts()).toBe(true);expect(accountsConfigured()).toBe(true);});
  it('shows only declared social connections',()=>{vi.stubEnv('VITE_CLERK_SOCIAL_PROVIDERS','google, github');expect(configuredSocialProviders()).toEqual(['google','github']);});
});
