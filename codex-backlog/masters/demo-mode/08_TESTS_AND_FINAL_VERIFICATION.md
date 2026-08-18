# Stage 7 - End-to-end verification and cleanup

## Goal

Verify that demo mode is production-quality and that normal application behavior has not regressed.

## Required test matrix

### Public/unauthenticated

- landing loads;
- demo CTA is visible;
- demo starts without registration;
- ordinary auth CTA still works.

### Demo mode

- demo indicator is visible;
- fixtures load;
- core navigation works;
- temporary profile edits work;
- calculations work;
- temporary program/workout interactions work where implemented;
- reset works;
- persistence attempts produce contextual conversion UX;
- AI Coach cannot be used;
- identity-bound actions cannot execute;
- no real-user mutation occurs.

### Authenticated web

- login/session behavior unchanged;
- profile persistence works normally;
- program/workout persistence works normally;
- AI Coach remains available according to existing authenticated product rules;
- notifications/invitations continue to follow existing permissions.

### Telegram Mini App

Verify existing authenticated Telegram behavior remains intact.

Demo mode should not masquerade as Telegram-authenticated state.

### Mode transitions

- public -> demo;
- demo -> web auth;
- demo -> Telegram continuation path;
- demo -> reset;
- demo -> exit;
- authenticated -> logout;
- stale demo state does not leak into authenticated mode.

## Browser/device coverage

Use the project's existing browser/test matrix.

At minimum manually or automatically verify responsive behavior for representative:

- mobile viewport;
- desktop viewport.

If project tooling supports screenshots/visual checks, use them according to existing QA conventions.

## Quality checks

Run all relevant:

- unit tests;
- integration tests;
- frontend tests;
- backend tests;
- type checking;
- linting;
- formatting validation;
- targeted E2E tests.

Run the broader/full suite only in accordance with the repository `AGENTS.md` workflow.

## Documentation

Update durable documentation so future developers know:

- how to enter demo mode;
- where demo fixtures live;
- how persistence is prevented;
- which capabilities are restricted;
- AI Coach is authenticated-only;
- how to add new demo-compatible features safely.

## Cleanup

Before completion:

- remove debug flags/logging;
- remove dead prototype code;
- ensure no fixture contains personal or production data;
- ensure no TODO hides a known security issue;
- ensure copy is in the project's localization system if one exists.

## Final report

Provide a concise completion report containing:

- stages/commits completed;
- architecture used;
- demo-supported flows;
- intentionally unavailable demo features;
- AI Coach enforcement;
- test commands/results;
- docs updated;
- migration support status;
- known limitations/follow-ups.

Do not deploy or merge unless requested separately.

## Commit

Suggested commit intent:

```text
test/demo: complete demo mode verification
```
