# TASK 69A. Заявка на доступ к кабинету тренера - доменная модель и пользовательский API

- Фаза: **Trainer activation foundation**
- Приоритет: **69A/93 - выполнить сразу после task 69**
- Зависит от: `47`, `59`, `69`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$solution-architect`, `$backend-engineer`, `$security-engineer`, `$privacy-engineer`, `$qa-engineer`

## Цель

Создать каноническую доменную модель заявки на доступ к Coach workspace и безопасный API для самого заявителя.

Заявка является запросом на включение Trainer capability. Она не является проверкой диплома, сертификацией или подтверждением квалификации.

Перед началом прочитать `TRAINER_APPLICATION_INTEGRATION_NOTES.md`.

## Обязательный current-code audit

Сначала точечно исследовать:

- как сейчас хранится trainer status/capability;
- есть ли существующая role application, форма, endpoint, таблица или временный флаг;
- как устроены account ownership, migrations, API errors и idempotency;
- как task `59` оформил transactional notification events/outbox;
- какие profile fields и verified identities уже доступны;
- какие ограничения действуют для blocked, deleting и Demo accounts.

Не создавать параллельную модель, если подходящая сущность уже существует. Сохранить совместимые данные и привести реализацию к контракту этой задачи.

## Owner-approved contract

- Application history и Trainer capability хранятся отдельно.
- Одобрение будет выполняться вручную в task `70A`.
- В первом релизе не загружаются дипломы, сертификаты, паспортные данные и другие документы.
- Не создавать и не возвращать пользователю статус `verified trainer`.
- Personal functionality остаётся доступной независимо от результата заявки.
- AI Coach не участвует в принятии решения.

## Доменная модель

Адаптировать названия к conventions проекта, но обеспечить эквивалентный контракт `TrainerApplication`:

- stable application ID;
- applicant account ID;
- status: `pending`, `approved`, `rejected`, `withdrawn`;
- experience range;
- bounded list of specialties/directions;
- intended use text;
- optional expected client count;
- optional short about text, только если оно не дублирует intended use;
- terms/version acceptance, если проект хранит такие версии;
- submitted/created/updated timestamps;
- withdrawn timestamp;
- reviewed timestamp и reviewer ID - nullable до решения;
- user-visible rejection reason - nullable;
- internal reviewer note - nullable и никогда не возвращается applicant API;
- audit-friendly immutable history без переписывания старых решений.

Не копировать email, Telegram ID или другие verified identities в заявку без доказанной необходимости. Администратор должен получать актуальные account identities через permission-gated admin read model.

## State machine

Разрешённые переходы:

```text
new -> pending
pending -> approved
pending -> rejected
pending -> withdrawn
rejected -> new pending record
withdrawn -> new pending record
```

Требования:

- одновременно существует не более одной `pending` заявки на account;
- constraint обеспечивается сервером и, где уместно, БД;
- terminal decision нельзя редактировать или переоткрывать обычным endpoint;
- повторная подача создаёт новую application record;
- approved applicant с активной Trainer capability не может подать новую заявку;
- blocked/deleting account и Demo Mode не могут подать заявку;
- Admin capability сама по себе не запрещает подачу, потому что Admin и Trainer независимы;
- hard experience threshold не вводится.

## Пользовательский API

Следовать текущему API style и generated contract проекта. Поддержать эквивалентные операции:

1. Получить текущий application state и ограниченную историю собственных заявок.
2. Подать заявку.
3. Отозвать только собственную `pending` заявку.
4. Повторно подать новую заявку после `rejected` или `withdrawn`.

Ответ пользователю не содержит:

- internal note;
- reviewer secrets/permissions;
- лишние идентификаторы администратора;
- данные других заявителей;
- утверждение о профессиональной верификации.

## Validation и abuse protection

- bounded enum/list values;
- разумные лимиты текста и количества specialties;
- trim/normalization без уничтожения осмысленного текста;
- понятные field errors;
- duplicate specialties не сохраняются;
- один pending record блокирует повторную отправку;
- повтор запроса после timeout/retry не создаёт дубликат;
- использовать существующий idempotency/request-dedup contract или минимальную безопасную альтернативу;
- применить существующий account/API rate limiting без произвольного многодневного cooldown после отказа;
- не логировать текст анкеты в обычные operational logs и product analytics.

## События

Создать или переиспользовать safe domain/outbox events минимум для:

- `trainer_application.submitted`;
- `trainer_application.withdrawn`.

События не должны содержать полный текст анкеты. Фактические каналы и UX уведомлений реализуются в task `71A`.

## Миграции и совместимость

- использовать текущий migration mechanism;
- не удалять существующий trainer status;
- не придумывать backfill заявок для уже существующих Trainer accounts;
- legacy Trainer может оставаться Trainer без synthetic approved application;
- индексировать только реальные query patterns: applicant/current pending/admin status+date;
- migration должна иметь понятный rollback/compatibility path в рамках conventions проекта.

## Проверки

Минимум:

- submit by eligible ordinary account;
- Admin without Trainer также может подать собственную заявку;
- duplicate/double submit создаёт одну pending application;
- applicant видит только свои данные;
- unrelated account получает отказ;
- pending withdraw;
- rejected/withdrawn resubmission создаёт новую запись и сохраняет историю;
- active Trainer submit denied;
- blocked/deleting/Demo submit denied;
- internal note не попадает в applicant response/log/analytics;
- concurrent submit не нарушает unique pending invariant;
- migration и API contract tests.

## Out of scope

- approve/reject API;
- назначение или отзыв Trainer capability;
- Admin Workspace UI;
- Profile form UI;
- professional document verification;
- verified badge;
- marketplace/rating;
- AI decision making;
- generic support chat.

## Done when

Есть единый application domain contract, безопасная state machine, пользовательский API и тесты. Заявка не смешана с capability, не создаёт дубликаты и не обещает профессиональную верификацию.

## Рекомендуемый commit

`feat(trainer): add application domain and applicant api`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений запустить только профильные migration/domain/API/security tests, generated contract checks при изменении API, typecheck/lint согласно `AGENTS.md`, проверить `git diff` и создать один логический commit.

В финальном отчёте: reused/changed, модель и state transitions, API, миграции/индексы, реально запущенные проверки, ограничения/follow-ups и commit hash.
