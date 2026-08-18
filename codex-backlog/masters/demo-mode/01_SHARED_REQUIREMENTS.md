# Shared requirements for demo mode

These requirements apply to every stage.

## Product principle

Demo mode is not a collection of screenshots and not a crippled read-only mock.

The visitor should be able to interact with the real product experience enough to understand its value.

The main conversion mechanic is:

> Let the visitor perform the valuable action first. Ask for authentication when persistence or an identity-bound capability is required.

Do not place authentication gates in front of every useful action.

## Demo identity

Demo mode must have an explicit application-level state, for example conceptually:

```text
authenticated
demo
unauthenticated/public
```

Use names consistent with the existing codebase.

Do not implement demo by sharing one ordinary database user account among all visitors.

Do not make a global `demo_user` whose records are mutated by anonymous sessions.

## Persistence policy

Demo changes must be temporary.

Preferred order:

1. client/session-local ephemeral state when feasible;
2. isolated short-lived server-side ephemeral state only if current architecture genuinely requires it;
3. never persist demo modifications as normal production user records.

A browser refresh may either reset the demo or restore only safe local ephemeral demo state. Choose the approach that best matches the current application architecture, but document it.

There must be a visible way to reset demo data to the prepared initial state.

## Prepared demo data

Provide realistic sample data sufficient to make empty-state-heavy screens understandable.

As applicable to the current product, include representative examples of:

- profile data;
- goal;
- anthropometric data;
- calculated calories/macronutrients;
- pulse/heart-rate related results if present;
- one or more training programs;
- exercises;
- workout history;
- progress/measurements/statistics.

Do not fabricate functionality that does not exist in the current product.

## Allowed interactions

Where the current product supports them, demo should normally allow the visitor to:

- navigate through core sections;
- edit temporary profile values;
- recalculate calories/macronutrients;
- view heart-rate calculations;
- inspect programs and exercises;
- create/edit a program temporarily;
- start a workout;
- enter temporary workout results;
- use workout/rest timers;
- finish a demo workout;
- view prepared progress/history examples.

The exact supported set must be based on the current repository.

## Persistence-triggered conversion

Do not block creation/editing merely because the user is in demo.

Instead, intercept persistence at the point where preserving data matters.

Examples:

- "Save program"
- "Save profile"
- "Save calculation"
- "Save workout result"
- "Keep progress"

At that point, show a clear explanation that demo data is temporary and offer continuation into the authenticated product.

Use the current product's established auth/navigation patterns.

## AI Coach

AI Coach must NOT be active in demo mode.

Requirements:

- no anonymous AI API calls;
- no model/provider calls from demo;
- no hidden route that bypasses this restriction;
- no demo AI quota;
- no placeholder chat pretending to be live AI.

If useful for conversion and consistent with the current UI, a non-interactive teaser may state that AI Coach is available in the full authenticated application.

The teaser must not look like an active chat.

## Identity-bound and external-side-effect features

Disable or block capabilities that require a real identity or create effects outside the temporary demo session, including as applicable:

- trainer/client invitations;
- linking trainer and client accounts;
- Telegram notifications;
- push/email notifications;
- exports that expose or create server-side data;
- uploads if they create persistent storage;
- payment actions;
- admin actions;
- social or sharing actions;
- any write operation to another real user's data.

When these features are visible, explain why authentication is required.

## UX rules

- Demo should use the same design system as the real application.
- Demo uses the same shared YFC Light/Dark visual system as the real application on Web and TMA.
- Clearly indicate that the visitor is in demo mode.
- Avoid repeated intrusive modal dialogs.
- Prefer contextual conversion prompts after meaningful actions.
- Provide a persistent but unobtrusive path to sign in/continue.
- Ensure mobile web and Telegram-related layouts remain usable.
- Do not introduce Web/TMA visual divergence; only documented Telegram platform behavior may differ.

## Accessibility and responsiveness

New demo UI must follow existing accessibility conventions.

At minimum verify:

- keyboard/focus behavior where applicable;
- semantic buttons/links;
- readable labels;
- mobile viewport layout;
- no clipped modals/sheets;
- touch target sizes consistent with existing components.

## Analytics/privacy

If analytics already exists, demo events may be tracked only through the existing analytics abstraction and privacy rules.

Do not introduce a new analytics vendor as part of this task.

Never include sensitive entered demo values in analytics event payloads.

## Documentation

Document only durable architectural/product behavior:

- what demo mode is;
- how it differs from authenticated mode;
- persistence rules;
- restricted capabilities;
- how to extend demo fixtures safely.

Do not create large audit reports in public documentation if the repository conventions keep audits private.
