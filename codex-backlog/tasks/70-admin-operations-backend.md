# TASK 70. Admin operations API, audit log и безопасные support-инструменты

- Фаза: **Admin backend**
- Приоритет: **70/93**
- Зависит от: `69`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$security-engineer`, `$qa-engineer`

## Цель

Создать безопасный operational backend для будущей Web Admin Workspace поверх capability model task `69`.

## In scope

### Operational reads

Переиспользовать existing services/repositories и предоставить permission-gated views:

- users;
- trainers;
- trainer-client relationships;
- invitations;
- account/capability status;
- delegated admin assignments;
- AI operational status/telemetry из tasks `33-48`;
- audit log.

### Users / trainers

Поддержать search, pagination, filters и detail без выдачи secrets.

Для trainer list/detail показывать только полезный operational summary без N+1.

Не смешивать trainer status и admin status.

### Relationships / invitations

Дать возможность диагностировать trainer-client relationship и invitation state.

Не превращать API в arbitrary row editor.

### Delegated admin management

Root/authorized permission может:

- list delegated admins;
- назначить supported admin role существующему account;
- изменить role;
- activate/deactivate.

Нельзя:

- создать Root;
- редактировать `ADMIN_TELEGRAM_USER_IDS`;
- повысить delegated admin до Root;
- обойти permission policy.

### Audit log

Sensitive admin actions пишутся в append-oriented audit trail:

- actor;
- effective admin role/capability;
- action;
- target type/id;
- safe metadata;
- result;
- timestamp.

Не логировать passwords, tokens, cookies, Telegram init data, provider keys, DB credentials.

### AI operations

Безопасный read model может показывать:

- AI enabled/disabled;
- provider order/status/cooldown/misconfigured без secrets;
- request/failover/error aggregates;
- model/provider metadata, если уже собирается.

Не показывать keys.

Не позволять обходить `AI_FREE_ONLY`.

Не выполнять inference healthchecks ради dashboard.

### Security/performance

Каждый endpoint/action имеет explicit backend permission.

Trainer без Admin не получает admin API.

Support/read-only admin не получает writes автоматически.

Lists paginated/bounded, no obvious N+1, safe errors без raw SQL/stack/secrets.

## Out of scope

Не делать UI, impersonation, SQL console, shell, DB browser, secret viewer, paid AI controls, billing admin или Root management через UI/API. Trainer application moderation API и атомарная выдача capability реализуются отдельно в task `70A` поверх этой foundation.

## Проверки

Ordinary user denied; trainer without Admin denied; delegated admin limited; inactive admin denied; Root allowed.

Admin assignment/change/deactivate audited.

No delegated->Root escalation.

No secrets.

AI status без keys/paid bypass/inference side effect.

Pagination/index/query behavior проверены.

## Done when

Admin backend даёт безопасные operational views/actions, sensitive actions permission-gated и audited, Root/delegated boundaries соблюдены, trainer сам по себе не имеет admin API.

## Рекомендуемый commit

`feat(admin): add secure operations api and audit log`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений запустить только профильные проверки согласно `AGENTS.md`, проверить `git diff` и создать один логический commit при tracked changes.

В финальном отчёте: изменения, ключевые файлы, миграции, реально запущенные проверки, результаты, ограничения/follow-ups, commit hash.
