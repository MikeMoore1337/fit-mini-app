# TASK 49. Комментарии тренера в workout/exercise context

- Фаза: **Coach UX**
- Приоритет: **49/93**
- Зависит от: `26`, `48`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Добавить UI contextual trainer feedback поверх backend task `26`, не превращая приложение в мессенджер.

## In scope

Trainer из client workout/history/detail оставляет comment к workout или optional exercise и видит chronological history. Client видит feedback в той же workout/exercise context и через notification/deep-link.

Composer plain-text, явный client/date/exercise context, limit/send/retry/edit-delete only if backend supports. Никаких chat bubbles/typing/replies.

History показывает author/time/edit state. Notification ведёт к target. Telegram остаётся signal/deep-link.

Former/revoked relation: composer unavailable, history строго по backend policy. Mobile trainer workflow без table-like UI.

## Out of scope

Не добавлять inbox/chat list/replies/reactions/read receipts/attachments/audio/video/AI.

## Проверки

Assigned/unassigned/revoked, workout/exercise comment, multiple comments, notification/deep-link, retry, XSS, long text, mobile/back navigation.

## Done when

Trainer даёт feedback в правильном workout/exercise context; client получает его там же; generic messaging product отсутствует.

## Рекомендуемый commit

`feat(ui): add contextual trainer feedback experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
