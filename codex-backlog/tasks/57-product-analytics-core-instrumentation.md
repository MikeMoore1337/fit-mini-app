# TASK 57. Инструментация ключевых product funnels

- Фаза: **Product analytics**
- Приоритет: **57/93**
- Зависит от: `37`, `38`, `40`, `41`, `44`, `47`, `51`, `52`, `53`, `55`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Подключить event contract к реальным core flows после UI.

## In scope

- Public->demo/login; auth; onboarding; program start; workout start/complete; food log; measurement; check-in; adaptation; trainer workflow; later AI events remain 83/84; no-sensitive-payload + dedupe.

## Out of scope

Без content payloads, every-click tracking и BI.

## Проверки

Representative funnels, no duplicates, SPA/demo/auth distinction, sensitive payload tests.

## Done when

После релиза измеряются ключевые funnels без лишних персональных данных.

## Рекомендуемый commit

`feat(analytics): instrument core product funnels`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## Final release integration: activation and reminders

Добавить high-level события без sensitive payload:
- onboarding_started / onboarding_completed;
- progression_suggestion_shown / dismissed (без веса/повторов);
- notification_preferences_changed (без quiet-hour exact value при ненужности);
- data_export_requested;
- account_delete_started/completed;
- cardio_logged (без distance/HR values).
