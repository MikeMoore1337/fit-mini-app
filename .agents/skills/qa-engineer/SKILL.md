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

## Mobile/TMA continuous gate

Для client-facing YFC task используй `references/MOBILE_TMA_ACCEPTANCE_MATRIX.md` и общий harness task `50A`.

Минимум:

- `360x800`, `390x844`, `430x932`;
- touch и `hover: none`;
- no horizontal overflow и touch-target review;
- keyboard/focus/safe-area/stable viewport;
- light/dark/reduced motion;
- reload/background/offline/reconnect, если flow хранит состояние;
- Mobile Web и mocked TMA parity;
- desktop regression.

Feature task должна добавить или расширить релевантный continuous smoke. Не создавать второй TMA fixture layer.

Разделяй evidence:

1. automated Mobile Web;
2. mocked TMA adapter;
3. real Telegram Android;
4. real Telegram iOS;
5. непроверенные среды.

Не использовать skipped tests как способ закрыть platform gap и не писать `проверено на мобильных`, если был только desktop browser с узким viewport.

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
