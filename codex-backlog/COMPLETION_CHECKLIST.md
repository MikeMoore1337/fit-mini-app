# Completion checklist - release backlog v10

## Per task

- [ ] Worked only in `feature/yfc-platform-v2`.
- [ ] Read root `AGENTS.md`, `GLOBAL_RULES.md`, lifecycle, current task and primary role.
- [ ] Loaded only core `Рекомендуемые skills` initially.
- [ ] Loaded each `Условный skill` only after its actual trigger was proven.
- [ ] Ran only the exact additional lifecycle roles declared by the task.
- [ ] Did not create an agent per skill or automatic researcher/reviewer/QA chain.
- [ ] Read `ACTIVE_DESIGN_SOURCE.md` before visual work.
- [ ] For tasks `49A-49G`, followed `DESIGN_ALTERNATIVES_EXPLORATION_CONTRACT.md`.
- [ ] For client-facing scope, followed applicable mobile/TMA contract/matrix.
- [ ] Ran targeted checks and recorded exact commands.
- [ ] Only `BLOCKER/HIGH` blocked completion.
- [ ] `MEDIUM/LOW/NIT/OUT_OF_SCOPE` did not create new schema/API/platform/product scope.
- [ ] If blocking findings were fixed, repeat review/QA was targeted rather than a new full audit.
- [ ] Stayed within lifecycle review/QA pass limits.
- [ ] Checked final `git diff`, migrations/config/dependencies/generated artifacts.
- [ ] Did not claim real Telegram/device coverage without actual verification.
- [ ] Created one logical commit when applicable.
- [ ] Did not start the next task.

## Current task 49 resume

- [ ] Preserved and classified existing uncommitted worktree changes.
- [ ] Finished only owner-requested UI/layout/compactness refinement and regressions caused by it.
- [ ] Did not continue review-induced idempotency/schema/deep-link/Telegram architecture from non-blocking findings.
- [ ] Did not automatically revert ambiguous user/foreign hunks.

## Release gates

- [ ] Task `49` completed before `49A`.
- [ ] Design V2 remained active until explicit owner decision in `49A-49G`.
- [ ] Task `50A` did not start before `49G` closure.
- [ ] Task `76` has no open release-blocking P0/P1.
- [ ] Task `77` evidence is factual.
- [ ] Task `78` production evidence exists.
- [ ] Task `79` contains go/no-go evidence.
