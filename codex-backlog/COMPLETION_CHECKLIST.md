# Completion checklist - release backlog v11

## Per task

- [ ] Worked only in `feature/yfc-platform-v2`.
- [ ] Read root `AGENTS.md`, `GLOBAL_RULES.md`, lifecycle, current task and primary role.
- [ ] Loaded only core `Рекомендуемые skills` initially.
- [ ] Loaded each `Условный skill` only after its actual trigger was proven.
- [ ] Ran only the exact additional lifecycle roles declared by the task.
- [ ] Did not create an agent per skill or automatic researcher/reviewer/QA chain.
- [ ] Read `ACTIVE_DESIGN_SOURCE.md` before visual work.
- [ ] For tasks `49B1-49G`, followed applicable `DESIGN_ALTERNATIVES_EXPLORATION_CONTRACT.md`.
- [ ] For client-facing UI, preserved `GLOBAL_RULES.md` UI consistency contract and did not create a local duplicate primitive/system.
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

## Current task 49B1 consistency checkpoint

- [ ] Audited real rendered UI once and covered each distinct UI pattern family rather than every duplicate route.
- [ ] Built component inventory and froze one baseline finding set before remediation.
- [ ] Closed all in-scope `MUST_FIX` findings without importing Direction A/B/C.
- [ ] Preserved business logic/API/schema/auth contracts.
- [ ] Verified mobile-first baseline plus representative desktop/light/dark states.
- [ ] Independent review/QA verified the frozen set and regressions instead of starting a second product-wide audit.


## Release gates

- [ ] Tasks `00-49B` remained untouched as completed history.
- [ ] Task `49B1` completed before `49C`.
- [ ] Design V2 remained active through `49B1` and until explicit owner decision/closure in `49C-49G`.
- [ ] Task `50A` did not start before `49G` closure.
- [ ] Task `76` has no open release-blocking P0/P1.
- [ ] Task `77` evidence is factual.
- [ ] Task `78` production evidence exists.
- [ ] Task `79` contains go/no-go evidence.
