# Project context

Your Fitness Coach is one product exposed through the browser and Telegram Mini App,
with a shared backend and PostgreSQL database.

Main areas:

- `frontend/` - React, TypeScript, Vite, TanStack Query;
- `backend/` - Python 3.14, FastAPI, SQLAlchemy, Alembic;
- `bot/` - Python 3.14, Aiogram;
- `scripts/` - project automation, checks, maintenance, deployment helpers;
- Docker Compose - local and production-oriented orchestration.

Preserve the current architecture and repository conventions unless the task explicitly
requires a change or there is a concrete technical reason to change them.

Use relevant repository skills from `.agents/skills/` for specialized work. This file
contains repository-wide rules and takes precedence over a generic skill when they conflict.
Do not load unrelated specialized guidance merely because it exists.

# Workspace hygiene

- Put caches, temporary files, test artifacts, logs, screenshots, traces, coverage and
  generated reports under `.artifacts/`.
- Never create ad-hoc scratch paths such as `.tmp*`, `pytest-cache-files-*`, reports,
  screenshots or logs in the repository root.
- Prefer paths already configured in `pyproject.toml`, Playwright config and `scripts/`.
- Use `.artifacts/cache/`, `.artifacts/tmp/` or another suitable `.artifacts/` subdirectory
  when an isolated path is needed.
- Never commit `.artifacts/` contents.

# Working principles

- Inspect the existing implementation, relevant tests and documentation before changing it.
- Make the smallest complete change that solves the actual problem.
- Preserve public behavior unless a behavioral change is intentional.
- Reuse existing components, utilities, dependencies, patterns and abstractions first.
- Do not add a dependency when the current stack can reasonably solve the problem.
- Do not perform unrelated refactoring in a focused task.
- Do not leave dead code, debug logging, temporary compatibility hacks, commented-out
  implementations or unfinished TODOs created by the task.
- Do not hide failures by weakening validation, types, tests, linting or other tooling.

Never use skipped/deleted tests, broad `# noqa`, unnecessary `type: ignore`, `@ts-ignore`,
`@ts-nocheck`, ESLint disables, empty/swallowed exceptions, arbitrary sleeps, or `Any`/`any`
merely to make checks pass. If an exception is genuinely required, keep it narrow and explain
why in code or documentation where appropriate.

# Architecture and scope

- Keep business rules out of transport and presentation layers where practical.
- Enforce authorization and critical validation on trusted server-side boundaries.
- Avoid duplicate sources of truth and unclear ownership of state.
- Prefer explicit data flow and clear module/component responsibilities.
- Do not introduce microservices, queues, Redis, Kubernetes, CQRS, Event Sourcing or similar
  infrastructure without a concrete requirement.
- Prefer improving the current modular architecture over replacing it with a more complex one.
- Do not rewrite a working subsystem solely to adopt newer technology.

For cross-cutting changes, identify all affected surfaces before implementation: backend,
frontend, Telegram Mini App, bot, database, generated API types, tests,
deployment/configuration and documentation.

# Workflow

For substantial work, use logical stages. For each completed stage:

1. implement one coherent part;
2. run checks directly related to that stage;
3. fix failures caused by the change;
4. review the diff for accidental changes;
5. create a separate focused Git commit.

Do not commit a knowingly broken stage. Do not manufacture extra stages for trivial edits.
Before finishing substantial work, run broader relevant verification for every touched
subsystem.

Normal local linting, formatting, type checking, tests, builds and browser verification do
not require additional confirmation.

Ask before operations that are destructive, production-affecting, use real paid external
services, modify real user data, or are unusually expensive/outside the task scope.

# Dependencies

- Add or upgrade dependencies only when justified by the task.
- Prefer maintained, narrowly scoped dependencies and consider security plus bundle/runtime cost.
- Update the appropriate lock/compiled dependency files and keep dependency diffs intentional.
- Do not perform broad dependency upgrades as part of unrelated work.

# Testing baseline

Use risk-based testing. Changes to business logic, API behavior, permissions, state
transitions, calculations, persistence, parsing/validation or regression-prone UI behavior
normally require appropriate tests.

Test meaningful boundaries and failure paths, not only happy paths. Prefer deterministic
waits/assertions over sleeps. Add a regression test for a meaningful bug fix when practical.
Use the relevant engineering/QA skill for project-specific commands and deeper rules.

# Security baseline

Never commit passwords, API or Telegram bot tokens, private keys, session secrets,
production credentials, real `.env` files or credentials copied into tests/documentation.
Use `.env.example` only for variable names and safe example/default values.

Authentication, authorization, user/trainer data isolation and critical validation must not
rely on hidden UI, frontend state, routes or Telegram client state. Do not expose secrets or
internal stack traces in user-visible errors or logs.

Use `security-engineer` for security-sensitive implementation, audit or threat modeling.

# Documentation baseline

Treat `docs/` as long-term architectural and operational context. Before changing an
existing subsystem, check for relevant documentation.

Update documentation in the same stage when a change makes documented setup, environment
variables, commands, API contracts, architecture, deployment, migrations, user-visible
behavior, significant business rules, security constraints or operational procedures
inaccurate.

Do not duplicate trivial implementation details when code is the better source of truth.
Use `technical-writer` for substantial documentation work.

- Russian is the mandatory primary language for all human-readable documentation
  under `docs/`.
- Do not create new English-language documentation under `docs/` unless the task
  explicitly requires an English version.
- When updating an existing English-language document under `docs/`, translate the
  explanatory prose you modify into Russian when practical, but do not mass-translate
  unrelated documentation outside the current task scope.
- Keep code, commands, configuration keys, API names, file paths, identifiers,
  library/framework names, protocol names, and other technical literals in their
  original form when translation would reduce clarity or accuracy.
- Do not manually translate generated documentation or vendored third-party content.
- Write all explanatory prose in Russian.

# Codex backlog

Large project work is decomposed into tasks under `codex-backlog/tasks/`.

When a task file is explicitly provided:

- read `codex-backlog/GLOBAL_RULES.md`;
- work only within the scope of that task;
- do not start later numbered tasks;
- treat the current code, Git history, and current documentation as the source
  of truth for completed previous stages;
- do not read all files under `codex-backlog/masters/` unless the current task
  explicitly requires clarification from a master specification.

# Git branch policy

The current long-lived implementation branch for the Codex backlog is:

`feature/yfc-platform-v2`

Before starting a backlog task, verify the current branch with:

`git branch --show-current`

For all tasks under `codex-backlog/tasks/`:

- work only in the currently checked out `feature/yfc-platform-v2` branch;
- do not create another branch;
- do not switch or checkout another branch;
- do not merge or rebase `main`, `master`, `develop`, or another branch;
- do not modify another worktree;
- do not push unless explicitly requested by the user;
- create the task's logical commit in the current branch;
- if the expected branch is not active, stop before making changes and report it;
- keep unrelated user changes intact.

# Production and infrastructure safety

Treat schema migrations, deployment configuration and infrastructure changes as production
changes. Do not run production deployment scripts, destructive production database actions,
or modify production auth, secrets, DNS, Cloudflare or external infrastructure unless the
user explicitly requested that operation.

# Environment safety

During backlog implementation and testing:

- never deploy to production unless explicitly requested;
- never run database migrations against production;
- never use production credentials for local or automated tests;
- never modify production data;
- prefer local/test/staging services;
- before running any command that appears to target production, stop and ask the user.

# Final verification

Before declaring substantial work complete:

- review `git diff`;
- confirm no accidental files exist outside `.artifacts/`;
- confirm no secrets or debug artifacts were introduced;
- run broad relevant checks for every touched subsystem;
- confirm migrations and generated artifacts are intentional;
- verify the main changed user flow;
- visually verify UI when UI changed;
- confirm relevant documentation is still accurate;
- confirm the repository is not knowingly broken.

Do not claim a check passed unless it was actually run. If a relevant check could not be run,
state exactly which check was skipped and why.

# Final report

Report concisely:

- what changed;
- commits/stages created;
- tests and checks actually run;
- migration/deployment implications;
- remaining risks or limitations.

Do not list hypothetical checks as completed.
