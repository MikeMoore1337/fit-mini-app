# TASK 52. Адаптивная калорийность — UX

- Фаза: **Nutrition UX**
- Приоритет: **52/93**
- Зависит от: `33`, `41`, `43`, `51`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Показать adaptive expenditure/calorie proposal прозрачно и с подтверждением.

## In scope

- Estimate/period/sufficiency; explain logged intake + weight trend; insufficient-data guidance; current->proposed diff; macros through deterministic rules; accept/reject; target history; knowledge link.

## Out of scope

Без exact TDEE promise, AI и auto-apply.

## Проверки

Insufficient/sufficient, no-change/proposal, accept/reject, goal changes, mobile/a11y.

## Done when

Пользователь понимает оценку и сам подтверждает изменение.

## Рекомендуемый commit

`feat(ui): add adaptive calorie calibration experience`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
