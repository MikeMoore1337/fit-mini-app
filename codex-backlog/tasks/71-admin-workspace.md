# TASK 71. Web Admin Workspace

- Фаза: **Admin UX**
- Приоритет: **71/93**
- Зависит от: `70`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Создать permission-aware Web Admin Workspace. Он должен быть отдельным operational context, пригодным сейчас для владельца и позже для нескольких delegated admins.

## In scope

### Web-only

Admin Workspace делать в Web-приложении. Не добавлять полноценную админку в Telegram Mini App.

### Context separation

Для account с несколькими capabilities явно разделять:

```text
Personal
Coach       # only Trainer
Admin       # only Admin/Root
```

Admin не должен "притворяться trainer".

### Overview

Показывать только реальные operational metrics, например users/trainers/relationships/pending invites/delegated admins/AI status/recent audit activity.

### Users

Search, filters, pagination, detail, capability summary, account status, relationships, безопасные actions согласно permissions.

### Trainers

List/search, client count/summary, detail, relationships, invitations, capability state.

Это operational admin view, не Coach workspace.

### Relationships / invitations

Диагностический interface по trainer/client/status/invitation state/timestamps.

### Administrators

Только для `admins.manage`/Root:

- delegated admins list;
- role/status;
- created by;
- assign/change role;
- activate/deactivate.

Показать, что Root управляется server config. Не показывать значение `ADMIN_TELEGRAM_USER_IDS`.

### AI operations

AI enabled/status/providers/cooldown/error/failover aggregates без keys и без paid controls.

### Audit log

Read-only list actor/action/target/result/time/safe metadata.

### Permission-aware navigation

Показывать sections/actions по effective permissions, но backend остаётся security boundary.

### States

Loading/empty/error/retry/permission denied/partial/pagination/long IDs.

Desktop-first, но graceful Web layout на 768/390/360.

## Design V2 contract

Admin Workspace является operational context внутри Approved Design V2, а не отдельным generic admin-template/SaaS UI. Перед UI-работой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`; переиспользовать shared shell, navigation, tables/lists, forms, buttons, status/permission states, semantic colors, typography и geometry. Desktop может быть плотнее product surfaces, но mobile/desktop и light/dark остаются одной системой; существенные visual changes проверить в реальном браузере и не менять канонический дизайн без owner checkpoint.

## Out of scope

Не добавлять Telegram admin panel, impersonation, automatic Admin=>Trainer, arbitrary DB editor, terminal/SQL console, secrets, billing UI или Trainer Copilot. Queue/detail/actions для trainer applications реализуются отдельно в task `71A` поверх готового Admin Workspace.

## Проверки

Ordinary user no admin entry; trainer no admin entry; delegated admin sees permitted sections; Root sees root sections; trainer+admin sees Coach/Admin separately.

Core flow: Overview -> Users -> User detail -> Trainers -> Trainer detail -> Relationships -> AI -> Audit.

Root flow: Administrators -> assign/change/deactivate -> audit entry.

Direct routes/actions denied без backend permission. No env/root IDs/secrets in client.

1440/1280/768/390/360, keyboard/focus, typecheck/lint/tests/build/targeted Playwright.

## Done when

Admin Workspace - отдельный operational context.

Root управляет delegated admins, но остаётся env-controlled.

Delegated admin видит только разрешённое.

Admin не получает Trainer автоматически.

Multi-capability account безопасно переключается между Personal, Coach и Admin.

## Рекомендуемый commit

`feat(admin): add permission-aware web admin workspace`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений запустить только профильные проверки согласно `AGENTS.md`, проверить `git diff` и создать один логический commit при tracked changes.

В финальном отчёте: изменения, ключевые файлы, миграции, реально запущенные проверки, результаты, ограничения/follow-ups, commit hash.
