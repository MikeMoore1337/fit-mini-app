# TASK 35. Детерминированная адаптация сегодняшней тренировки

- Фаза: **Training adaptation**
- Приоритет: **35/93**
- Зависит от: `23`, `25`, `29`, `30`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Адаптировать конкретную тренировку под время/оборудование/замену упражнения без AI.

## In scope

- Reasons: limited time, unavailable equipment, replace exercise, different environment/equipment.
- Curated alternatives + canonical metadata; same muscle alone is not equivalence.
- Time-budget rules сохраняют high-priority/core и убирают lower-priority accessory, всегда preview.
- Replacement compatible with available equipment; explicit confirm.
- Store original/applied diff/reason/timestamp; history shows actual.
- Pain/injury context => no medical workaround, controlled safety response.

## Out of scope

Без new program generation, medical adaptation, silent future changes, random substitutions и AI.

## Проверки

Time budgets, no alternative, equipment mismatch, preview/cancel/apply, history, pain boundary.

## Done when

Пользователь безопасно адаптирует одну тренировку и видит diff до применения.

## Рекомендуемый commit

`feat(workouts): add deterministic session adaptation`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
