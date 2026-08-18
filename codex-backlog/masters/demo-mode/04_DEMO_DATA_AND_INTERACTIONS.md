# Stage 3 - Demo fixtures and temporary interactions

## Goal

Make demo mode useful enough to demonstrate the current product without persisting real data.

## Demo fixtures

Create maintainable representative demo fixtures.

Use current domain models/types where possible so fixtures cannot silently diverge from real application contracts.

Include only data for features that currently exist.

Aim to avoid mostly empty screens.

## Temporary editing

Enable temporary interactions for the product's core flows where technically reasonable.

Examples, depending on the current codebase:

- edit profile fields;
- change goal;
- recalculate Kcal/macros;
- recalculate pulse zones;
- create/edit a training program;
- edit sets/repetitions/rest values;
- start a workout;
- enter results;
- use timers;
- finish a workout;
- inspect prepared history/progress.

## No real persistence

Demo writes must not become ordinary persistent records.

Explicitly verify the write path for each enabled demo interaction.

Where practical, use an adapter/repository abstraction:

```text
real repository -> backend persistence
demo repository -> ephemeral state
```

This is only a conceptual example. Use the project's architecture.

Do not create a single shared mutable demo account in the database.

## Reset

Add an obvious but non-intrusive "Reset demo" capability.

Reset must restore the prepared initial data for the current visitor/session only.

It must not affect real users.

## Reload/session behavior

Choose and implement one consistent rule:

### Option A - reset on reload
Simple and safe if it fits the app.

### Option B - temporary browser/session persistence
Allowed only for demo-scoped, non-sensitive temporary data and only if it cannot be confused with authenticated persistence.

Document the chosen behavior.

## Error handling

A demo action that would require unsupported persistence should fail gracefully with a product-level explanation, not an unhandled backend error.

## Tests

Cover:

- fixture loading;
- demo editing;
- calculations still work;
- reset restores fixtures;
- no normal persistence write is emitted for simulated demo actions;
- isolation between demo and authenticated state;
- no real-user data appears in demo.

## Commit

Suggested commit intent:

```text
feat/demo: add ephemeral demo data and interactions
```
