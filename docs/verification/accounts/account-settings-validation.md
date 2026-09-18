# Account settings release validation

> **Shipped in v2.4.1** (#166, 14 September 2026).

Requested alongside the API onboarding rollout: make account settings, password changes and passkeys accessible in production, and improve the account pages on desktop/mobile in both Air and Play.

## Confirmed before implementation

- The production account button opened the API-key page. Account settings were missing from the active page's header/footer navigation.
- The active mobile shell restored a small account icon through a later CSS override, but it still led to API keys. The stylesheet declared a 29 × 32 CSS-pixel minimum target. The legacy consumer shell hid the account link.
- Production's signed-in passwordless settings page offered a recovery link, but that link returned signed-in users to their API-key page.
- Production Clerk public configuration enables editable passwords and passkeys, email-code verification, and reverification. Release build flags enable passkeys. No Clerk dashboard setting needs changing.
- Custom password, passkey and username mutations need Clerk reverification support. The existing password adapter converted structured Clerk errors before the UI could respond to the verification challenge.
- A separate production browser tab confirmed the signed-in settings page and an enabled Add a passkey control. No password, passkey or profile was changed during inspection. Existing user tabs and unsaved API keys were preserved.

## Implementation and validation

Implemented shared compact account headers, persistent settings/API navigation, active and revoked key states, clear one-time key saving, profile/security controls before browser preferences, and 44px mobile account targets. Current native account browser checks passed across 320px, 390px, and 1440px in Air/Play light/dark (24 screenshots): no horizontal page overflow, settings/API navigation, required current password, real key creation/reveal acknowledgment/revocation, live sample processing activity, and usage before starter tips on mobile. Screenshots use reduced motion to capture settled layouts.

Passwordless accounts now create a password inline, and existing-password accounts require their current password. Password, username and passkey actions preserve Clerk verification challenges and bind retries to the original account. Passkey enrollment asks for a fresh click after verification so the browser receives a user gesture. Account deletion verifies and deletes the Clerk identity before backend cleanup; a bounded cleanup failure produces an honest warning without retrying identity deletion.

Final local checks passed: 914 frontend tests across 107 files, nine content/build-preparation tests, TypeScript, zero-warning ESLint, production build, bundle budgets and whitespace validation. Independent review of the full account diff and screenshots found no material issue. A disposable native account also passed a real browser/API password change: wrong current password rejected, successful change cleared fields, old login rejected and new login accepted. Its fixtures were removed.

No production user's password, passkey, username or account was changed. Clerk-origin webhook delivery remains unverified. Automatic approval review blocked a proposed signed synthetic deletion event on production before execution; zero requests or fixtures were created. The isolated signed-handler check passed 17 checks with complete fixture cleanup. Account UI checks and mocked security-flow tests must not be described as a real credential mutation on a production user's account. Release rollout is recorded separately after deployment.
