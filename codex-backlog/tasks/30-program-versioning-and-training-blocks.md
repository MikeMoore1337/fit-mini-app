# TASK 30. Версионирование программ и тренировочные блоки

- Фаза: **Program domain**
- Приоритет: **30/93**
- Зависит от: `25`, `26`, `29`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Сделать изменения программы прозрачными и добавить простой block-level lifecycle.

## In scope

- Program revisions/snapshots: who/when/what changed + optional reason.
- Self vs trainer changes.
- Completed historical workouts immutable; documented policy для future planned workouts.
- Training block: title, dates/duration, purpose/goal, optional priority muscles, notes, status.
- Optional deload marker only; no auto-prescription.
- Trainer permissions/revoke.
- Подготовить context для future AI, без AI.

## Out of scope

Без auto-periodization, automatic deload, complex merge/rollback UI и AI writes.

## Проверки

Revision history, concurrent edits, trainer revoke, past/future workout behavior, blocks overlap/lifecycle.

## Done when

Есть надёжная история программы и последовательные тренировочные блоки.

## Рекомендуемый commit

`feat(programs): add revisions and training blocks`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
