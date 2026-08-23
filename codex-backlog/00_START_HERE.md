# Your Fitness Coach - backlog первого публичного релиза v11

Backlog использует resource-aware lifecycle. Завершённые задачи архивируются в `tasks/done/` и остаются доступными для чтения.

## Текущее состояние

- tasks `00-55`, включая буквенные подзадачи, подтверждены как завершённые;
- завершённые task-файлы перенесены в `tasks/done/` без переименования;
- `DESIGN_V2_1` остаётся единственным active production source of truth;
- следующая task — `56`.

## Текущая задача

```text
56-unified-weekly-review-adaptive-energy.md
```

Не запускать заново `00-55`. После успешной task `56` следующая task — `57`.

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
50-55 feature tasks [done]
56 unified weekly review + adaptive energy [CURRENT]
```

## Что изменено в v11

- Добавлена `49B1` с реальным browser visual audit, component inventory и mobile-first normalization.
- Audit в `49B1` формирует один frozen finding set до fixes, поэтому review не превращается в бесконечный повторный поиск проблем.
- В `GLOBAL_RULES.md` добавлен короткий `UI consistency contract` для всех будущих client-facing tasks.
- Новые feature tasks обязаны сохранять shared tokens/components/sizes/states, но проверяют только свою изменённую поверхность, а не весь продукт.
- `49C` сравнивает alternatives с актуальной normalized Design V2 baseline после `49B1`.
- Resource-aware review policy `BLOCKER/HIGH only` сохранена.

Подробности: `TASK_EXECUTION_LIFECYCLE.md`, `SKILL_ASSIGNMENT_MATRIX.md`, `BACKLOG_V11_CHANGELOG.md`.
