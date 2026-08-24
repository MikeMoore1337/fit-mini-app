# Project context

Your Fitness Coach is one product exposed through the browser and Telegram Mini App,
with a shared backend and PostgreSQL database.

Main areas:

- `frontend/` - React, TypeScript, Vite, TanStack Query;
- `backend/` - Python 3.14, FastAPI, SQLAlchemy, Alembic;
- `bot/` - Python 3.14, Aiogram;
- `scripts/` - project automation, checks, maintenance, deployment helpers;
- Docker Compose - local and production-oriented orchestration.

Preserve the current architecture and repository conventions unless the current task
explicitly requires a change or there is a concrete technical reason to change them.

# Instruction precedence and source of truth

Use this order for the current work:

1. explicit user instructions in the current session;
2. current task and its backlog `GLOBAL_RULES.md`;
3. current backlog `TASK_EXECUTION_LIFECYCLE.md`;
4. this root `AGENTS.md`;
5. assigned role from `.agents/roles/`;
6. task-recommended skills from `.agents/skills/`;
7. relevant long-term documentation under `docs/`.

Destructive, production-affecting, credential, billing and real-user operations still require
explicit user authorization when required by the safety rules below.

For already implemented behavior, current code, migrations, tests, Git history and active
documentation are the source of truth. The task defines the intended change, not assumed
current state.

Do not load unrelated tasks, roles, skills, masters or historical documents merely because
they exist.

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
why where appropriate.

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

For any user-facing seven-day week context or date selector, reuse the shared frontend
`WeekStrip` component and its documented `overview`/`picker` modes. Do not create page-local week
markup or a parallel responsive visual system. Keep adjacent page content in normal layout flow;
do not overlap the week strip with negative margins or absolute positioning. Verify adjacent
bounding boxes at desktop and relevant mobile widths; see `docs/design/component-principles-v2.md`.

# Skills

Repository skills live under `.agents/skills/`.

- For a backlog task, `Рекомендуемые skills` are the **core skills** for the primary role. Open
  only these initially.
- `Условные skills` are not preload instructions. Open one only after inspection proves its
  documented trigger is actually present in the current implementation/fix.
- For code/diff review, reviewer may use `$code-reviewer`; QA uses `$qa-engineer`. These base
  skills need not be repeated in task metadata. A non-code design/decision review does not load
  `$code-reviewer` automatically. Add at most 1-2 task-specific review skills for a normal pass.
- Do not load every skill merely because the product surface could theoretically involve it.
  In particular, visible-in-TMA UI does not by itself require `$telegram-engineer`; ordinary UI
  does not by itself require a separate `$accessibility-engineer` pass.
- A skill never expands task scope. New schema/API/platform/product work requires the task or a
  reproducible `BLOCKER/HIGH`, not a broad skill checklist.
- Repository/backlog rules take precedence over generic skill guidance when they conflict.

# Agent roles and subagents

Reusable role contracts live under `.agents/roles/`.

- Role defines responsibility; skill defines domain workflow; task defines result and scope.
- For a backlog task, `Основная роль` and `Дополнительные роли lifecycle` are authoritative.
- Read only the assigned primary role initially. Do not synthesize the old automatic chain
  `researcher -> implementer -> independent-reviewer -> qa-verifier`.
- Add a role only when the task explicitly lists it, it is the primary role, or the lifecycle
  allows a narrowly triggered conditional role.
- Keep one primary production writer for a normal task. A reviewer/QA pass is read-only; any
  subsequent fix returns to the primary writer.
- Do not create an agent per skill or re-read unchanged role/skill files after every pass.
- Use `.agents/references/ROLE_ROUTING_GUIDE.md` only when routing/delegation is actually needed.
- Do not let multiple write-agents edit the same working tree or core contract concurrently.
- `orchestrator` or `integration-release` does not override branch/worktree restrictions.
- If real subagents are unavailable, perform required role stages as clearly separated
  sequential passes in the same session and report that accurately.

# Backlog routing and full task lifecycle

Current backlog families include:

- `codex-backlog/tasks/`;
- `codex-backlog/bugs/pending/` for owner-selected standalone bug-fix tasks;
- `codex-backlog/telegram-core-release-backlog/tasks/`;
- `post-release-priority-backlog/tasks/`.

When a task file is explicitly provided:

1. identify its backlog root from the task path;
2. read this `AGENTS.md`;
3. read that backlog's `GLOBAL_RULES.md`;
4. read that backlog's `TASK_EXECUTION_LIFECYCLE.md`;
5. read the current task and its assigned role;
6. open the task's core `Рекомендуемые skills`; open `Условные skills` only on their actual trigger;
7. execute only the `Основная роль` plus the exact `Дополнительные роли lifecycle` declared by the task;
8. execute only the current task;
9. do not start the next task automatically.

The phrase `полный task lifecycle` always means the `TASK_EXECUTION_LIFECYCLE.md` belonging to
the current task's backlog. That file is the canonical implementation/review/QA/finalization
workflow. Do not duplicate it with an improvised workflow.

The phrase `Все предыдущие tasks считаются выполненными` is only a sequencing assumption. It
does not pass owner checkpoints, create missing Trigger/evidence, authorize production or
external actions, provide secrets/tokens, override conditional/skip rules, or prove real-user,
Telegram, provider or production validation.

For standardized backlog tasks, normally create one logical commit only after applicable
review, QA and final verification. Do not create intermediate lifecycle commits unless the
current task/backlog explicitly requires them. A read-only/no-code outcome does not require a
manufactured commit.

Do not read all files under `masters/`, completed tasks or historical changelogs unless the
current task explicitly requires them.

# Resource-aware review and stop policy

For backlog tasks, severity determines whether work continues:

- `BLOCKER` and `HIGH` block completion and must be fixed or reported as a blocker.
- `MEDIUM`, `LOW`, `NIT` and `OUT_OF_SCOPE` are non-blocking. They must not trigger a new
  architecture/data/API/platform workstream.
- Every `MEDIUM` or `LOW` finding from any task, review, QA or audit must be added or updated in
  `codex-backlog/bugs/FINDINGS.md` before commit and finalization, even when fixed in the same
  task. A chat final report or an ignored `.artifacts/` report is not durable tracking.
- If a finding is fixed and verified in the current task, do not create a separate bug task. An
  unresolved finding becomes a file under `codex-backlog/bugs/pending/` only after triage and an
  explicit owner decision; bug tasks do not enter or advance the main product-task sequence.
- Keep resolved entries in that registry and update their status/verification instead of deleting
  them. The primary agent owns registry synchronization; read-only reviewer/QA roles return the
  required registry-ready details.
- A finding cannot be labelled `MEDIUM` and still be used to prevent commit. If it truly makes
  the task unacceptable, the reviewer must reclassify it as `HIGH/BLOCKER` with reproducible
  evidence tied to the task or regression introduced by the current diff.
- The first independent review is the only full review pass. After `BLOCKER/HIGH` fixes, perform
  only the targeted recheck defined by the backlog lifecycle - do not restart a fresh audit.
- Normal tasks have a finite review/QA budget. Respect `TASK_EXECUTION_LIFECYCLE.md` limits and
  stop with an exact blocker instead of looping.
- A dedicated later review/audit task is a reason not to duplicate the same full review in the
  preceding implementation task unless that task explicitly requires it.

Prefer targeted checks, relevant files, compact subagent context and closed finding sets. More
roles, more skills and more passes are not inherently higher quality.

# Git branch and worktree policy

Before changing files for a backlog task, verify the branch with:

`git branch --show-current`

The current backlog's `GLOBAL_RULES.md` defines the expected branch.

For `codex-backlog/tasks/`, `codex-backlog/bugs/pending/` and
`codex-backlog/telegram-core-release-backlog/tasks/`, the expected long-lived implementation
branch is:

`feature/yfc-platform-v2`

Unless the current backlog rules or user explicitly permit otherwise:

- do not create another branch;
- do not switch/checkout another branch;
- do not merge or rebase unrelated branches;
- do not modify another worktree;
- do not push;
- keep unrelated user changes intact.

If the expected branch is not active, stop before tracked changes and report the mismatch.

Parallel write-agents/worktrees are allowed only when the current backlog rules, task or user
explicitly permits them. Do not infer permission from the existence of multi-agent roles.

# Dependencies

- Add or upgrade dependencies only when justified by the task.
- Prefer maintained, narrowly scoped dependencies and consider security plus bundle/runtime cost.
- Update the appropriate lock/compiled dependency files and keep dependency diffs intentional.
- Do not perform broad dependency upgrades as part of unrelated work.

# Testing and verification

Use risk-based testing. Changes to business logic, API behavior, permissions, state
transitions, calculations, persistence, parsing/validation or regression-prone UI behavior
normally require appropriate tests.

Test meaningful boundaries and failure paths, not only happy paths. Prefer deterministic
waits/assertions over sleeps. Add a regression test for a meaningful bug fix when practical.

For normal backlog tasks:

- run targeted/profile-specific checks required by the task, affected subsystems,
  `GLOBAL_RULES.md` and relevant skills;
- do not run the full repository suite by default;
- expand verification only when the actual risk justifies it.

Broader/full verification is appropriate when explicitly required or when changes affect
shared contracts, migrations, auth/RBAC, build/deployment infrastructure, broad generated
artifacts, cross-cutting integration or a release/integration gate.

Do not claim a check passed unless it was actually run. State exactly what could not be run
and why.

# UI verification

For UI changes, verify the main affected user flow and relevant responsive states.

When working in the Codex IDE extension, use Playwright MCP for local visual and functional
verification, including interactions, responsive states, screenshots and console errors.

Do not use the Browser skill or In-app Browser in Codex IDE when that integration is not
supported in the current environment. This does not replace existing project e2e scripts or
browser tooling in other environments.

For Mobile Web/TMA/client-facing tasks, follow the current backlog's mobile/TMA contracts,
acceptance matrix and relevant listed skills.

# Security baseline

Never commit passwords, API or Telegram bot tokens, private keys, session secrets,
production credentials, real `.env` files or credentials copied into tests/documentation.
Use `.env.example` only for variable names and safe example/default values.

Authentication, authorization, user/trainer data isolation and critical validation must not
rely on hidden UI, frontend state, routes or Telegram client state. Do not expose secrets or
internal stack traces in user-visible errors or logs.

Use `security-engineer` for security-sensitive implementation, audit or threat modeling.

# Documentation baseline

Treat `docs/` as long-term architectural and operational context. Before changing an existing
subsystem, check for relevant documentation.

Update documentation in the same task when a change makes documented setup, environment
variables, commands, API contracts, architecture, deployment, migrations, user-visible
behavior, significant business rules, security constraints or operational procedures
inaccurate.

Do not duplicate trivial implementation details when code is the better source of truth.
Use `technical-writer` for substantial documentation work.

- Russian is the mandatory primary language for all human-readable documentation under
  `docs/`.
- Do not create new English-language documentation under `docs/` unless the task explicitly
  requires an English version.
- When updating an existing English-language document under `docs/`, translate the
  explanatory prose you modify into Russian when practical, but do not mass-translate
  unrelated documentation outside the current task scope.
- Keep code, commands, configuration keys, API names, file paths, identifiers,
  library/framework names, protocol names and other technical literals in their original form
  when translation would reduce clarity or accuracy.
- Do not manually translate generated documentation or vendored third-party content.
- Write all explanatory prose in Russian.

# Production and infrastructure safety

Treat schema migrations, deployment configuration and infrastructure changes as
production-sensitive.

Do not:

- deploy to production unless explicitly requested;
- run database migrations against production;
- modify production auth, secrets, DNS, Cloudflare or external infrastructure without explicit
  user authorization;
- rotate/revoke real tokens without explicit authorization;
- modify real user data;
- use production credentials for local or automated tests;
- invoke real paid external services unless explicitly authorized.

Prefer local/test/staging services.

Before a command that appears destructive, production-targeting, unusually expensive or
outside task scope, stop and ask the user.

Normal local linting, formatting, type checking, targeted tests, builds and local browser
verification do not require additional confirmation.

# Completion and final report

Before declaring tracked backlog implementation complete:

- complete the current backlog lifecycle;
- inspect the final `git diff`;
- confirm no accidental files exist outside `.artifacts/`;
- confirm no secrets or debug artifacts were introduced;
- confirm migrations, generated files, dependencies and configuration changes are intentional;
- confirm all blocking `BLOCKER/HIGH` review/QA findings are resolved or explicitly blocked;
- keep `MEDIUM/LOW/NIT/OUT_OF_SCOPE` as concise non-blocking follow-ups rather than reopening scope;
- confirm every new or changed `MEDIUM/LOW` is synchronized in
  `codex-backlog/bugs/FINDINGS.md` and cite its ID/status in the final report;
- create the task's one logical commit only after successful applicable verification;
- do not start the next task.

For backlog tasks, follow the current `TASK_EXECUTION_LIFECYCLE.md` final-report contract.

For other substantial work, report concisely:

- what changed;
- checks actually run;
- migration/config/deployment implications;
- remaining risks or limitations;
- commit hash or explicit `no commit`.

Never list hypothetical checks as completed or claim independent review, QA, real-user,
Telegram, provider or production validation if it did not actually happen.
