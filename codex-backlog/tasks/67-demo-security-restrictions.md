# TASK 67. Demo Mode - security и side-effect restrictions

- Фаза: **Demo security**
- Приоритет: **67/93**
- Зависит от: `66`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$security-engineer`, `$qa-engineer`, `$backend-engineer`

## Цель

Защитить публичный anonymous demo и подтвердить server-side enforcement для чувствительных возможностей.

## In scope

Focused threat model и enforcement для:
- AI Coach;
- trainer/client invitations;
- account linking;
- Telegram/push/email notifications;
- persistent uploads;
- export real/server user data;
- payments;
- admin/moderation;
- social/sharing;
- persistent writes к настоящим/чужим records.

Проверить data isolation:
- no arbitrary real-user data;
- fixtures не из production users;
- fixture IDs не target real rows;
- demo state не становится trusted ownership token;
- caches/session state scoped correctly.

Если есть новые anonymous server endpoints - переиспользовать существующие rate limits/security middleware.

Никаких AI/provider keys, Telegram bot secrets, privileged tokens, DB credentials или granting identifiers в client bundle.

Тестировать direct route/API/backend attempts, а не только disabled UI.

## Out of scope

Не добавлять новую глобальную security-платформу, новую auth систему или новые продуктовые функции.

## Проверки

Security regression: direct AI/API, invitations/linking/notifications, persistent writes, IDOR/cross-user, malicious fixture IDs, rate limits, secret scan, demo/auth isolation.

## Done when

Demo безопасен для anonymous internet access, backend реально блокирует side effects, fixtures/temp state изолированы.

## Рекомендуемый commit

`security(demo): enforce anonymous demo boundaries`

## Процесс и отчёт

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.
Работать только в текущей выделенной feature-ветке. Не создавать и не переключать ветки,
не merge/rebase и не deploy в production без прямого указания владельца.
Не переходить к следующему task.

После изменений запустить только профильные проверки согласно `AGENTS.md`, проверить `git diff`
и создать один логический commit, если task меняет tracked files.

В финальном отчёте перечислить:
- изменения;
- ключевые файлы;
- миграции;
- реально запущенные проверки;
- ограничения;
- commit hash.
