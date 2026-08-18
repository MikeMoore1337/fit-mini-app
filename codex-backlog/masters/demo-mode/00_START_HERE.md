# Your Fitness Coach - Demo Mode

## Purpose

Implement a public demo mode for Your Fitness Coach that lets a new visitor explore the real product without registration, while creating natural motivation to continue in the authenticated web application or Telegram Mini App.

The core rule is:

> The user may explore and interact with the main product features, including entering and changing temporary data, but demo data must not be persisted as real user data.

AI Coach is intentionally excluded from demo mode. It is a feature of the full authenticated product.

## Repository

- Repository: `https://github.com/MikeMoore1337/fit-mini-app`
- Product site: `https://your-fitness-coach.ru/`

Work against the current repository state. Do not assume that file paths, components, routes, APIs, or architecture match an older version of the project.

## How to work with this task package

Do not load every task file into context at once.

For each stage:

1. Read this file.
2. Read `01_SHARED_REQUIREMENTS.md`.
3. Read only the current stage file.
4. Inspect the relevant current code and relevant `docs/`.
5. Implement only that stage.
6. Run tests related to that stage.
7. Update documentation if the stage changes documented behavior, architecture, setup, contracts, or security assumptions.
8. Commit the completed stage separately.
9. Continue to the next stage in the same Git branch.

Follow the repository `AGENTS.md` and all applicable project skills/rules.

## Execution order

1. `02_AUDIT_AND_DESIGN.md`
2. `03_DEMO_MODE_FOUNDATION.md`
3. `04_DEMO_DATA_AND_INTERACTIONS.md`
4. `05_DEMO_UX_AND_CONVERSION.md`
5. `06_AUTH_HANDOFF_AND_OPTIONAL_MIGRATION.md`
6. `07_SECURITY_AND_RESTRICTIONS.md`
7. `08_TESTS_AND_FINAL_VERIFICATION.md`

## Important workflow constraints

- Use one dedicated feature branch for the entire demo-mode implementation.
- Do not create a new branch for each subtask.
- Do not merge to the production branch as part of this task.
- Do not deploy to production unless explicitly requested separately.
- Keep the project working after every stage.
- Make one meaningful Git commit per completed stage.
- Do not mix unrelated refactoring with demo-mode work.
- Prefer the smallest architectural change that cleanly supports demo mode.
- Reuse existing design-system components and application flows instead of building a visually separate "fake demo".

## Non-goals

This task does not include:

- enabling AI Coach in demo;
- anonymous AI requests;
- payments or subscription redesign;
- a new authentication system;
- a redesign of unrelated product screens;
- creating a second independent application just for demo;
- production deployment;
- large-scale backend rewrites unrelated to demo mode.

## Definition of done

The feature is complete when an unauthenticated visitor can:

- enter demo mode directly from the public product entry point;
- explore the main application UI;
- change demo profile/calculation/training data temporarily;
- perform meaningful demo flows without registering first;
- see realistic prepared sample data;
- reach contextual sign-in/continue CTAs after valuable actions;
- leave/reload/reset the demo without contaminating real user data;
- never invoke AI Coach from demo;
- never create external side effects such as invitations or notifications;
- authenticate and continue into the real product cleanly.

All relevant automated tests and project quality checks must pass.
