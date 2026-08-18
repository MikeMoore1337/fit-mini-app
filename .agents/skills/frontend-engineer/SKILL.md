---
name: frontend-engineer
description: Frontend application architecture, state, forms, accessibility, performance and browser verification.
---

# frontend-engineer

Строй frontend как поддерживаемое приложение.

## Архитектура

- разделяй domain/state/view responsibilities;
- переиспользуй компоненты по смыслу, а не ради абстракции;
- не создавай god-components;
- держи серверное и клиентское состояние различимыми;
- избегай дублирования derived state;
- используй существующие conventions проекта.

## Данные

- типизируй contracts;
- учитывай loading/error/empty/stale states;
- отменяй/игнорируй устаревшие запросы там, где возможны race conditions;
- не доверяй клиенту в вопросах авторизации и критических бизнес-правил;
- обрабатывай network failures.

## Формы

- schema validation;
- доступные labels/errors;
- server-side validation остаётся обязательной;
- double submit и повторные запросы должны быть безопасны.

## Производительность

Не оптимизируй вслепую.

Следи за:

- bundle size;
- лишними render;
- тяжёлыми зависимостями;
- image/font loading;
- layout shift;
- длинными main-thread задачами.

## Доступность

Семантика, клавиатура, focus, ARIA только там, где нужно, contrast, reduced motion.

## Проверки

Добавляй unit/component/integration/e2e тесты пропорционально риску.
Для визуальных изменений проверяй реальный браузер.
## Адаптация к проекту

Сначала определи framework, language/type system, state/data-fetching approach, component system,
package scripts и browser/e2e tooling. Следуй существующим conventions. Для существенных
визуальных изменений используй `ui-audit` и проверяй фактический render.
