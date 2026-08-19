# Reference renders Design V2

## Статус

Эти PNG фиксируют owner-selected направление A / Quiet Pace для финального checkpoint task `46F`.
Они являются visual source of truth вместе с `docs/design/*v2*`, но не означают, что production UI
уже изменён или что pilot разрешён.

Рабочий воспроизводимый prototype находится в `.artifacts/design-v2/approved/` и не коммитится.
Canonical assets содержат только representative crops, без тяжёлых full-board exports.

## Каталог

| Surface | Light | Dark |
|---|---|---|
| Landing desktop | `landing-desktop-light.png` | `landing-desktop-dark.png` |
| Landing mobile | `landing-mobile-light.png` | `landing-mobile-dark.png` |
| `/login` + AppShell/Today desktop | `login-today-desktop-light.png` | `login-today-desktop-dark.png` |
| Active Workout mobile | `active-workout-mobile-light.png` | `active-workout-mobile-dark.png` |
| Mobile Web / TMA composition | `mobile-web-tma-light.png` | `mobile-web-tma-dark.png` |
| Nutrition desktop | `nutrition-desktop-light.png` | `nutrition-desktop-dark.png` |
| Nutrition mobile | `nutrition-mobile-light.png` | `nutrition-mobile-dark.png` |
| Progress / analytics | `progress-analytics-light.png` | `progress-analytics-dark.png` |
| Program wizard + exercise detail | `programs-exercise-detail-light.png` | `programs-exercise-detail-dark.png` |
| Loading/empty/error/validation/access states | `system-states-light.png` | `system-states-dark.png` |

## UI audit и refinement

Проверка выполнена реальным Chromium render командой:

```powershell
node .artifacts/design-v2/approved/render-and-audit.mjs
```

Проверены `1440`, `1280`, `768`, `390` и `360 px` в Light/Dark: horizontal overflow, broken images,
console/page errors, внешние requests, semantic sections, core contrast, visible focus, minimum
`44 px` controls, `6/4 px` button geometry, reduced motion, theme palettes, обязательные surfaces и
ровно семь ключевых primary CTA с парой `lime`/`on-lime`.

Первый pass нашёл P2: program/mobile evidence создавали overflow `24 px` на `768 px`. Root cause —
двухколоночная композиция сохранялась после того, как content переставал безопасно сжиматься.
Refinement перевёл Landing mobile evidence и program wizard в stacked tablet composition. Повторный
запуск: `10` theme/viewport combinations, findings `0`, external requests `0`, gradients `0`.

После дополнительного owner feedback выполнен второй refinement: Landing, Today, Active Workout,
Nutrition и program result используют один lime primary CTA в локальном контексте. Provider login,
navigation, secondary, recovery и destructive actions остались нейтральными. Повторный audit также
завершился с findings `0`.

Проверенные минимальные core contrast ratios:

- Light secondary text on secondary surface — `5.50:1`;
- Dark secondary text on secondary surface — `7.26:1`;
- `on-lime` в Light — `10.61:1`;
- `on-lime` в Dark — `11.51:1`.

Это не является заявлением о полной WCAG 2.2 AA compliance будущей production реализации.

## Human Design Test

- Brand Swap — PASS: характер держат current-set notation, rest state, lime endpoint, compact rail
  и canonical lockup.
- Screenshot — PASS: Landing, dense data, workout и states имеют разный rhythm.
- Card — PASS: Nutrition/Progress используют rules; cards остаются у самостоятельных task regions.
- Decoration — PASS: нет glow, glass, gradients, blobs, synthetic people или fake social proof.
- Designer Intent — PASS: control/card geometry, density и lime имеют зафиксированную роль.
- Desktop/mobile hierarchy и Light/Dark parity — PASS в пределах static prototype.

## Ограничения

Static renders не доказывают production SEO, screen-reader semantics, focus order/traps, real API
loading/error/offline behavior, keyboard viewport, CLS или Telegram lifecycle. Это обязательные
проверки pilot после отдельного owner approval.
