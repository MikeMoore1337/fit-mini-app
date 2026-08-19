# TASK 70A. Рассмотрение заявок тренеров и атомарная выдача Trainer capability

- Фаза: **Admin backend / Trainer activation**
- Приоритет: **70A/93 - выполнить сразу после task 70**
- Зависит от: `69A`, `70`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$solution-architect`, `$backend-engineer`, `$security-engineer`, `$privacy-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Добавить безопасный moderation backend для заявок тренеров и гарантировать, что одобрение одной транзакцией выдаёт Trainer capability, фиксирует решение и создаёт audit/notification events.

Перед началом прочитать `TRAINER_APPLICATION_INTEGRATION_NOTES.md` и использовать application model task `69A`, capability model task `69` и admin/audit foundation task `70`.

## Permission model

Централизовать или переиспользовать permissions эквивалентного смысла:

- `trainer_applications.read`;
- `trainer_applications.manage`.

Целевая политика:

- Root и `super_admin` - read + manage;
- `support_admin` - read-only, без approve/reject;
- internal reviewer note доступен только `manage`; backend обязан использовать отдельную безопасную read projection для support_admin;
- ordinary account и Trainer without Admin не получают admin application endpoints;
- inactive delegated admin denied;
- frontend visibility не является security boundary;
- reviewer не может принять решение по собственной заявке;
- Root при необходимости получает Trainer capability отдельным root-only capability assignment действием, а не через фиктивное одобрение собственной заявки.

Не расширять Root authority и не менять `ADMIN_TELEGRAM_USER_IDS`.

## Admin read API

Добавить bounded, paginated и permission-gated операции:

- list applications;
- фильтр по status;
- pending-first/default ordering;
- поиск заявителя через существующий safe user search contract;
- application detail;
- applicant capability/account status summary;
- previous application decisions;
- current verified contact identities в объёме, необходимом для рассмотрения;
- reviewer metadata без secrets.

Не возвращать passwords, tokens, Telegram init data, provider credentials, private fitness/nutrition data или произвольные user records.

## Approve

Approve должен выполняться как единая согласованная операция:

1. Проверить `trainer_applications.manage` и запрет self-review.
2. Заблокировать или optimistic-compare application в статусе `pending`.
3. Повторно проверить applicant account eligibility и фактический Trainer capability state.
4. Создать или активировать Trainer capability через canonical service task `69`.
5. Создать минимальный Trainer profile только если он требуется архитектурой, не заполняя выдуманные данные.
6. Перевести application в `approved`.
7. Зафиксировать reviewer и timestamp.
8. Добавить append-oriented audit event с safe metadata.
9. Создать notification/outbox event.
10. Commit только при успешности всех обязательных шагов.

Нельзя получить состояние `approved application`, если Trainer capability не выдана, и нельзя выдать capability без зафиксированного решения в рамках этой операции.

Повтор идентичного approve после подтверждённого успеха должен вернуть безопасный idempotent result. Конкурирующий второй reviewer не должен повторно назначить capability или перезаписать первого reviewer.

Если Trainer capability уже активна из legacy/manual flow, не создавать дубликат и не угадывать историю. Вернуть явный conflict/reconciliation state и показать его будущему Admin UI.

## Reject

Reject разрешён только для `pending` application и требует:

- обязательную понятную user-visible reason;
- optional internal note;
- reviewer/timestamp;
- audit event;
- notification/outbox event.

Reason должна иметь разумный лимит, не содержать внутренних security details и возвращаться заявителю. Internal note не возвращается applicant API и не попадает в обычные логи/аналитику.

Решение не редактируется задним числом. После `rejected` пользователь может создать новую заявку через task `69A`.

## Capability lifecycle boundary

- Approval активирует Trainer capability.
- Suspension/revocation Trainer capability является отдельной admin operation и не меняет historical application status.
- Rejected application не изменяет Personal/Admin capabilities.
- Approval не создаёт trainer-client relationship, invitation или доступ к клиентским данным.
- Trainer capability не выдаёт Admin.
- Admin capability не выдаёт Trainer без approve или отдельного разрешённого capability assignment flow.
- Suspended/revoked Trainer не восстанавливается автоматически новой отправкой без current owner policy; не ослаблять существующий revoke boundary.

## Audit и события

Audit минимум:

- actor/effective admin permission;
- action `trainer_application.approve` или `trainer_application.reject`;
- application ID и applicant account ID;
- old/new status;
- capability result;
- timestamp/result/reason code;
- без полного текста анкеты и без user-visible/internal reason body в обычном audit metadata, если для этого нет защищённого поля и retention policy.

Notification/outbox events минимум:

- `trainer_application.approved`;
- `trainer_application.rejected`.

Payload минимальный, без полной анкеты и internal note.

## Security и concurrency checks

Проверить минимум:

- ordinary user denied;
- Trainer without Admin denied;
- support_admin read-only;
- Root/super_admin approve/reject allowed;
- inactive admin denied;
- self-review denied;
- applicant cannot choose capability/status/reviewer;
- two reviewers approve concurrently - ровно одно решение и одна capability assignment;
- approve vs withdraw race имеет один детерминированный terminal result;
- repeated request idempotent;
- reject requires public reason;
- internal note hidden from applicant/support read-only where applicable;
- audit created on allowed decisions and denied escalation attempts where current audit policy requires;
- no cross-user private fitness data leakage;
- no Root/admin/trainer capability coupling regression.

## Out of scope

- Profile application form;
- Admin Workspace queue/detail UI;
- Telegram Mini App adaptation;
- document verification;
- verified trainer badge;
- marketplace/rating;
- support messenger;
- AI qualification scoring;
- automatic approval.

## Done when

Admin backend безопасно показывает и рассматривает заявки, approve атомарно активирует Trainer capability, reject требует понятную причину, self-review/escalation/concurrency защищены, а audit и notification events не раскрывают лишние данные.

## Рекомендуемый commit

`feat(admin): add trainer application review and capability grant`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать и не переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений запустить только профильные permission/API/transaction/concurrency/audit tests, generated contract checks при изменении API, typecheck/lint согласно `AGENTS.md`, проверить `git diff` и создать один логический commit.

В финальном отчёте: permissions, endpoints, transaction boundary, audit/events, migration changes, реально запущенные проверки, ограничения/follow-ups и commit hash.
