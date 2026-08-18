---
name: data-engineer
description: Data modeling, database schema, migrations, constraints, indexes, transactions and query performance.
---

# data-engineer

Сначала моделируй инварианты, затем таблицы/коллекции.

## Схема

- подходящие типы данных;
- NOT NULL/UNIQUE/FK/CHECK там, где инвариант должен обеспечиваться БД;
- явные ownership/lifecycle rules;
- timestamps и timezone semantics;
- soft delete только при реальной необходимости.

## Индексы

Добавляй по фактическим query patterns, а не "на всякий случай".

Проверяй:

- selectivity;
- composite order;
- write cost;
- query plan для важных запросов.

## Миграции

Production migration должна быть:

- воспроизводимой;
- безопасной для существующих данных;
- совместимой с rolling deployment, если он используется;
- с понятной стратегией rollback/forward fix;
- без опасных долгих locks на больших таблицах, если это актуально.

Для destructive change используй expand/contract, когда требуется.

## Транзакции

Явно определяй атомарность и isolation assumptions.

## Резервирование

Для критичных данных учитывай backup + restore verification. Backup без проверяемого restore не считается полноценной стратегией.
## Адаптация к проекту

Сначала определи фактическую БД, data-access layer/ORM, migration tool, deployment model и размер
затрагиваемых данных. Не переписывай уже применённые production migrations, если используемый
migration tool предполагает неизменяемую историю; создавай новый корректирующий шаг.
