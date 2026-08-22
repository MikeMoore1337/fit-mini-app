# Mobile Web/TMA acceptance matrix

Эта матрица применяется к client-facing Your Fitness Coach flows. Она не расширяет scope task и не превращает TMA в отдельный продукт.

## 1. Surface priority

```text
Personal/client daily flows -> smartphone-first
Mobile Web + Telegram Mini App -> основные клиентские поверхности
Desktop Web -> полноценная дополнительная поверхность
Coach/Admin data-heavy work -> desktop-first, если task указывает это явно
```

Один frontend, одна Design V2, один API/domain contract. TMA отличается только platform adapter и реальными ограничениями Telegram runtime.

## 2. Automated viewport matrix

Минимум для изменённого client-facing flow:

| Surface | Размер | Input |
|---|---:|---|
| Compact phone | `360x800` | touch, `hover: none` |
| Baseline phone | `390x844` | touch, `hover: none` |
| Large phone | `430x932` | touch, `hover: none` |
| Tablet/small desktop smoke | `768x900` | touch/keyboard where relevant |
| Desktop regression | `1280` или `1440` | mouse/keyboard |

Проверяй device pixel ratio только когда он влияет на media, canvas, icon или screenshot quality.

## 3. Interaction

- Одно очевидное primary action на основном экране.
- Основные touch targets практически удобны, ориентир не меньше 44x44 px.
- Нет обязательного горизонтального scroll, кроме обоснованной специализированной области с доступной альтернативой.
- UI не зависит от hover.
- Double tap/retry не создают дублирующее действие.
- Bottom navigation, sticky CTA, timer, toast и sheet не перекрывают друг друга.
- Длинные названия упражнений, продуктов, клиентов и локализованный текст не вытесняют действие.
- Для тренировки учитывать управление одной рукой, короткие паузы и частые отвлечения.

## 4. Forms и keyboard

- Корректные `type`, `inputMode`, `enterKeyHint`, autocomplete и label.
- Numeric fields открывают подходящую клавиатуру.
- Active field, validation message, primary action и способ закрыть flow видимы при keyboard.
- Focus не прыгает после rerender, theme/viewport event или server response.
- Recoverable error не стирает введённые данные.
- Keyboard close/reopen не оставляет неверную высоту layout.

## 5. Safe areas и viewport

- Browser `env(safe-area-inset-*)` и Telegram safe-area values проходят через один layout contract.
- Fixed/sticky UI учитывает `safeAreaInset` и `contentSafeAreaInset`.
- Используется стабильная высота viewport там, где Telegram keyboard/drag может менять текущую высоту.
- `viewportChanged`, `safeAreaChanged` и `contentSafeAreaChanged` не сбрасывают route/form/dialog state.
- Проверяется portrait. Landscape нужен только если task его поддерживает или реальный flow ломается при повороте.

## 6. Telegram Mini App platform contract

- На backend передаётся raw `initData`; identity не берётся из `initDataUnsafe` или query params.
- Valid TMA launch не проходит второй browser login.
- `ready()` вызывается после готовности критического UI; `expand()` не используется как замена responsive layout.
- Telegram Light/Dark выбирает YFC Light/Dark, не создавая Telegram-only palette.
- `isActive`/foreground restore не уничтожает незавершённое состояние.
- `BackButton` согласован с router/history/dialog/sheet lifecycle.
- Deep links открывают allowlisted внутренний контекст и имеют предсказуемый return path.
- `MainButton`/`SecondaryButton` применяются только при доказанной пользе и не дублируют shared controls.
- Unsupported/older client получает graceful fallback.
- Raw `initData` не попадает в logs, analytics, errors или third-party telemetry.

При реализации названия полей/events и поддерживаемые версии перепроверяются по актуальной официальной Telegram Mini Apps документации.

## 7. Lifecycle, сеть и storage

- Проверить reload, background/foreground, offline/reconnect и повторное открытие TMA для recoverable flows.
- Подтверждённое действие не теряется и не применяется повторно.
- Draft/queue scoped к account/resource; logout/account switch исключают cross-user state.
- Чувствительные данные не сохраняются в небезопасном storage без отдельного решения.
- Stale/conflict/corrupted local state имеет понятное восстановление.

## 8. Accessibility и states

- Light/dark, loading, empty, partial, error, offline, disabled, success, long-content.
- Keyboard/focus restoration и touch-only operation.
- Смысл статуса не передаётся только цветом.
- `prefers-reduced-motion` поддержан.
- Charts имеют units, period, текстовую/табличную альтернативу и touch-friendly exploration.
- Screen zoom/reflow не блокирует основной сценарий.

## 9. Performance

- Отдельно смотреть Mobile Web и TMA initial/core-flow cost.
- Нет platform-specific duplicate component/CSS bundle.
- Media lazy-loaded, размеры зарезервированы, CLS отсутствует.
- Keyboard/sheet/foreground resume не вызывают заметный main-thread jank.
- Не загружать тяжёлые charts/media до открытия.
- Lab measurement не выдаётся за field data.

## 10. Evidence levels

В отчёте разделять:

1. automated Mobile Web;
2. mocked TMA adapter;
3. real Telegram Android;
4. real Telegram iOS;
5. Telegram Desktop, если проверялся;
6. непроверенные среды и ограничения.

Нельзя писать `проверено на мобильных`, если были только viewport emulation или unit tests.

## 11. Per-task exit

Client-facing task завершена только когда:

- feature-specific mobile/TMA scenario добавлен или доказанно не затронут;
- `360/390` touch flow проходит;
- keyboard/safe area/lifecycle проверены там, где релевантны;
- browser desktop regression не сломан;
- нет отдельного TMA component tree/palette/business logic;
- точные проверки и ограничения указаны в отчёте.
