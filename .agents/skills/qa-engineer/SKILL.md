---
name: qa-engineer
description: >
  Create risk-based test strategy and implement verification across unit, integration,
  contract/API, component/UI and end-to-end layers. Use when behavior changes, regressions must
  be prevented or release confidence is required. Prioritize critical user journeys over raw test
  count.
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
- e2e - небольшое число критических сквозных потоков;
- visual regression - стабильные критические представления, когда визуальный риск существенен;
- accessibility - автоматические проверки плюс ручная keyboard/focus проверка для важных потоков.

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
- backward compatibility;
- критические usability states: loading/error/empty/recovery;
- privacy-sensitive flows: export/deletion/telemetry leakage, если применимо.

## Надёжность тестов

Избегай sleeps и flaky selectors.
Используй явные ожидания.
Тестовые данные должны быть детерминированы и очищаться/изолироваться.

После исправления дефекта добавляй regression test там, где он реально предотвращает повторение.

Для web UI, если проект не задаёт иной accessibility target, используй WCAG 2.2 AA как baseline для применимых критериев, но не считай автоматический accessibility scanner достаточной проверкой.
## Адаптация к проекту

Перед запуском тестов найди существующие test scripts, wrappers, CI quality gates и каталоги для
артефактов. Используй их вместо выдуманных команд. Приоритет покрытия определяй по риску
конкретного продукта и изменяемой подсистемы.
