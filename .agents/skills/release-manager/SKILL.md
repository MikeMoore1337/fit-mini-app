---
name: release-manager
description: Release preparation, migrations, rollout, smoke checks, rollback and post-deploy verification.
---

# release-manager

Перед релизом собери release checklist, соответствующий типу продукта.

Проверь:

- build artifact воспроизводим;
- нужные tests/checks green;
- migrations проверены;
- configuration/secrets готовы;
- backward compatibility;
- external dependencies;
- feature flags, если есть;
- rollback/forward-fix path;
- backup, если изменение может повредить данные;
- smoke tests;
- monitoring/alerts готовы наблюдать изменение.

После deployment:

- health/readiness;
- error rate;
- latency;
- critical user flow;
- background jobs/queues;
- migration completion;
- новые логи/метрики.

Release notes должны говорить о пользовательски/операционно значимых изменениях, а не переписывать Git diff.
## Адаптация к проекту

Собирай порядок релиза из фактических компонентов проекта: services/apps, migrations, generated
contracts, background jobs, feature flags и external dependencies. Не предполагай конкретную
схему deployment. Сам production deployment требует явного запроса; подготовка и локальная
проверка могут выполняться без него, если repository-wide правила не говорят иначе.
