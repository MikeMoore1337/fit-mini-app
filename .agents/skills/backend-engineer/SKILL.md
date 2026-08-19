---
name: backend-engineer
description: >
  Design or change backend services, APIs, business logic, transactions and external integrations
  with production reliability. Use when server-side behavior or API contracts change. Do not use
  as the primary skill for persistence-only schema work or pure infrastructure changes.
---

# backend-engineer

Строй backend вокруг ясных бизнес-границ.

## API

- явные request/response schemas;
- валидация на границе;
- стабильные error contracts;
- корректные status codes/protocol semantics;
- pagination/filter/sort contracts;
- versioning только при необходимости;
- backward compatibility.

## Бизнес-логика

- не прячь бизнес-правила в controllers/routers;
- транзакционные границы должны быть явными;
- side effects должны происходить в предсказуемом порядке;
- повторяемые операции делай идемпотентными, если запрос может повториться.

## Интеграции

Для внешних сервисов учитывай:

- timeout;
- retry с backoff только когда безопасно;
- rate limits;
- partial failure;
- malformed response;
- observability;
- sandbox/test doubles.

## Ошибки

Не возвращай stack traces наружу.
Логируй достаточно для расследования, но не секреты и чувствительные данные.

## Безопасность

- server-side authorization;
- least privilege;
- validation;
- safe serialization;
- secure secret handling;
- защита от injection/SSRF/path traversal и других релевантных классов.

## Privacy и data exposure

Для API, работающего с пользовательскими/чувствительными данными:

- возвращай только необходимые поля;
- не доверяй client-side фильтрации скрытых данных;
- учитывай export/delete lifecycle;
- не логируй payload целиком по умолчанию;
- минимизируй данные, уходящие во внешние интеграции;
- проверяй authorization на объект, а не только факт аутентификации.

При изменении lifecycle данных используй `$privacy-engineer`.

## Тесты

Покрой:

- happy path;
- validation;
- auth/authz;
- transaction rollback;
- duplicate/retry scenarios;
- external integration failures;
- critical business invariants.
## Адаптация к проекту

Сначала определи используемый backend framework, структуру модулей, contract-generation workflow,
auth model и проектные команды. Если API contract генерирует клиентские типы/SDK, используй
существующий generator workflow и не редактируй generated output вручную.
