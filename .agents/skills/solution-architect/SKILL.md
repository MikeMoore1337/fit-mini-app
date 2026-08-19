---
name: solution-architect
description: >
  Design or change system boundaries, APIs, data flow, integrations, deployment topology and
  major technical trade-offs. Use before significant architectural changes or cross-component
  work. Prefer the simplest architecture that satisfies real reliability, security, privacy and
  operability requirements.
---

# solution-architect

Проектируй минимальную архитектуру, которая выдерживает реальные требования.

## Сначала

Определи:

- требования и ограничения;
- текущий стек;
- expected load;
- consistency requirements;
- failure modes;
- security boundaries;
- privacy/data lifecycle boundaries;
- observability requirements for critical flows;
- deployment environment;
- skills команды и стоимость поддержки.

## Затем

Опиши:

- компоненты и их ответственность;
- data flow;
- API/contract boundaries;
- модель хранения;
- транзакционные границы;
- фоновые процессы;
- кэширование только при необходимости;
- идемпотентность там, где возможны повторные запросы;
- retry/backoff только для безопасно повторяемых операций;
- timeout/circuit-breaking на внешних интеграциях при необходимости;
- versioning и backward compatibility;
- миграции;
- failure isolation;
- observability/correlation points for critical paths;
- data retention/deletion boundaries where sensitive data is involved;
- deployment topology.

## Запрещённые привычки

Не вводи микросервисы, message broker, Kubernetes, CQRS/Event Sourcing, Redis или сложный DDD автоматически.

Каждый крупный инфраструктурный компонент должен иметь конкретную причину.

Предпочитай modular monolith, если требования не требуют распределённой системы.

## ADR

Для спорных архитектурных решений фиксируй:

- контекст;
- решение;
- альтернативы;
- последствия.

Не создавай ADR для очевидных локальных решений.
## Адаптация к проекту

Сначала зафиксируй фактическую текущую архитектуру и ограничения репозитория. Предпочитай
эволюционное улучшение существующей системы. Для cross-cutting change перечисли все реально
затронутые surfaces: приложения/сервисы, данные, contracts, tests, deployment и documentation.
