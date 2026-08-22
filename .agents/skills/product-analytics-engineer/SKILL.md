---
name: product-analytics-engineer
description: >
  Design, implement or review privacy-safe product event taxonomy, funnel instrumentation,
  activation, retention, identity transitions, event schemas and data-quality checks. Use when
  product behavior must be measured. Do not use for operational logs/metrics or indiscriminate
  every-click tracking.
---

# product-analytics-engineer

Начинай не с события, а с продуктового вопроса. Каждое событие должно помогать принять решение.

## Граница с observability

Product analytics отвечает:

- где пользователь начинает и завершает ключевой сценарий;
- где теряется;
- получает ли первую ценность;
- возвращается ли;
- какие product variants работают лучше.

Observability отвечает:

- работает ли сервис;
- почему произошла ошибка;
- какова latency/throughput/resource health.

Не копируй operational logs в product analytics и не передавай raw product content в metrics.
Используй `$observability-engineer` для runtime signals.

## Сначала

Для каждой feature сформулируй:

1. Product question.
2. Decision, которую изменит ответ.
3. User journey и expected states.
4. Success/failure/abandonment definitions.
5. Event owner: client или server.
6. Минимальные свойства.
7. Privacy/consent ограничения.
8. Validation/dashboard plan.

Проверь current analytics/SEO measurement stack, consent/legal path, environments, account model,
Demo, Web/TMA и existing events. Не создавай второй event pipeline без причины.

Актуальные юридические требования и consent policy проверяй по официальным источникам и фактической
юрисдикции. Не делай legal guess в skill или коде.

## Event taxonomy

Event name описывает устойчивое business occurrence, а не случайный DOM action.

Предпочитай события уровня:

- landing/demo/login/onboarding;
- program/workout;
- nutrition log;
- measurement/check-in;
- coach/admin workflow;
- suggestion shown/accepted/dismissed;
- export/delete lifecycle;
- AI high-level request/result state без текста.

Не отправляй every click, hover, scroll или component implementation detail без конкретного вопроса.

Для каждого event зафиксируй:

- canonical name;
- schema version;
- definition и trigger boundary;
- producer/owner;
- required/optional properties;
- dedupe/idempotency key;
- subject identity class;
- environment/surface;
- retention/consent classification;
- examples и prohibited payload;
- downstream metric/funnel.

## Event envelope

Используй provider-neutral internal contract. Поля выбирай по проекту, но обычно нужны:

- event id;
- event name/version;
- occurred_at и received_at;
- environment;
- surface/client type;
- anonymous/authenticated scoped subject id;
- session/journey/correlation id, если нужен;
- source/producer;
- allowlisted properties.

Не делай vendor payload единственным source of truth. Provider adapter преобразует internal event.

## Client vs server ownership

Client подходит для:

- page/screen impression;
- visible prompt/banner;
- button intent;
- validation/UI abandonment signal, если он действительно нужен.

Server подходит для:

- auth завершён;
- program/workout создан/завершён;
- food/measurement/check-in реально сохранены;
- permission/admin action выполнены;
- export/delete job принят/завершён;
- AI request принят/завершён на high level.

Не считай client click успешным business outcome. Не дублируй одно завершение client и server events
без dedupe и чёткой причины.

## Identity lifecycle

Разделяй:

- anonymous visitor;
- pre-auth/demo session;
- authenticated account;
- device/session;
- trainer/admin capabilities;
- Web и Telegram Mini App surfaces.

При anonymous -> authenticated transition:

- не сливай пользователей по email/Telegram id на клиенте;
- используй canonical account mapping на доверенной стороне;
- не создавай duplicate conversion;
- не переносись через logout к следующему пользователю на shared device;
- Demo fixture interactions не становятся реальными user actions;
- role/capability не заменяют account identity.

Raw database/user/Telegram ids не отправляй во внешний analytics provider без необходимости. Используй
scoped/pseudonymous identifiers по privacy policy.

## Privacy-safe properties

По умолчанию запрещены:

- содержимое food diary/recipe;
- exact calories/macros, weight, measurements, HR, distance;
- trainer comments и notes;
- support messages;
- AI conversation/prompt/answer/tool payload;
- exercise free text/custom names, если они могут быть private;
- auth tokens, initData, emails, phones;
- secrets/internal stack traces;
- uploaded file content;
- arbitrary URL/query params с PII.

Событие `measurement_logged` обычно не требует самого значения. `cardio_logged` не требует distance/HR.
`notification_preferences_changed` не требует exact quiet hours, если вопрос лишь о факте изменения.

Используй allowlist properties и automated sensitive-payload regression tests.

Для privacy review используй `$privacy-engineer`.

## Consent и failure behavior

- Не включай hidden tracking как побочный эффект SEO/UI task.
- Consent/opt-out state применяется до external delivery по project policy.
- Product-critical action не должен падать из-за analytics provider.
- Queue/retry bounded; duplicate delivery безопасна.
- Offline buffering, если нужен, имеет size/age limits и не хранит sensitive content.
- Provider unavailable наблюдаем, но не блокирует пользователя.
- Test/staging data не загрязняет production reports.

## Versioning и compatibility

- Изменение смысла event требует новой version или нового имени по проектной policy.
- Добавление optional property не должно менять старую семантику.
- Required property migration имеет rollout order для mixed frontend/backend versions.
- Consumers/dashboards фиксируют используемую version.
- Deprecated event имеет owner и removal date.
- Не переиспользуй старое имя для другого product question.

## Dedupe, order и time

Учитывай:

- React/SPA rerender и route transitions;
- double click;
- retry/reload;
- browser back/forward;
- multiple tabs/devices;
- offline/late events;
- server retry;
- timezone boundaries;
- clock skew.

`occurred_at` и `received_at` не взаимозаменяемы. Funnel window и reporting timezone должны быть
зафиксированы.

Dedupe не должна удалять два реальных повторных действия пользователя. Используй business/journey key,
а не только event name + user.

## Funnels, activation и retention

Для funnel зафиксируй:

- population/denominator;
- entry event;
- ordered/unordered steps;
- completion definition;
- allowed repeats;
- time window;
- cross-device/account behavior;
- exclusions;
- timezone;
- version/date range.

Activation - первое достижение конкретной ценности, а не просто регистрация. Пример для fitness
продукта может включать завершение onboarding и реальное полезное действие, но точное определение должно
следовать product decision.

Retention определяй по meaningful return action, а не любому page view. Не меняй definition после
просмотра данных ради красивой метрики.

## Experiments

Если появляется experiment:

- assignment происходит один раз на доверенной границе;
- variant сохраняется и стабилен;
- exposure event отправляется только при фактическом exposure;
- outcome не содержит sensitive payload;
- sample ratio mismatch и contamination проверяются;
- stopping rule/primary metric задаются до анализа;
- analytics failure не меняет product variant.

Не добавляй experimentation platform без task.

## Data quality

Проверь:

- schema validation;
- required property coverage;
- unknown event/property rate;
- duplicate rate;
- late/out-of-order rate;
- environment contamination;
- anonymous/auth transition;
- client/server count reconciliation;
- provider delivery failures;
- sudden volume drop/spike;
- funnel invariant violations;
- sensitive property scan.

Dashboard без data-quality checks создаёт ложную уверенность.

## AI и health/fitness features

AI product analytics может хранить:

- request started/completed/failed;
- general vs personalized high-level class;
- unavailable/tool-unavailable state;
- memory/rationale UI interaction;
- latency bucket или error class, если это не operational duplication.

Не хранит raw conversation, prompt, answer, tool args/results или exact user facts.

Fitness analytics events не содержат exact health/fitness measurements. Числовые данные остаются в
canonical product/reporting storage с соответствующим authorization.

## Tests

Минимально:

- schema valid/invalid;
- prohibited property rejected/redacted according to explicit policy;
- SPA rerender/double click/dedupe;
- server outcome vs client intent;
- anonymous -> auth continuity без cross-user merge;
- Web/TMA/Demo distinction;
- dev/test/prod isolation;
- consent/opt-out;
- provider unavailable/non-blocking behavior;
- late/out-of-order;
- event version compatibility;
- representative funnels;
- no raw AI/support/fitness content.

Для полного review используй `references/PRODUCT_ANALYTICS_CHECKLIST.md`.

## Формат результата

Опиши:

- product questions;
- event catalog changes;
- funnel/activation/retention definitions;
- identity и privacy decisions;
- implementation owners;
- validation/dashboard changes;
- tests и known blind spots.

## Не делай

- every-click tracking;
- sensitive session replay;
- full request/response logging в analytics;
- raw PII/health/fitness content;
- vendor lock-in в domain event contract;
- registration-as-activation без product rationale;
- dashboard без metric definition;
- legal/consent assumptions без проверки.
