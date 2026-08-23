# Design V2: принципы компонентов

## Общий контракт

Компонент существует для повторяемой семантики и поведения, а не только одинакового border/radius.
Он использует shared tokens, поддерживает Light/Dark и релевантные состояния. Локальная страница не
создаёт собственную палитру, control geometry, focus ring или error pattern.

## Buttons

- На surface один визуально главный action: ключевой primary получает lime fill и `on-lime`.
  Несколько соседних lime fills запрещены.
- Primary обозначает следующий безопасный шаг; provider choices, navigation, secondary и recovery
  сохраняют neutral surface/border; danger используется только для действительно опасного действия.
- Основная geometry buttons и form controls — `12 px`, compact controls — `8 px`; pill не является
  default. Круглая geometry допустима для icon-only controls с соответствующей семантикой.
- Loading не меняет ширину и блокирует double submit. Disabled объясняет причину, если она не
  очевидна. Icon-only control имеет accessible name и touch target не меньше `44 px`.

## Inputs и forms

- Постоянный label важнее placeholder. Unit и допустимый диапазон видны рядом с вводом.
- Validation находится рядом с причиной, не заменяет значение и не выдаёт network error за ошибку
  поля.
- Keyboard order следует визуальному порядку; mobile input type помогает вводу, но server-side
  validation остаётся source of truth.
- Long form использует sections/progressive disclosure, а не stack одинаковых cards.

## Navigation

- Выбранный раздел использует одновременно neutral active surface, усиленный вес label и lime
  boundary. Одного тонкого lime marker без изменения surface недостаточно.

- Desktop contextual rail даёт location и быстрый переход, но не конкурирует с содержимым.
- Mobile navigation сохраняет главные destinations и не перекрывает keyboard, input или current
  workout action.
- Active state выражается не только lime. Capability-based пункты не появляются без права доступа.
- Full lockup обязателен на identity surfaces; mark-only разрешён только в compact context.

## Cards и containers

Card оправдана при самостоятельной задаче, entity context, selection, elevation или важной границе
recovery. Rule, whitespace и typography предпочтительнее, если они уже сохраняют структуру. Card
inside card и универсальная `surface` вокруг каждого subsection запрещены.

## Tables и lists

- Строки выравнивают labels, values, units и actions; related data не дробятся на KPI cards.
- Dense desktop table сохраняет scan path и keyboard access. На mobile выбирается priority order,
  grouped rows или controlled disclosure, а не горизонтальный squeeze.
- Empty row не выглядит как populated zero. Row action остаётся рядом с сущностью и имеет понятный
  destructive/undo contract.

## Dialogs, drawers и sheets

- Dialog используется для короткого blocking decision; drawer/sheet — для контекста, который можно
  закрыть без потери основного места.
- Нужны title, close action, focus trap/return, Escape, scroll lock и safe-area/keyboard behavior.
- Destructive confirmation описывает объект и последствие. Toast не перекрывает header/close или
  current mobile action.

## Charts и progress

- Progress показывает current/total и period. Color не является единственным различием series.
- Chart labels, axes, units, empty/insufficient states и methodology доступны без hover-only UI.
- Skeleton не изображает вымышленные data points. Reduced motion не скрывает финальное значение.

## Workout patterns

- Current exercise/set и flow `Вес → Повторы → Готово` имеют первый приоритет.
- Rest — отдельное state с theme-native surface и lime boundary; оно не конкурирует с primary CTA.
- Completed set отличается от editable current set. Post-finish controls не остаются в конфликтном
  состоянии.
- Упражнения являются самостоятельными task regions с geometry `16 px`, видимой boundary и
  spacing между ними; подходы остаются более плоскими внутри упражнения и не сливаются с соседней
  группой.
- Offline save, pending sync, retry и duplicate-safe recovery видимы и сформулированы фактически.
- Exercise detail разделяет media, параметры программы, технику и long text; media не auto-play.

## Nutrition patterns

- Meal list, repeated actions и daily balance строятся alignment/rules, а не nested cards.
- Actual, target, remaining и units остаются одной системой. Превышение ориентира не маскируется
  success color.
- Quick add/Repeat остаются компактными, но доступными. Empty meal объясняет следующий шаг.

## Недельный контекст и выбор даты

- Канонический недельный блок приложения — shared-компонент `WeekStrip` из
  `frontend/src/shared/ui/WeekStrip.tsx`. Страницы `Сегодня`, `Питание` и будущие surfaces с
  семидневным контекстом переиспользуют его; локальные копии разметки, диапазона дат и CSS-сетки
  не создаются.
- Компонент имеет два смысловых режима. `overview` показывает недельный контекст и доменные
  статусы, а ссылкой делает только день с реальным доступным действием. `picker` выбирает дату,
  сохраняет явную навигацию между неделями и не смешивает выбранную дату с календарным сегодня.
- На desktop компонент использует спокойный contained surface, полный доступный width и семь
  равных колонок. На Mobile Web/TMA он становится плоским, отделяется rule, собирает заголовок и
  icon-only week controls в одну строку и не образует card inside card.
- `aria-current="date"` обозначает только календарное сегодня. В `picker` выбранный день задаётся
  через `aria-pressed`; в `overview` статус дня передаётся также текстом в accessible name, а не
  только цветом или marker.
- Previous/next controls и интерактивные дни сохраняют touch target не меньше `44 px`, видимый
  `focus-visible` и полный русский accessible name. Swipe может дополнять навигацию, но не заменяет
  кнопки.
- Доменная страница передаёт только состояние или действие дня. Формат диапазона, weekday labels,
  responsive geometry, selected/current presentation, loading announcement и базовая семантика
  остаются ответственностью `WeekStrip`.
- Контент до и после `WeekStrip` остаётся в обычном layout flow. Бейджи, подсказки и page-specific
  actions не накладываются на недельный блок отрицательными margin или absolute positioning. Для
  страниц с соседним контентом e2e-проверка сравнивает bounding boxes блока и следующего элемента
  на desktop и контрольных mobile widths.

## Loading, empty, error и access states

- **Loading:** сохраняет будущую hierarchy и не подменяет отсутствие данных нулём.
- **Empty:** объясняет, что будет после первого действия, и даёт один next step.
- **Error:** локальная ошибка не стирает рабочий shell или уже загруженные данные; retry безопасен.
- **Validation:** конкретна, связана с field и сохраняет ввод.
- **Permission:** называет границу доступа и безопасный путь назад.
- **Expired session:** ведёт к canonical `/login`, не смешивает данные аккаунтов.
- **Offline/stale:** сообщает, что сохранено локально, что устарело и когда будет sync.
- **Disabled:** остаётся различимым и сопровождается причиной.

## Запрет локальных visual systems

Нельзя вводить экранные цвета, radii, button family, loading/error shell, chart palette или motion,
если существующая semantic роль решает задачу. Новая роль сначала доказывается на нескольких
surfaces и только потом входит в shared Design V2 system.
