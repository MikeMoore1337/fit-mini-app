# Design V2.1 — platform-контракт Telegram Mini App

## Принцип

TMA и Mobile Web используют один React component tree, Design V2 tokens, labels, routes и
business states. Отличия Telegram ограничены adapter-слоем. Нет отдельной Telegram-blue
palette, альтернативного набора cards/buttons, feature fork или Telegram-only bottom navigation.

Официальный API reference: `https://core.telegram.org/bots/webapps`.

## Trust boundary и launch

- Непустой raw `Telegram.WebApp.initData` обозначает кандидата на TMA launch; signature,
  freshness и bot binding всегда проверяет backend.
- `initDataUnsafe`, query parameters и frontend user identifiers не являются identity evidence.
- Raw `initData` не попадает в logs, analytics, rendered errors и third-party telemetry.
- Valid TMA launch не показывает browser provider list. Invalid/expired launch получает
  безопасный recovery boundary без автоматического перехода в другой account.
- Browser `/login` и Telegram OAuth остаются разными flows; V2.1 не меняет auth architecture.

## Shared layout adapter

Production adapter нормализует browser и Telegram values в один read-only snapshot для CSS/layout:

```ts
interface MobileViewportSnapshot {
  active: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  safeArea: { top: number; right: number; bottom: number; left: number };
  contentSafeArea: { top: number; right: number; bottom: number; left: number };
}
```

- CSS публикует нормализованные `--yfc-*` variables из `responsive-v2.1.md`.
- Browser fallback: `100dvh` и `env(safe-area-inset-*)`; неподдерживаемые Telegram fields дают
  zero/fallback, а не `undefined` в CSS.
- Adapter слушает `viewportChanged`, `safeAreaChanged`, `contentSafeAreaChanged`, `activated` и
  `deactivated`, когда methods доступны. Старые clients деградируют к browser CSS behavior.
- `viewportStableHeight` закрепляет bottom navigation и persistent sheets. `viewportHeight` отражает
  live keyboard/resize, но не управляет frame-by-frame bottom animation.
- Safe area защищает от device/system UI; content safe area дополнительно учитывает Telegram
  chrome. Берётся больший применимый inset; два inset не суммируются вслепую.
- Theme, viewport, safe-area и foreground events обновляют только layout и не пересоздают
  provider, router, query cache, dialog, workout или draft state.

## Keyboard

- При focus ближайший owning region scroll сохраняет label, field, adjacent error и
  primary/cancel action в current viewport.
- Bottom navigation не перекрывает form actions над keyboard. Shared mobile layout state может
  временно скрыть nav; после focusout nav возвращается без reset route, scroll и draft.
- Numeric fields тренировки, питания и замеров имеют корректный mobile keyboard и
  сохраняют draft при viewport changes.
- Keyboard mock в frozen render задаёт composition, но не доказывает работу реальной OS keyboard.

## BackButton

| Контекст                         | Поведение                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------- |
| `/`, `/onboarding`, root `/app`  | Скрыт.                                                                       |
| Nested app route/section         | Видим; возвращает в `/app` или предыдущий allowlisted internal context.      |
| Workout feedback query           | Видим; возвращает в `/app?section=progress` с replace временной entry.       |
| Sheet/dialog с dismiss semantics | Первое нажатие закрывает верхний overlay; route не меняется.                 |
| Unsaved critical draft           | Перед выходом работает тот же in-product confirmation; silent loss запрещён. |

В active workout на root `/app` сохраняется видимый in-page back `К сводке`, а native Telegram
BackButton остаётся скрытым. Дублирующий native control запрещён.

Кнопкой владеет только один active handler через общий priority coordinator. Верхний modal/sheet
или последовательный mobile client detail временно получает приоритет над route handler; первое
нажатие закрывает верхний контекст, следующее выполняет route return. Cleanup восстанавливает
предыдущего владельца либо скрывает button, поэтому параллельные callbacks не срабатывают.
Browser Back следует той же navigation semantics без дублирующего TMA control.

## Theme и shell colors

- Telegram `colorScheme` выбирает YFC Light/Dark; `themeParams` могут дать только fallback.
- Semantic YFC colors остаются источником contrast; произвольные Telegram button/link colors не
  заменяют accent/error/success semantics.
- `setHeaderColor`, `setBackgroundColor` и `setBottomBarColor` получают YFC shell colors;
  неподдерживаемые methods/errors безопасно игнорируются.
- `themeChanged` обновляет tokens и shell colors без смены visual language и user state.

## Foreground recovery

- Переход `deactivated -> activated` публикует один shared recovery event поверх layout snapshot.
- Authenticated profile refresh и active-workout queue используют этот event вместе с обычными
  browser `focus`/`visibilitychange`/`online`, потому что Telegram client не обязан синхронно менять
  все browser lifecycle signals.
- Temporary network error на restore не очищает session, route, modal или локальную workout queue.

## Haptics

- `notificationOccurred('success')` — server-confirmed completion подхода, записи или тренировки,
  когда тактильное подтверждение уместно.
- `notificationOccurred('warning'|'error')` — вызванная user action ситуация, требующая
  внимания, а не passive background fetch failure.
- Haptics — optional enhancement, а не единственное confirmation. Они вызываются только
  из Telegram adapter; failure игнорируется.
- Haptic не вызывается на navigation, scroll, каждый keystroke или decorative transition.

## Deep links и close/return

- Принимаются только существующие allowlisted internal start contexts и validated resource tokens.
- Сохраняется deterministic return path в `/app` или исходный product section.
- Переход на arbitrary URL/path из raw `startapp` запрещён.
- V2.1 не вводит новый deep-link type. Известный residual risk `R49D-11` зафиксирован в
  `codex-backlog/archive/DESIGN_V2_1_INTEGRATION_NOTES.md` и не входит в visual rollout.

## Platform buttons, `ready` и `expand`

- Shared in-app controls остаются canonical. `MainButton`/`SecondaryButton` не выбраны и не
  дублируют mobile primary action.
- `ready()` вызывается после готовности critical UI/theme shell, а не до empty root.
- `expand()` может запросить available height, но не заменяет responsive layout и не
  гарантирует full-screen/stable height.

## Barcode camera hierarchy

- На touch-first surface при фактической поддержке `BarcodeDetector` и `getUserMedia`
  `Сканировать камерой` — единственный primary action и расположен раньше ручного ввода.
- Ручной ввод остаётся доступным fallback. Его `Найти` выровнен с полем штрихкода, а hint/error
  располагаются под общей строкой; когда камера доступна, ручной action имеет secondary hierarchy.
- Если camera capability отсутствует, disabled primary action не показывается: `Найти` становится
  primary, а интерфейс кратко объясняет ручной fallback.
- На desktop/fine-pointer surface camera action скрыт даже при наличии webcam: ручной поиск остаётся
  primary. Tablet/hybrid получает camera-first только когда основной input действительно coarse и
  без hover.

## Evidence и ограничения

1. Adapter покрыт unit tests для snapshot, event cleanup и unsupported/fallback values.
2. Mocked TMA проверяет safe/content insets, stable/live viewport, keyboard, BackButton ownership,
   неиспользование дублирующих `MainButton`/`SecondaryButton` и фактические haptic calls на
   production seam.
3. Mobile Web/TMA остаются одним component tree для Today и active workout.
4. Raw `initData` не логируется на изменённых paths.
5. Real Telegram Android/iOS smoke выполняется только в доступной авторизованной среде.
   В task 49G `REAL_TELEGRAM = NOT_RUN`; static boards и Chromium mocks не являются real-client evidence.
