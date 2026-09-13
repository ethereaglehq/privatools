import { afterEach, describe, expect, it, vi } from 'vitest';
import { accountModeForLocation, accountPathForLocation, withAccounts } from './withAccounts';

class Base {
  state = {};
}

afterEach(() => vi.unstubAllGlobals());

describe('account path-specific navigation', () => {
  it.each(['/account/keys', '/account/keys/'])('does not reload an already correct keys path: %s', pathname => {
    const replace = vi.fn();
    vi.stubGlobal('location', { pathname, hash: '#/account/keys', replace });
    const Account = withAccounts(Base, {});
    new Account({})._ensureAccountPath();
    expect(replace).not.toHaveBeenCalled();
  });

  it.each([
    ['/', '#/account', '/account'],
    ['/tools/hash-generator', '#/account/keys', '/account/keys'],
    ['/account', '#/account/keys', '/account/keys'],
    ['/', '#/account/sign-in', '/account/sign-in'],
    ['/tools/hash-generator', '#/account/sign-up', '/account/sign-up'],
    ['/account', '#/account/settings', '/account/settings'],
  ])('loads the account CSP for %s %s', (pathname, hash, target) => {
    const replace = vi.fn();
    vi.stubGlobal('location', { pathname, hash, replace });
    const Account = withAccounts(Base, {});
    new Account({})._ensureAccountPath();
    expect(replace).toHaveBeenCalledExactlyOnceWith(target);
  });

  it('leaves signup queries and unrelated routes alone', () => {
    const replace = vi.fn();
    const Account = withAccounts(Base, {});
    vi.stubGlobal('location', { pathname: '/account', search: '?mode=signup', hash: '#/account', replace });
    new Account({})._ensureAccountPath();
    vi.stubGlobal('location', { pathname: '/', hash: '#/tools', replace });
    new Account({})._ensureAccountPath();
    expect(replace).not.toHaveBeenCalled();
  });

  it.each([
    ['/account/sign-up', '', '', 'signup'],
    ['/account/sign-in', '', '?mode=signup', 'signin'],
    ['/account', '', '?mode=signup', 'signup'],
    ['/', '#/account/sign-up', '', 'signup'],
    ['/account/settings', '', '', 'signin'],
  ])('derives auth mode from %s %s', (pathname, hash, search, mode) => {
    expect(accountModeForLocation({ pathname, hash, search })).toBe(mode);
  });

  it('recognises settings and keys without treating unrelated account-like URLs as accounts', () => {
    expect(accountPathForLocation({ pathname: '/account/settings/', hash: '' })).toBe('/account/settings');
    expect(accountPathForLocation({ pathname: '/account/keys', hash: '' })).toBe('/account/keys');
    expect(accountPathForLocation({ pathname: '/accounting', hash: '' })).toBeNull();
  });
});
