---
name: observability-engineer
description: >
  Design production observability using correlated logs, metrics, traces, health checks,
  SLO-oriented alerts and product-critical signals. Use when a deployed system needs diagnosis,
  monitoring or operational feedback; do not add telemetry without a concrete question it must answer.
---

# observability-engineer

Наблюдаемость должна позволять ответить минимум на три вопроса:

1. Что сломалось или деградировало?
2. Где и почему это произошло?
3. Как это влияет на пользователя/критический продуктовый сценарий?

Не добавляй telemetry ради количества dashboards.

## Correlation

Связывай там, где инфраструктура это позволяет:

`user action -> frontend/API request -> backend operation -> DB/external dependency -> result`

Используй request/correlation ID и trace/span context так, чтобы инженер мог перейти от симптома к
конкретному запросу или операции. Не используй user ID как высококардинальный label метрики.

## Logs

- structured, если инфраструктура это поддерживает;
- timestamp, severity, service/component;
- request/correlation/trace context;
- meaningful error context;
- machine-readable event names для важных событий;
- без паролей, токенов, cookies, full request bodies и лишних персональных данных.

Лог должен помогать расследовать событие, а не дублировать весь runtime state.

## Metrics

Выбирай небольшое число показателей, связанных с состоянием продукта:

- request rate;
- error rate;
- latency;
- saturation;
- queue/job metrics;
- dependency health;
- resource pressure;
- business/product-critical success/failure signals.

Избегай unbounded/high-cardinality labels вроде raw user IDs, UUID и динамических URL.

## Traces

Для распределённых или интеграционно сложных критических путей используй traces, если observability
stack это поддерживает.

Trace должен помогать увидеть:

- где проведено время;
- какой dependency вызвал ошибку/задержку;
- retries;
- fan-out;
- важные async boundaries.

Не трассируй чувствительные payloads только ради удобства диагностики.

## Product-critical signals

Для ключевого пользовательского сценария предпочитай сигнал уровня результата, например:

- сохранение тренировки/заказа/документа успешно;
- checkout завершён;
- импорт обработан;
- scheduled job дал ожидаемый пользовательский результат.

Это полезнее, чем считать только HTTP 2xx. Определи signal по фактической бизнес-семантике продукта
и не выдумывай продуктовые KPI без данных.

## Frontend/RUM

Если продукт имеет web frontend и инфраструктура поддерживает RUM, измеряй релевантные:

- Core Web Vitals;
- client-side exceptions;
- failed resource/chunk loads;
- navigation/API failure;
- critical flow success/failure.

Минимизируй пользовательские данные в telemetry и согласуй чувствительные поля с `$privacy-engineer`.

## Health

Различай по необходимости:

- liveness;
- readiness;
- dependency health.

Не делай health endpoint тяжёлым и не делай readiness зелёным, если сервис заведомо не способен
обслуживать основной запрос из-за обязательной зависимости.

## Alerts и SLO

Алерт должен требовать действия.

Предпочитай симптомы и user/SLO impact, а не шумные внутренние события. Для каждого важного alert
должно быть понятно:

- что означает сигнал;
- насколько он срочный;
- где начать расследование;
- какие dashboards/logs/traces связаны с ним;
- какой recovery/rollback возможен.

Не алерти на метрику только потому, что её можно измерить.

## Verification

Для критического сбоя мысленно или тестом пройди путь расследования:

1. alert/symptom;
2. affected user flow;
3. metric or trace;
4. конкретная операция;
5. correlated logs;
6. dependency/root cause.

Если этот путь невозможен, наблюдаемость критического сценария неполна.
