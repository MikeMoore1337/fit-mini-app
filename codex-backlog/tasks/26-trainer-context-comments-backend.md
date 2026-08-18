# TASK 26. Контекстные комментарии тренера - backend и permissions

- Фаза: **Trainer collaboration domain**
- Приоритет: **26/93**
- Зависит от: `21`, `25`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$security-engineer`, `$qa-engineer`

## Цель

Добавить минимальную contextual feedback system: trainer comment к workout и при необходимости к exercise. Это не чат/мессенджер.

## In scope

Сначала убедиться, что current code не получил comment/feedback model к моменту task.

Минимальные targets: workout и optional workout_exercise внутри конкретного workout. Comment: id, trainer author, client context, workout, optional exercise, body, created_at, edited/history semantics. Не generic free-floating chat.

Permissions: только действующий закреплённый trainer пишет в client context; client читает свой context; unrelated trainer/user не видит/не пишет. После revoke явно определить read-history policy, новые comments запрещены.

History chronological; не перезаписывать один note. Edit — либо audit/revision, либо updated_at + audit. Plain text/controlled formatting, limits, safe render.

Notifications: existing in-app + Telegram if linked/allowed. Telegram лишь signal/preview/deep link, source of truth остаётся в приложении. Deep link ведёт к разрешённому workout/exercise context. Operational logs не должны хранить полный sensitive comment без необходимости.

## Out of scope

Не делать messenger, sockets, typing/read receipts, attachments/voice/video, AI comments или unrelated-user communication.

## Проверки

Assigned/unassigned/former trainer, wrong workout owner, exercise belongs/does not belong, history, revoke, notifications, linked/unlinked Telegram, XSS/limits, deep-link authorization.

## Done when

Комментарии контекстно привязаны к workout/exercise, имеют history/permissions и уведомления; generic messenger не создан.

## Рекомендуемый commit

`feat(coach): add contextual workout feedback comments`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
