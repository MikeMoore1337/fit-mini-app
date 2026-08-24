# Design V2.1 — responsive rules

## Breakpoint model

Breakpoints trigger composition changes, not device labels.

| Range / target | Contract |
| --- | --- |
| `360x800` | minimum supported phone; `16px` gutters; one-column; no clipped Russian labels |
| `390x844` | baseline Mobile Web/TMA board; one-column; `16px` gutters |
| `430x932` | large phone; `20px` gutters; still mobile navigation |
| `768x900` | tablet/small desktop; Landing tablet composition; app retains mobile nav until `900px` |
| `900–1023` | desktop rail starts at `220px`; app content one/two regions by data need |
| `1024` | compact desktop Landing and Login split; `24px` outer gutters |
| `1280` | full desktop composition; `32px` gutters; max containers apply |
| `1440` | reference desktop composition; no uncontrolled whitespace expansion |

Global requirements at every width: no page-level horizontal overflow; 200% zoom/reflow preserves
the primary flow; long labels wrap or truncate only when full accessible name remains available.

## Landing composition by required width

| Width | Composition |
| ---: | --- |
| `1440` | Header `logo / nav / sign-in`; hero two columns `1.02fr/.98fr`; copy max `650px`, product proof max `580px`; next chapter begins near fold. Twelve-column sections, varied grouping, max `1180px`. |
| `1280` | Same desktop story; hero gap `40px`; product proof does not exceed `48%`; section padding reduced from `120` to `96px`; no scale/zoom. |
| `1024` | Two-column hero remains if each track is at least `420px`; `48–64px` display; nav may collapse to accessible menu at `<=980`; feature/dual-audience blocks use two columns where readable. |
| `768` | Tablet composition: header menu, hero copy before a full-width product proof, CTA visible before proof; sections one/two columns by content; workflow becomes two columns with final item spanning. |
| `430` | Mobile composition: logo/menu; promise → one primary CTA → readable workout proof in first meaningful sequence; `20px` gutters, `44px` display; secondary CTA moves below proof/context, not beside primary. |
| `390` | Same mobile order; `16px` gutters, `42px` display; proof values retain three aligned columns only if each value remains readable; otherwise two-row factual layout. |
| `360` | `40px` display; `16px` gutters; hero proof is flat/full-width, no negative margins or transform scaling; navigation/action targets `>=44px`; supporting copy capped to product truth, not hidden. |

Desktop and mobile are one system but different compositions. Mobile never uses whole-layout
`scale()`/`zoom`, overlapping fake device screens or desktop card grid squeezed into one column.

## `/login`

### Desktop `>=1024`

- Full viewport two-plane layout after public header; split exactly `1.04fr / .96fr`.
- Left continuation group vertically centered with `22px` minimum internal inline padding.
- Headline `35px`, one line. At `1024` it may reduce available copy width before reducing font;
  font never drops below `32px` on split layout.
- Right auth stack is centered on both axes. Provider control column is exactly `240px` wide;
  helper/error may expand to `min(360px, 100%)` while providers stay aligned to the 240px column.
- Four providers are a vertical stack; loading reserves stack geometry; provider error is adjacent
  and does not shift the primary recovery outside the viewport.

### Tablet `768–1023`

- Split collapses to one column: concise continuation first, provider stack second.
- Auth column width `min(100%, 400px)`; provider controls fill it. No 240px floating island.
- Header remains public/auth continuity; unused left-plane background is removed.

### Mobile `360/390/430`

- Header, title, factual helper, provider states in document order.
- Controls full width and at least `48px` high; `12px` gaps.
- Loading, error and cancellation keep all providers/retry visible with vertical scrolling.
- Keyboard: focused input, adjacent error, primary action and cancel/back remain above the visual
  viewport; draft is retained after recoverable errors.
- Valid signed TMA launch skips browser providers and continues to app loading/error boundary.

## Authenticated app shell

### Desktop `>=900`

- Rail: fixed `220px`, full stable viewport height, `12px` inline padding, `28px` top padding.
- Content body reserve: left `250px`, top `28px`, right `30px`, bottom `44px`. The `30px`
  content gutter after the rail equals the right viewport gutter, keeping the main canvas centered.
- Rail uses V2 logo, pictograms and type. Selected destination uses quiet secondary surface plus
  `3px` lime inline marker; no full-lime nav tile.
- Full lockup использует vertical stack на центральной оси rail: mark → `YOUR FITNESS` → `COACH`.
  Primary/secondary button surfaces также центрируются относительно rail, сохраняя общую колонку
  pictograms и labels; scrollbar gutter резервируется симметрично и не сдвигает navigation влево.
  Основной client group label `МОИ ДАННЫЕ` сохраняется на одной строке; более длинные capability
  headings могут переноситься без overflow.
- Нижний utility block центрируется в rail общей областью: theme pictogram + label остаются
  центрированы внутри полной ширины theme button, а account name и role выравниваются по общему
  левому краю внутри центрированной account-колонки `144px`, с logout в отдельной правой колонке
  второй строки. Независимое центрирование трёх строк запрещено, потому что создаёт расширяющийся
  вниз силуэт.
  Theme button сохраняет видимый `1px` contour; центр проверяется по фактическим границам pictogram
  и label относительно этого contour, а не по служебному icon box.
- Desktop typography scale для rail: primary destination `13px`, secondary/theme `12.8px`, account
  name `12.8px`, account meta около `11.5px`. Демо использует короткое plain-language meta
  `Отдельная сессия`, а не техническую формулировку, нарушающую ритм utility block.
- Main content `980px`; wide Progress/Coach may use `1180px`.
- Today: current workout region and progress/evidence region can sit side by side; current action
  receives greater width. Nutrition/Progress use aligned rules and shared metrics, not KPI tiles.
- Shared `WeekStrip`: контекст недели занимает первую grid-колонку; каждая строка легенды
  центрируется в оставшейся колонке справа, а не относительно внешних границ карточки.
- Coach: roster/context rail plus client detail at `>=1024`; client identity remains persistent.
  Destructive actions name the client. Dense tables retain text alternatives and explicit units.

### Mobile `<900`

- Bottom navigation is fixed to the stable viewport bottom, never after short content.
- Five destinations: `Сегодня`, `План`, `Прогресс`, `Питание`, `Ещё`; each `>=58px` plus safe area.
- Content bottom reserve equals nav measured height + safe/content inset + `12px` separation.
- `Ещё` opens a bottom sheet; secondary sections, account, theme and logout are grouped there.
- Screen composition remains V2. Related facts are closer (`12–18px`); section changes remain
  `28px`; body/meta/font guardrails are unchanged.

## Feature-specific mobile rules

- Today: одно primary workout action показывается до nutrition/progress facts; контекст недели
  остаётся компактным и не превращается в notification feed. После переноса legend сохраняет
  центрирование в правой колонке.
- Active workout: sticky top context contains back + short title only; full plan/day/status stays
  in hero. Current set has two numeric fields and a full-width completion action. Rest timer,
  bottom nav, toast and keyboard never overlap.
- Nutrition: add action precedes date/balance; summary before meal details; unavailable/incomplete/
  intentionally unfilled states are textually distinct.
- Progress: period control scrolls only inside itself if needed; charts show units/period and have
  a readable fact/table equivalent. Cards do not become a wide table on mobile.
- Coach fallback: roster → selected client detail as sequential views; back returns to preserved
  roster scroll/filter; complex parallel editing is not squeezed into columns.

## Viewport, keyboard and safe-area layout formula

Production browser/TMA adapter публикует shared CSS variables:

```css
--yfc-viewport-stable-height: 100dvh;
--yfc-safe-top: max(env(safe-area-inset-top, 0px), var(--yfc-tg-safe-top));
--yfc-safe-right: max(env(safe-area-inset-right, 0px), var(--yfc-tg-safe-right));
--yfc-safe-bottom: max(env(safe-area-inset-bottom, 0px), var(--yfc-tg-safe-bottom));
--yfc-safe-left: max(env(safe-area-inset-left, 0px), var(--yfc-tg-safe-left));
--yfc-content-safe-top: var(--yfc-tg-content-safe-top);
--yfc-content-safe-bottom: var(--yfc-tg-content-safe-bottom);
```

В TMA Telegram `viewportStableHeight` закрепляет bottom-pinned UI; `viewportHeight` — только
live observation для keyboard/resize, а не animation frame source. Browser fallback использует
`100dvh` и `visualViewport` для видимости focused content. Viewport/theme/safe-area events не
сбрасывают route, open sheet, dialog или form draft.

## State and interaction verification matrix

- Themes: Light/Dark with identical hierarchy.
- Input: touch/`hover:none`, mouse/keyboard; pressed state exists without hover.
- Content: short/long Russian names, large numbers, no data, partial data.
- Runtime: initial loading, recoverable error, offline/reconnect, background/foreground, reload.
- Motion: default/reduced.
- Runtime evidence targets: `360x800`, `390x844`, `430x932`, `768x900`, `1024x900`,
  `1280x900`, `1440x900`; mocked TMA всегда отделяется от real Android/iOS evidence.
