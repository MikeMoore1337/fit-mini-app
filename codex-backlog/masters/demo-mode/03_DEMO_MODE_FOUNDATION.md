# Stage 2 - Demo mode foundation

## Goal

Introduce a first-class demo mode without changing normal authenticated behavior.

## Requirements

Implement a centralized way to determine current application mode/capabilities.

The codebase should be able to distinguish at minimum:

- ordinary unauthenticated/public state;
- demo state;
- authenticated user state.

Use architecture appropriate to the current repository.

## Entry behavior

Add a public demo entry path/action that does not require creating an account.

Requirements:

- reachable from the public web product/landing experience;
- direct and fast;
- no Telegram authorization required merely to try demo;
- reuses the actual application shell;
- clearly marked as demo mode.

Do not force the user through onboarding meant for a persistent real account.

## Demo indicator

Add a persistent but unobtrusive indicator such as a banner/chip/header state showing that the user is in demo.

It should communicate:

- this is demo mode;
- changes are temporary;
- a clear action exists to continue/sign in.

Use existing UI primitives.

## Capability model

Prefer centralized capability checks, conceptually such as:

```text
canPersistUserData
canUseAiCoach
canInviteClient
canSendNotifications
canLinkAccounts
```

The exact API/naming should follow the codebase.

Avoid spreading raw route-name checks or one-off `isDemo` conditions through many unrelated components when a capability abstraction is cleaner.

## AI Coach boundary

From this stage onward, demo must not be able to use AI Coach.

Guard all applicable layers:

- navigation/UI entry;
- route access;
- client API invocation;
- backend endpoint authorization/validation if anonymous access could otherwise reach it.

If AI Coach appears in navigation, replace active access in demo with either:

- a disabled/locked non-interactive entry; or
- a small teaser for the authenticated product.

Do not call an AI provider.

## Compatibility

Authenticated web app and Telegram Mini App behavior must remain unchanged unless a shared bug is discovered and fixed explicitly.

## Tests

Add focused tests for:

- entering demo;
- mode detection;
- authenticated mode unaffected;
- AI Coach unavailable in demo;
- direct demo attempt to reach AI route/API is blocked safely.

## Commit

Suggested commit intent:

```text
feat/demo: add first-class demo application mode
```
