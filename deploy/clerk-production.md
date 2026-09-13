# Clerk accounts for PrivaTools

The consumer app defaults to Clerk. Email/password, optional usernames, Google
and GitHub connections, passkeys and email password reset use the same Air/Play
interface. File tools remain available without signing in. Missing Clerk
configuration shows an honest unavailable state; it never silently creates a
native recovery-code account.

## Current dashboard configuration

Verified on 2026-09-13 in the existing PrivaTools application; production Google configuration completed and password settings rechecked on 2026-09-14:

| Setting | Production | Development |
| --- | --- | --- |
| Optional username at signup and username sign-in | Enabled | Enabled |
| Username length | 4–64 | 4–64 |
| Passkey sign-in and enrollment | Enabled | Enabled |
| Password minimum | 12 | 12 |
| Reject compromised passwords | On | On |
| Compulsory capitals, numbers or symbols | None | None |
| Device Trust | Retained | Retained |
| Google | Enabled with custom PrivaTools OAuth credentials | Enabled with shared development credentials |
| GitHub | Enabled | Enabled with shared development credentials |

The dashboard's separate Mobile Biometric setting applies to native iOS/Android
apps. The website and installed PWA use passkeys: device biometrics, screen lock
or a security key, depending on the browser. Users enroll their own passkeys
from Account Settings after creating or signing into an account.

## Local development

Copy `frontend/.env.example` to `frontend/.env.local` and set the **public**
`pk_test_…` key. Development and Production have separate users. A Google signup
on localhost appears under **Development → Users**, not Production.

The local backend launcher reads only `VITE_CLERK_PUBLISHABLE_KEY` from that file,
and only when it is a development key. It never imports a secret key or production
environment file. An explicit backend `CLERK_PUBLISHABLE_KEY` takes precedence.
The frontend and backend must refer to the same instance.

## Production build and runtime

Set the public `pk_live_…` key as the GitHub repository variable
`CLERK_PUBLISHABLE_KEY`, and as `CLERK_PUBLISHABLE_KEY` in the server environment.
The existing release workflow passes it into the frontend build. Docker Compose
also passes matching build arguments when building locally.

`VITE_CLERK_SOCIAL_PROVIDERS` controls which verified providers appear. The release
workflow reads repository variable `CLERK_SOCIAL_PROVIDERS`, defaulting to
`google,github` now that production Google configuration and hosted sign-in are
verified. Explicit repository-variable or Compose/build overrides still take
precedence; inspect an existing `github`-only override before releasing. Username and passkey feature flags are also build arguments; match
them to the instance settings before deploying a different Clerk application.

Do not deploy a localhost build containing the development key. A frontend build
must use the production key for the production domain.

The backend validates Clerk tokens with public JWKS. It does not need
`CLERK_SECRET_KEY`. Native register, login, recover, password-change and recovery
rotation endpoints return 409 when Clerk is configured, before hashing or writes.
Existing native records and keys are not deleted. Explicit legacy installations
can still use `VITE_AUTH_PROVIDER=local` with no Clerk key.

## Google OAuth configuration

The existing production Google connection is enabled at **Configure → SSO
connections → Google**. Its verified callback is:

`https://clerk.privatools.me/v1/oauth_callback`

After the owner's specific approval, project **PrivaTools** (`privatools-508520`)
was created under the PrivaTools Google account. The **PrivaTools Web** client
uses `https://privatools.me` as its JavaScript origin and the callback above.
Homepage, Privacy and Terms URLs and the authorized `privatools.me` domain are
saved. Google audience is External with publishing status **In production**.
No billing, trial, paid service or paid upgrade was enabled.

The owner explicitly approved transferring the new client ID and secret directly
into Clerk. The Google connection is enabled for sign-up and sign-in and requests
only `openid`, email and basic profile. No Drive/Gmail scopes were added. The
secret is held in provider configuration, not this repository or a `VITE_` variable.
Existing GitHub and other connection settings were preserved.

Provider configuration and an actual hosted production Google sign-in are
verified. The flow started at `https://accounts.privatools.me/sign-in`, completed
the Google chooser/consent and returned to the currently deployed account page.
Clerk production user details confirmed the Google identity is verified and
linked. The callback destination is still the older website: the new Air/Play
release is not deployed, and its production key/account/API integration must
still be checked. No new release variables or secrets were changed in this
defaults update.
Keep provider verification evidence privately; do not commit account records or OAuth credentials.
See [Clerk's Google setup guide](https://clerk.com/docs/guides/configure/auth-strategies/social-connections/google).

## Account deletion and verification

Configure a Clerk webhook for `user.deleted` at
`https://privatools.me/api/clerk/webhook`, and set `CLERK_WEBHOOK_SECRET` on the
server. This removes local API keys when an identity is deleted through Clerk.
Application-initiated deletion first removes local API access, then deletes the
Clerk identity. The webhook remains necessary for deletion initiated in Clerk
or another client; without it those deletions cannot notify this key store.

Before release, verify signed-in key access, sign-out, email recovery, new-device
verification and a real passkey on the HTTPS origin. Passkeys and Google provider
screens require the account owner to complete device/account prompts. The local
automated tests use synthetic identities and do not enroll credentials.
