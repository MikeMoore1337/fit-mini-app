# Stage 1 - Audit current product and design the integration

## Goal

Understand the current application architecture and produce the smallest safe implementation plan for demo mode before changing behavior.

## Scope

Inspect:

- web landing/product entry points;
- web application routing;
- Telegram Mini App routing/entry behavior;
- authentication/session state;
- user/profile state management;
- API client and backend write paths;
- training/program/calculation/progress modules;
- AI Coach routes/components/API;
- notifications/invitations/trainer-client linking;
- persistence/database layer;
- existing feature flags or application modes;
- design-system components for banners, dialogs, sheets, buttons and navigation;
- relevant tests;
- relevant `docs/`.

## Required decisions

Determine and record in a short implementation note:

1. Where demo mode is represented in application state.
2. How demo mode is entered.
3. Where prepared demo data lives.
4. How temporary edits are stored.
5. Which write operations can be safely simulated client-side.
6. Which actions must be blocked because they have external side effects.
7. How AI Coach is made unreachable/non-callable from demo.
8. How demo conversion to web auth and Telegram Mini App should work with the current auth architecture.
9. Whether transferring demo data after authentication is feasible now or should be deferred.
10. What tests should protect the mode boundary.

## Constraints

- Do not implement the full feature in this stage.
- Small scaffolding changes are acceptable only if required to validate the design.
- Prefer extending existing session/state abstractions over scattering `if demo` checks everywhere.
- Identify existing reusable permission/capability logic before inventing new guards.
- Do not redesign authentication.

## Deliverable

Create or update an appropriate technical note under the project's normal documentation location if repository conventions support it.

If the repository uses private audit artifacts, place raw audit notes under the existing private artifact convention rather than public `docs/`.

The final implementation decision should be concise enough that future stages can rely on it.

## Verification

Run only lightweight checks relevant to any files actually changed in this stage.

## Commit

Suggested commit intent:

```text
docs/demo: define demo mode integration plan
```
