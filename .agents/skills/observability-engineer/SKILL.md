---
name: observability-engineer
description: Logs, metrics, traces, health checks and actionable alerts for production operation.
---

# observability-engineer

Наблюдаемость должна отвечать на вопрос "что сломалось и почему?".

## Logs

- structured, если инфраструктура это поддерживает;
- request/correlation ID;
- severity;
- meaningful context;
- без паролей, токенов, cookies и лишних персональных данных.

## Metrics

Выбирай показатели, связанные с состоянием продукта:

- request rate;
- error rate;
- latency;
- saturation;
- queue/job metrics;
- dependency health;
- business-critical success/failure signals.

Не создавай сотни бесполезных метрик.

## Health

Различай по необходимости:

- liveness;
- readiness;
- dependency health.

Не делай health endpoint тяжёлым.

## Alerts

Алерт должен требовать действия.

Предпочитай симптомы и SLO-impact, а не шумные внутренние события.

Для критических сценариев определи, как инженер сможет найти конкретную проблему по логам/метрикам/traces.
