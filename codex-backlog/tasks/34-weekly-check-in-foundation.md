# TASK 34. Еженедельный check-in

- Фаза: **Progress / Coaching foundation**
- Приоритет: **34/93**
- Зависит от: `27`, `31`, `32`, `33`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Создать weekly feedback loop без обязательного AI.

## In scope

- Deterministic weekly summary: nutrition/adherence, training adherence, weight trend, anthropometry only if sufficient, relevant progression, current goal.
- Optional subjective inputs: training load, recovery, hunger/adherence difficulty, note.
- History/version/date/user ownership.
- Trainer sees own client only if permitted.
- Notification via existing preferences; skip allowed.
- Future AI reads structured check-in.

## Out of scope

Без medical questionnaire, overtraining diagnosis, mandatory completion, wearables и AI summary.

## Проверки

Week/timezone, skip, duplicate week, optional fields, trainer revoke, notification.

## Done when

Weekly check-in полезен сам по себе и создаёт structured context для будущего Coach.

## Рекомендуемый commit

`feat(progress): add weekly check-ins`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
