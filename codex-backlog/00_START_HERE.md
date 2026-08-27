# Your Fitness Coach - backlog первого публичного релиза v12

Backlog использует resource-aware lifecycle. Завершённые задачи архивируются в `tasks/done/` и остаются доступными для чтения.

## Текущее состояние

- tasks `00-75A`, включая буквенные подзадачи и `74A`, а также owner-selected tasks `103-105`
  подтверждены как завершённые;
- завершённые task-файлы перенесены в `tasks/done/` без переименования;
- `DESIGN_V2_1` остаётся текущим production baseline, но полностью пересматриваем в отдельной
  owner-approved design task;
- task `75A` завершила Rethink-аудит, получила screenshot approval и owner decision
  `START_RETHINK_EXPLORATION`, затем архивирована;
- task `75B` назначена current explicit exploration/selection gate, но ещё не начата;
- `DESIGN_V2_1` остаётся production baseline до отдельного selection/specification/pilot gate.

## Текущая задача

```text
75b-product-design-motion-rethink-exploration.md [CURRENT PENDING NOT STARTED]
```

Не запускать заново `00-75A`, `74A` и `103-105`. Назначение `75B` не запускает exploration,
prototypes, specification, pilot, rollout или task `76` в completion run `75A`.

## Design alternatives flow

```text
49A  targeted brief/current-state delta [done]
49B  exactly three cross-surface directions + renders [done]
49B1 current Design V2 UI consistency + mobile-first normalization [done]
49C  compare normalized V2/A/B/C + owner selection [done]

KEEP_V2_UNCHANGED
  -> skip 49D-49F
  -> 49G closure

V2.1 / A / B / C / explicit hybrid
  -> 49D final responsive specification
  -> owner approval
  -> 49E production-realistic pilot
  -> owner manual test
  -> 49F final owner approval
  -> 49G conditional rollout + backlog alignment

49G -> 50A mobile/TMA quality foundation [done]
50-74A feature/release/hardening tasks [done]
75 performance/motion hardening [COMPLETED]
75A design/UX/UI/motion Rethink audit [COMPLETED]
  -> KEEP: continue to 76
  -> EVOLVE: bounded remediation
  -> RETHINK [SELECTED]: 75B isolated exploration + owner selection
75B product-wide visual + motion directions [CURRENT, PENDING]
  -> selected direction: separate specification/pilot/rollout/performance verification
  -> keep/stop: continue to 76
  -> 76 only after resolved owner decision and release state
103-105 owner-selected Telegram news flow [done]
```

## Что изменено в v12

- Добавлены design guardrails v6, `$motion-design-engineer` и explicit-only `$ui-prototyper`.
- Удалён дублирующий `$commercial-product-builder`; pending tasks переведены на реальные domain skills.
- Design V2/V2.1 теперь current baseline обычных tasks, а не вечная эстетическая догма.
- Task `75` зафиксирована как завершённая по подтверждению владельца.
- `75A` завершена с решением `START_RETHINK_EXPLORATION`; добавлена и назначена `75B` для
  isolated directions и owner selection без production changes.
- Resource-aware review policy `BLOCKER/HIGH only` сохранена; `MEDIUM/LOW` синхронизируются в
  `bugs/FINDINGS.md`.

Подробности: `TASK_EXECUTION_LIFECYCLE.md`, `SKILL_ASSIGNMENT_MATRIX.md`, `ACTIVE_DESIGN_SOURCE.md`.
