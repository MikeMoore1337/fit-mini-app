# TASK 69. Root Admin, delegated admins и независимые account capabilities

- Фаза: **Admin foundation**
- Приоритет: **69/93**
- Зависит от: `11`, `12`, `47`, `48`, `68`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$security-engineer`, `$backend-engineer`, `$qa-engineer`

## Цель

Перейти от текущей convenience-модели, где admin автоматически получает client/trainer functionality, к композиционной модели capabilities.

Целевая модель:

```text
Authenticated Account
├── Personal capabilities   # baseline
├── Trainer capability      # optional additive
├── Admin capability        # optional additive
└── Root Admin              # server-configured owner/break-glass
```

`ADMIN_TELEGRAM_USER_IDS` остаётся source of truth для Root Admin.

## In scope

### Текущая модель

Сначала изучить фактическую реализацию:

- парсинг `ADMIN_TELEGRAM_USER_IDS`;
- поддержка нескольких IDs;
- backend admin/trainer guards;
- frontend navigation/guards;
- хранение trainer status;
- Web/Telegram auth identity;
- почему admin сейчас получает trainer/client возможности;
- migrations/tests.

Не менять модель по предположениям.

### Personal - baseline

Личный fitness-функционал доступен authenticated account независимо от дополнительных capabilities:

- свои тренировки;
- свои программы;
- своё питание;
- КБЖУ/targets;
- progress;
- measurements;
- AI Coach в собственном разрешённом context.

Trainer и Admin не должны отключать Personal.

### Trainer - additive

Trainer = Personal + Trainer.

Trainer-specific возможности:

- Coach workspace;
- clients;
- invitations;
- client program workflows;
- разрешённые client progress/nutrition summaries.

Trainer не получает Admin автоматически.

Не создавать self trainer-client relationship ради личных данных trainer.

### Admin - additive и независим от Trainer

Delegated admin = Personal + Admin.

Admin не становится trainer автоматически.

Если один account должен быть trainer + admin, оба capabilities назначаются независимо.

### Root через env

Сохранить:

```env
ADMIN_TELEGRAM_USER_IDS=<telegram_user_id>[,...]
```

как server-side Root Admin / owner / break-glass mechanism.

Root:

- определяется trusted backend identity;
- не создаётся и не удаляется через UI/API;
- не зависит от delegated-admin records;
- не раскрывает root ID list в frontend/API/logs;
- не получает Trainer автоматически.

Если несколько IDs уже поддерживаются - сохранить. Если нет - безопасно поддержать список без изменения смысла env.

### Delegated admins

Добавить минимальную DB-модель delegated admin assignments/roles, адаптированную к conventions проекта.

Минимально поддержать понятие:

- `super_admin`;
- `support_admin`;

с возможностью позже добавить `content_admin`/`operations_admin`.

Не строить enterprise policy engine.

Permissions централизовать по смыслу: users read/manage-limited, trainers read, relationships read, invitations read, AI operations read, audit read, admins manage, system manage.

Критичные admin-management/system permissions должны быть root-only или явно ограничены.

### Убрать implicit admin => trainer

Найти и удалить только автоматическую связь административного доступа с trainer capability.

Не отнимать trainer status у аккаунта, который действительно является trainer.

Если исторически невозможно отличить настоящий trainer status от convenience admin=>trainer, не угадывать и не разрушать данные молча: зафиксировать migration/follow-up.

### Backend enforcement

Централизовать reusable checks для:

- root;
- delegated admin permission;
- trainer capability;
- personal ownership.

Frontend visibility не является security boundary.


## Auth identity integration

Использовать hardened auth foundation tasks `09-11`.

`ADMIN_TELEGRAM_USER_IDS` сопоставляется только с trusted verified Telegram identity.

Multi-provider login/linking не должен позволять:

- перенести Root authority другому internal account;
- получить Root по совпавшему email;
- получить Root по произвольному frontend `telegram_user_id`.

Если root входит через linked non-Telegram provider, соблюдать security decision task `09-10`; не расширять Root trust молча.

## Out of scope

Не делать Admin Workspace UI/API operations из tasks `65-66`.

Не добавлять impersonation, Trainer Copilot, enterprise IAM, десятки admin roles, root management через БД/UI или self trainer-client relation.

## Проверки

Проверить capability matrix:

```text
ordinary user: Personal yes / Trainer no / Admin no
trainer: Personal yes / Trainer yes / Admin no
delegated admin: Personal yes / Trainer no / Admin yes
trainer+admin: Personal yes / Trainer yes / Admin yes
root: Personal yes / Root yes / Trainer only if separately assigned
```

Проверить root from env, unknown ID denial, no env leakage, delegated-admin create/revoke/escalation protection, inactive admin denial, admin-without-trainer denial на Coach endpoints, trainer personal regression, Web/Telegram auth regression.

## Done when

Root остаётся server-configured через `ADMIN_TELEGRAM_USER_IDS`.

Delegated admins управляются отдельно.

Admin больше не подразумевает Trainer.

Trainer сохраняет весь Personal functionality.

Account может безопасно иметь Trainer + Admin одновременно при независимом назначении.

Backend authorization централизован и протестирован.

## Рекомендуемый commit

`feat(auth): separate personal trainer admin and root capabilities`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений запустить только профильные проверки согласно `AGENTS.md`, проверить `git diff` и создать один логический commit при tracked changes.

В финальном отчёте: изменения, ключевые файлы, миграции, реально запущенные проверки, результаты, ограничения/follow-ups, commit hash.
