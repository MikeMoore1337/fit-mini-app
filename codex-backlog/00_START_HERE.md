# Your Fitness Coach - backlog первого публичного релиза v11

Эта версия сохраняет production-качество и resource-aware lifecycle, но добавляет один ограниченный checkpoint для фактической UI consistency перед design owner decision.

## Текущее состояние

- tasks `00-49B` подтверждены как завершённые;
- Design V2 остаётся текущим production source of truth;
- `49A` и `49B` уже подготовили три design alternatives без изменения production UI;
- из-за смены правил/ролей/skills на предыдущих этапах перед `49C` выполняется один current-state normalization checkpoint `49B1`;
- `49B1` не выбирает новый дизайн - она приводит фактическую реализацию текущего V2 к общей component/token/mobile системе.

## Текущая задача

```text
49b1-current-ui-consistency-mobile-first-normalization.md
```

Не запускать заново `00-49B`. После успешного `49B1` следующая task - `49C`.

## Design alternatives flow

```text
49A  targeted brief/current-state delta [done]
49B  exactly three cross-surface directions + renders [done]
49B1 current Design V2 UI consistency + mobile-first normalization [CURRENT]
49C  compare normalized V2/A/B/C + owner selection

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

49G -> 50A mobile/TMA quality foundation
```

## Что изменено в v11

- Добавлена `49B1` с реальным browser visual audit, component inventory и mobile-first normalization.
- Audit в `49B1` формирует один frozen finding set до fixes, поэтому review не превращается в бесконечный повторный поиск проблем.
- В `GLOBAL_RULES.md` добавлен короткий `UI consistency contract` для всех будущих client-facing tasks.
- Новые feature tasks обязаны сохранять shared tokens/components/sizes/states, но проверяют только свою изменённую поверхность, а не весь продукт.
- `49C` сравнивает alternatives с актуальной normalized Design V2 baseline после `49B1`.
- Resource-aware review policy `BLOCKER/HIGH only` сохранена.

Подробности: `TASK_EXECUTION_LIFECYCLE.md`, `SKILL_ASSIGNMENT_MATRIX.md`, `BACKLOG_V11_CHANGELOG.md`.
