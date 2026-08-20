# TASK 53. Адаптация сегодняшней тренировки — UX

- Фаза: **Training UX**
- Приоритет: **53/93**
- Зависит от: `35`, `40`, `46`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Быстро адаптировать текущую тренировку по времени/оборудованию/замене.

## In scope

- Entry Today/Active; presets; preview diff; curated alternatives; apply/cancel; history provenance; medical/pain boundary; mobile.

## Design V2 contract

Adaptation flow продолжает Design V2 active-workout language и использует shared sheet/dialog, selection, diff и action primitives. Прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`; не создавать отдельный workout skin или navigation pattern. Проверить в реальном браузере light/dark, desktop/mobile и active/error states.

## Out of scope

Без новой программы, AI и silent future changes.

## Проверки

Preview/apply/cancel, time budgets, missing alternative, active state, history.

## Done when

Изменение конкретной тренировки быстрое и прозрачное.

## Рекомендуемый commit

`feat(ui): add workout adaptation flow`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
