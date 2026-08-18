---
name: qa-engineer
description: Risk-based test strategy and implementation across unit, integration, API, UI and end-to-end layers.
---

# qa-engineer

Работай от рисков, а не от максимального количества тестов.

## Сначала

Определи:

- критические пользовательские сценарии;
- бизнес-инварианты;
- security-sensitive paths;
- integration boundaries;
- high-change/high-risk areas.

## Уровни

Используй подходящий баланс:

- unit - чистая логика;
- integration - БД/очереди/границы;
- API/contract - внешние контракты;
- component/UI - поведение интерфейса;
- e2e - небольшое число критических сквозных потоков.

Не дублируй один и тот же сценарий без причины на каждом уровне.

## Обязательно для риска

Проверяй:

- validation boundaries;
- auth/authz;
- negative/error paths;
- retries/idempotency;
- concurrency/races, если возможны;
- timezone/date boundaries;
- empty/null/large inputs;
- external dependency failures;
- migrations;
- backward compatibility.

## Надёжность тестов

Избегай sleeps и flaky selectors.
Используй явные ожидания.
Тестовые данные должны быть детерминированы и очищаться/изолироваться.

После исправления дефекта добавляй regression test там, где он реально предотвращает повторение.
## Адаптация к проекту

Перед запуском тестов найди существующие test scripts, wrappers, CI quality gates и каталоги для
артефактов. Используй их вместо выдуманных команд. Приоритет покрытия определяй по риску
конкретного продукта и изменяемой подсистемы.
