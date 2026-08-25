# Your Fitness Coach - backlog первого публичного релиза v11

Backlog использует resource-aware lifecycle. Завершённые задачи архивируются в `tasks/done/` и остаются доступными для чтения.

## Текущее состояние

- tasks `00-73`, включая буквенные подзадачи, и owner-selected tasks `88-89` подтверждены как завершённые;
- завершённые task-файлы перенесены в `tasks/done/` без переименования;
- `DESIGN_V2_1` остаётся единственным active production source of truth;
- current task — `89A`, назначена в `PENDING` и не начата.

## Текущая задача

```text
89a-telegram-news-publication-composition-preview-parity.md
```

Не запускать заново `00-73` и `88-89`. Task `89A` не реализуется в completion run task `89`.
После успешной task `89A` следующая task owner-selected Telegram news потока — `90`;
автоматически её не начинать.

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
50-73 feature/release tasks [done]
88 Telegram news ingestion/editorial drafts [done]
89 Telegram news images/moderation/publishing [done]
89A Telegram news exact composition/preview parity [CURRENT, PENDING]
```

## Что изменено в v11

- Добавлена `49B1` с реальным browser visual audit, component inventory и mobile-first normalization.
- Audit в `49B1` формирует один frozen finding set до fixes, поэтому review не превращается в бесконечный повторный поиск проблем.
- В `GLOBAL_RULES.md` добавлен короткий `UI consistency contract` для всех будущих client-facing tasks.
- Новые feature tasks обязаны сохранять shared tokens/components/sizes/states, но проверяют только свою изменённую поверхность, а не весь продукт.
- `49C` сравнивает alternatives с актуальной normalized Design V2 baseline после `49B1`.
- Resource-aware review policy `BLOCKER/HIGH only` сохранена.

Подробности: `TASK_EXECUTION_LIFECYCLE.md`, `SKILL_ASSIGNMENT_MATRIX.md`, `BACKLOG_V11_CHANGELOG.md`.
