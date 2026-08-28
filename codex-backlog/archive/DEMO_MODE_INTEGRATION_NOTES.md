# Demo Mode integration - simplified release contract

Demo is tasks `68-69`, not a second full product.

## Three curated scenarios

1. Для себя: Today -> несколько подходов -> итог тренировки -> Progress.
2. Питание: добавить продукт/quick add -> дневной итог -> nutrition report.
3. Для тренера: открыть подготовленного клиента -> посмотреть факты -> временный contextual comment.

## Boundaries

- demo writes are ephemeral and resettable;
- no production notifications, support relay, trainer invitation, account export, deletion or external provider side effects;
- no migration of demo state into a real account;
- no arbitrary user data;
- a single Design V2 implementation with explicit demo capability boundary;
- conversion CTA appears after meaningful action, not on every screen.
