# Stage 4 - Demo UX and contextual conversion

## Goal

Turn demo usage into a natural path toward authentication without blocking evaluation of the product.

## Public entry point

Add a clear secondary/parallel CTA on the public landing/product entry experience, using wording consistent with the current UI, for example:

- `Попробовать демо`

Keep the main real-product CTA intact.

## Conversion principle

Do not gate valuable actions before the user can try them.

Prefer:

```text
try -> receive value -> attempt to keep result -> authenticate
```

over:

```text
authenticate -> try
```

## Contextual persistence prompts

For enabled demo flows, intercept the moment the visitor tries to keep a result.

Use contextual copy appropriate to the action.

Examples of intent:

### Program

User creates/edits a program and presses save.

Explain that demo changes are temporary and offer continuation into the real application.

### Kcal/macros

Allow calculation first.

After result, offer to save it to a real profile.

### Workout

Allow a representative workout flow.

At finish/save, explain that workout history requires an authenticated profile.

### Profile/progress

Allow temporary editing/viewing.

Persisting long-term progress requires authentication.

## CTA destinations

Offer the current supported continuation paths:

- authenticated web application;
- Telegram Mini App, where appropriate.

Use existing URL/navigation/auth helpers. Do not hardcode duplicate auth logic when reusable helpers exist.

## Avoid modal spam

Do not show the same blocking prompt repeatedly during normal exploration.

Use a sensible UX mechanism:

- contextual dialog/sheet at save;
- persistent demo banner action;
- locked identity-bound feature explanation.

## AI Coach presentation

AI Coach remains disabled in demo.

It may be shown as a full-mode feature teaser, for example an inactive card/entry indicating that it becomes available after sign-in.

Requirements:

- no active chat input;
- no fake response simulation;
- no model calls;
- no implication that the visitor has consumed or owns an AI quota.

## Responsive behavior

Verify on:

- desktop web;
- mobile web;
- layouts used around Telegram Mini App entry/auth flows.

Do not alter intentional theme differences between web and Telegram Mini App.

## Tests

Add focused UI/integration tests for:

- demo CTA;
- demo indicator;
- save interception;
- correct auth/Telegram CTA targets;
- no repeated disruptive prompt behavior;
- AI Coach teaser/locked behavior if shown.

## Commit

Suggested commit intent:

```text
feat/demo: add demo conversion and sign-in UX
```
