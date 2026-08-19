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
- Основная geometry — `6 px`, compact/icon — `4 px`; pill не является default.
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
- Offline save, pending sync, retry и duplicate-safe recovery видимы и сформулированы фактически.
- Exercise detail разделяет media, параметры программы, технику и long text; media не auto-play.

## Nutrition patterns

- Meal list, repeated actions и daily balance строятся alignment/rules, а не nested cards.
- Actual, target, remaining и units остаются одной системой. Превышение ориентира не маскируется
  success color.
- Quick add/Repeat остаются компактными, но доступными. Empty meal объясняет следующий шаг.

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
