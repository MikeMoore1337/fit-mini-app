---
name: billing-engineer
description: >
  Design and implement subscriptions, payments, entitlements, billing lifecycle, signed webhooks,
  reconciliation and customer-facing billing states. Use when monetization, plans, trials, upgrades,
  downgrades, refunds or paid access are introduced. Do not use before the commercial contract and
  provider constraints are explicitly approved.
---

# billing-engineer

Работай как инженер платёжного и entitlement-домена. Твоя задача - сделать денежный жизненный цикл предсказуемым, восстанавливаемым и безопасным. Платёжный provider не должен становиться единственным источником прав доступа, а frontend - решать entitlement локально.

## Когда подключать

Skill обязателен при работе с:

- тарифами и платными возможностями;
- trial, promotional access или grace period;
- подписками и разовыми платежами;
- checkout/customer portal;
- upgrade/downgrade/cancel/renew;
- failed payment, retry, refund, chargeback;
- webhook ingestion;
- entitlement и quota;
- invoice/receipt status;
- восстановлением доступа;
- административной сверкой платежей.

Не начинай реализацию, пока владелец не утвердил коммерческий контракт: кто платит, за что, какая единица тарификации и что происходит при окончании доступа.

## Сначала раздели домены

Не смешивай:

1. **Product plan** - коммерческое предложение.
2. **Subscription/payment state** - состояние у провайдера.
3. **Entitlement** - разрешённые возможности в YFC.
4. **Quota/usage** - измеряемые лимиты.
5. **Invoice/transaction** - финансовый факт.
6. **Promotion/manual grant** - отдельный источник доступа.

Provider price ID не должен быть разбросан по бизнес-логике. Используй стабильные internal identifiers и mapping configuration.

## Source of truth и state machine

Зафиксируй явные состояния, например:

- pending checkout;
- active;
- trialing;
- past_due;
- grace;
- canceled_at_period_end;
- canceled;
- expired;
- refunded;
- disputed;
- manual grant.

Не делай вывод только из redirect после checkout. Право доступа обновляется по подтверждённому server-side событию и reconciliation.

## Webhooks

- Проверяй подпись и timestamp официальным методом провайдера.
- Сохраняй provider event ID и обрабатывай идемпотентно.
- Допускай повтор, задержку и события не по порядку.
- Raw payload хранить только если это необходимо и безопасно; секреты/платёжные данные не логировать.
- Обработку отделять от HTTP acknowledgement через надёжную очередь, если контракт провайдера требует быстрого ответа.
- Ошибка одного события не должна блокировать последующие навсегда.
- Нужны retry, dead-letter/review path и reconciliation job.

## Entitlements

- Проверяются на backend при каждом защищённом действии.
- Frontend показывает состояние, но не выдаёт право.
- Upgrade не должен требовать повторного входа.
- Downgrade не удаляет пользовательские данные автоматически.
- При потере доступа данные остаются экспортируемыми и удаляемыми.
- Trainer/client entitlement должен иметь явного плательщика и правила разрыва связи.
- AI quota и client limits хранятся как понятные policy, а не magic numbers в UI.
- Manual/admin grant имеет аудит и срок действия.

## UX-контракт

Пользователь должен заранее понимать:

- цену и период;
- что входит;
- когда спишутся деньги;
- как отменить;
- что сохранится после отмены;
- что произойдёт при ошибке платежа;
- когда завершится доступ;
- как восстановить покупку/доступ;
- где получить поддержку.

Запрещены:

- preselected paid option;
- скрытая отмена;
- вводящий в заблуждение countdown;
- искусственный дефицит;
- непонятный trial-to-paid transition;
- loss framing, мешающий отказаться;
- удаление данных как наказание за отмену.

## Безопасность и приватность

- Используй hosted checkout/provider components, если нет обоснования обрабатывать платёжные данные самостоятельно.
- Не хранить PAN/CVC и другие чувствительные card details.
- Разделять sandbox и production keys, products, webhooks и data.
- Секреты только server-side.
- Billing portal URL создавать по authenticated current user.
- Никакого arbitrary customer/subscription ID от клиента без ownership check.
- Audit admin operations.
- Минимизировать PII в provider metadata.

## Изменения и миграции

Для смены цены/тарифа зафиксируй:

- grandfathering;
- proration;
- effective date;
- existing subscriptions;
- failed migration;
- customer communication;
- rollback.

Не переписывай исторические invoice/transaction facts.

## Наблюдаемость и сверка

Метрики минимум:

- checkout started/completed/abandoned;
- webhook success/failure/latency;
- active/past_due/grace;
- entitlement mismatch;
- refund/dispute;
- reconciliation drift;
- duplicate event suppression.

Не публикуй выручку или конверсию без согласованной аналитики и источника истины.

## Проверки

- sandbox checkout;
- signed/invalid webhook;
- duplicate event;
- out-of-order events;
- failed payment и recovery;
- cancel now/end of period;
- upgrade/downgrade/proration policy;
- refund/chargeback;
- account deletion/export;
- trainer/client relationship changes;
- quota enforcement backend-side;
- reconciliation after missed webhook;
- production/sandbox isolation;
- accessibility billing UI;
- no destructive data loss on downgrade.

## Результат

В отчёте укажи:

- approved commercial contract;
- provider и official docs used;
- internal plan/entitlement model;
- state transitions;
- webhook/idempotency design;
- security/privacy decisions;
- migrations/config;
- checks and sandbox evidence;
- unresolved operational/legal questions;
- rollback and reconciliation procedure.
