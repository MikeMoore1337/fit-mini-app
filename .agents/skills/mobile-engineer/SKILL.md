---
name: mobile-engineer
description: >
  Engineer smartphone runtime behavior: mobile keyboard, safe areas, dynamic viewport, lifecycle,
  touch/device-specific behavior, offline/resume and Mobile Web/TMA runtime parity.
  Do not load solely because a responsive UI is visible on a phone.
---

# mobile-engineer

В v6 этот skill намеренно узкий.

## Не владеет

- общей visual composition - `$product-designer`;
- обычной responsive CSS implementation - `$frontend-engineer`;
- Telegram Bot/Mini App API contracts - `$telegram-engineer`;
- general UI audit - `$ui-audit`.

## Trigger

Используй при изменении/риске:

- mobile keyboard;
- input mode/focus restoration;
- safe areas;
- `visualViewport`;
- dynamic/stable viewport height;
- foreground/background;
- reload/resume;
- minimize/restore;
- offline/reconnect;
- touch-only behavior;
- stuck hover;
- gesture/pointer specifics;
- device memory/main-thread cost;
- Mobile Web/TMA runtime differences.

## Контекст YFC

Учитывай:

- телефон во время тренировки;
- одна рука;
- короткие паузы;
- повторные taps;
- пот/движение;
- interruptions;
- плохую сеть;
- keyboard;
- смену orientation/viewport;
- foreground return.

## Forms

Проверяй:

- `type`;
- `inputMode`;
- `enterKeyHint`;
- autocomplete;
- numeric keyboard;
- focus;
- error visibility;
- CTA при открытой keyboard;
- сохранение recoverable draft;
- отсутствие layout jump.

## Safe areas / viewport

Fixed/sticky UI не должен:

- перекрывать content;
- перекрывать focused field;
- конфликтовать с bottom navigation;
- уходить под system/Telegram chrome.

Смена viewport/theme/background не должна необоснованно сбрасывать route/dialog/form state.

## Lifecycle / network

Для critical flow проверяй по scope:

- reload;
- resume;
- background/foreground;
- offline/reconnect;
- stale server state;
- repeated submit;
- local draft recovery.

## TMA

Для Telegram-specific API/initData/BackButton/deep link используй `$telegram-engineer`.

Этот skill проверяет только smartphone runtime parity и physical interaction.

## Performance

Desktop localhost не является доказательством mobile quality.

Измеряй при необходимости:

- main-thread blocking;
- memory growth;
- animation jank;
- keyboard/sheet jank;
- resume cost;
- media loading;
- duplicate bundles.

## Verification

Выбирай representative viewports по task, обычно:

- 360;
- 390;
- 430;

и применимые keyboard/touch/lifecycle states.
