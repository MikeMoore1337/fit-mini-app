# TASK 36. Offline-safe active workout

- Фаза: **Reliability**
- Приоритет: **36/93**
- Зависит от: `29`, `35`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Не терять введённые подходы при плохой связи, refresh или закрытии TMA.

## In scope

- Проверить current persistence/API mutations.
- Local durable draft/queue только для active workout minimum data.
- Network loss, offline set edits, reconnect, refresh, TMA reopen, safe retry.
- Backend idempotency/version semantics, duplicate prevention, stale/conflict policy.
- Draft scoped to account/workout; logout/account switch isolate/clear; no auth bypass.
- Clear stale queue after sync. Web + TMA.

## Out of scope

Не делать весь продукт offline, не кешировать лишние personal data, не вводить service worker/background sync без необходимости.

## Проверки

Offline edits, reconnect, duplicate retry, refresh, logout/switch, stale server, two tabs, storage corruption.

## Done when

Активная тренировка восстанавливается и синхронизируется без потери/дубликатов.

## Рекомендуемый commit

`feat(workouts): make active sessions offline safe`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
