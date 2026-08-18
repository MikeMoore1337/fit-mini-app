---
name: ui-audit
description: Audit an implemented UI in the real browser for layout, responsive behavior, accessibility and interaction defects.
---

# ui-audit

Проверяй фактический render, а не только исходный код.

Используй Playwright/browser tooling, если доступен.

Проверь репрезентативные размеры, обычно:

- 1440;
- 1280;
- 768;
- 390;
- 360.

Проверяй релевантные состояния:

- empty;
- loading;
- error;
- populated;
- hover;
- focus;
- disabled;
- validation;
- modal/drawer.

Классификация:

- P0 - блокирует критический сценарий;
- P1 - серьёзно мешает использованию/доступности;
- P2 - заметный дефект качества или согласованности;
- P3 - косметика.

Проверяй:

- hierarchy;
- grid/spacing;
- typography;
- components;
- responsive;
- overflow;
- fixed/sticky UI;
- touch targets;
- keyboard/focus;
- contrast;
- semantic HTML;
- interaction states;
- generic AI-patterns;
- clarity of labels/errors/CTA.

Не путай намеренное различие тем с дефектом.

Если нужно исправление - исправь root cause и повторно воспроизведи проблемное состояние.
## Адаптация к проекту

Используй фактические browser/e2e scripts и настроенный каталог артефактов проекта. Набор viewport
должен отражать поддерживаемые устройства; перечисленные размеры выше - отправная точка, а не
жёсткая матрица. Намеренные различия между platform themes не являются дефектом сами по себе.
