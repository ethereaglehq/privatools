import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ExperienceShell } from './ExperienceShell';

vi.mock('@/lib/experience', () => ({ useExperience: () => ({
  experience: 'air', appearance: 'light', resolved: 'light',
  setExperience: vi.fn(), setAppearance: vi.fn(),
}) }));
vi.mock('@/components/pwa/PwaControls', () => ({ PwaControls: () => null }));
afterEach(cleanup);

it('opens signed-in account settings directly from the persistent header', () => {
  render(<ExperienceShell view="settings" signedIn onSearch={vi.fn()}><h1>Account settings</h1></ExperienceShell>);
  const headerLink = within(screen.getByRole('banner')).getByRole('link', { name: 'Account settings' });
  expect(headerLink).toHaveAttribute('href', '/account/settings');
  expect(headerLink).toHaveAttribute('aria-current', 'page');
  expect(within(screen.getByRole('contentinfo')).getByRole('link', { name: 'Account settings' }))
    .toHaveAttribute('href', '/account/settings');
});

it('returns a signed-out visitor to settings after signing in', () => {
  render(<ExperienceShell view="home" signedIn={false} onSearch={vi.fn()}><h1>Home</h1></ExperienceShell>);
  expect(within(screen.getByRole('banner')).getByRole('link', { name: 'Sign in' }))
    .toHaveAttribute('href', '/account/sign-in?next=/account/settings');
});
