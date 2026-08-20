# TASK 59. Единая система уведомлений и напоминаний

- Фаза: **Platform / Engagement**
- Приоритет: **59/93**
- Зависит от: `33`, `38`, `44`, `47`, `50`, `53`, `56`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Собрать разрозненные уведомления в единый channel-aware contract,
чтобы reminders были полезными, не дублировались и уважали пользователя.

## In scope

1. Сначала инвентаризировать current notification/bot/background-job infrastructure.
Не создавать второй scheduler или второй notification model без необходимости.

2. Разделить:
   - transactional/product events;
   - optional reminders.
Не смешивать с marketing campaigns.

3. Минимальные категории:
   - upcoming workout reminder;
   - trainer contextual comment;
   - trainer program update;
   - weekly check-in reminder;
   - optional measurement reminder;
   - invitation/relationship events, если уже есть.

4. Notification preferences:
   - per-category enable/disable там, где это уместно;
   - timezone-aware scheduling;
   - quiet hours;
   - sensible defaults;
   - trainer/security-critical transactional events не маскировать как обычный reminder.

5. Channels:
   - in-app notification center/current existing in-app mechanism;
   - Telegram channel для Telegram-linked user;
   - Web Notification API только если current architecture/support делает это оправданным.
Не вводить mandatory browser push infrastructure ради feature parity.

6. Deep links:
   - ведут в правильный screen/entity;
   - безопасный internal destination;
   - Web/TMA aware;
   - revoked/deleted entity даёт graceful fallback.

7. Delivery semantics:
   - idempotency;
   - dedupe;
   - retry/backoff;
   - cancelled/rescheduled workout не должен прислать старый reminder;
   - timezone/DST edge cases.

8. Не отправлять contents, которые раскрывают лишние sensitive данные на lock screen,
если можно использовать нейтральный текст.

9. Settings UX:
   - понятно;
   - не десятки микротумблеров;
   - mobile/TMA friendly;
   - quiet hours optional.

10. Observability:
   - delivery failure counts;
   - без PII/body data в обычных operational logs.

## Design V2 contract

Notification center, settings и deep-link fallback используют shared Design V2 list, form, status и feedback primitives; Telegram delivery не вводит отдельный product visual language. Перед UI-работой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`, проверить light/dark, desktop/mobile/TMA и empty/error/permission states в реальном браузере.

## Out of scope

Не делать маркетинговые рассылки.
Не спамить пользователя за каждый food log.
Не добавлять email/SMS только ради количества каналов.
Не строить сложную CRM.
Не создавать отдельный chat/messenger.

## Проверки

Timezone/DST; quiet hours; dedupe; retry; reschedule/cancel; Telegram linked/unlinked;
revoked trainer; disabled category; deep link auth; deleted entity; duplicate job;
no sensitive notification payload regression.

## Done when

У приложения есть одна согласованная notification architecture с управляемыми reminders,
корректным Telegram/in-app delivery и защитой от дублей/спама.

## Рекомендуемый commit

`feat(notifications): unify reminders and delivery preferences`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными.
Текущий код, Git history и актуальный `docs/` — source of truth по их результатам.

Не проводить повторный полный аудит репозитория.
Не перечитывать все предыдущие task-файлы.
Не читать весь `codex-backlog/masters/` без необходимости.

Если текущий task явно относится к одному master-документу,
прочитать только этот master.

Если предыдущий audit уже исследовал нужную область и результат доступен,
переиспользовать его; точечно перепроверять только факты, которые могли измениться.

Сначала прочитать текущий task, затем исследовать только релевантный набор файлов
и подсистем, необходимый для корректного выполнения задачи.

Если требуемая функциональность уже существует:
- не реализовывать её заново;
- переиспользовать текущую архитектуру;
- закрыть только реальные gaps.

Не расширять scope самостоятельно.

Если для выполнения нужен крупный architectural change вне scope:
- не начинать его автоматически;
- зафиксировать follow-up;
- выполнить безопасную часть текущего task, если возможно.

Работать только в текущей feature-ветке.

Не:
- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- переходить к следующему task.

После реализации:
1. только профильные проверки согласно `AGENTS.md`;
2. не запускать полный test suite без необходимости;
3. проверить `git diff`;
4. создать один логический commit при tracked changes;
5. краткий финальный отчёт: reused / changed / files / migrations-config / checks / follow-ups / commit hash.
