# Billing and entitlement checklist

Использовать с `$billing-engineer`.

- [ ] Владелец утвердил плательщика, plans, limits и downgrade policy.
- [ ] Payment state отделён от entitlement и quota.
- [ ] Internal plan IDs не зависят от provider price IDs.
- [ ] Checkout подтверждается server-side событием.
- [ ] Webhook signature и timestamp проверяются.
- [ ] Provider event ID обрабатывается идемпотентно.
- [ ] Учтены duplicate, delayed и out-of-order events.
- [ ] Есть reconciliation и review/dead-letter path.
- [ ] Entitlement проверяется на backend.
- [ ] Downgrade не удаляет данные.
- [ ] Export/delete доступны независимо от тарифа.
- [ ] Sandbox и production полностью разделены.
- [ ] Секреты и платёжные данные не попадают в клиент/логи.
- [ ] Cancel, failed payment, grace, refund и dispute имеют UX и тесты.
- [ ] Admin grants и ручные исправления аудируются.
