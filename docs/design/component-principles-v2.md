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
- Все action buttons приложения, Mobile Web/TMA, публичных auth surfaces и лендинга используют
  единый token `--radius-action` (`12 px`). Локальный `border-radius` для action button запрещён:
  responsive-состояние, primary/secondary/danger и ссылка, оформленная как кнопка, сохраняют ту же
  geometry. `8 px` остаётся только для compact controls, которые не являются action buttons; pill
  не является default. Круглая geometry допустима только для icon-only controls с соответствующей
  семантикой.
- Loading не меняет ширину и блокирует double submit. Disabled объясняет причину, если она не
  очевидна. Icon-only control имеет accessible name и touch target не меньше `44 px`.
- Самостоятельное secondary, danger или destructive text-action визуально остаётся кнопкой:
  имеет постоянный контур, достаточный padding и `44 px` touch target. Borderless допустим только
  для очевидного inline navigation/action внутри текста; появление контура лишь на hover запрещено.

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
- Secondary destinations, доступные в desktop rail, не прячутся в мобильный `Ещё`/bottom sheet на
  широком экране. Bottom sheet остаётся mobile-only; desktop использует inline rail group или
  привязанный к trigger popover, если inline-размещение невозможно.
- Active state выражается не только lime. Capability-based пункты не появляются без права доступа.
- Full lockup обязателен на identity surfaces; mark-only разрешён только в compact context.
- Full lockup в desktop `AppShell` строится вертикально на единой центральной оси rail: canonical
  mark, `YOUR FITNESS` и `COACH` центрируются друг относительно друга; локальные demo/account
  variants не меняют его alignment.
- Desktop navigation rows занимают симметричную относительно rail ширину. Primary/secondary
  hit areas и active surface центрируются как единые кнопки, а иконки и labels сохраняют общие
  внутренние колонки; нельзя центрировать каждую подпись независимо и ломать scan path.
- Desktop rail должен вмещать common destination labels и group heading `МОИ ДАННЫЕ` без переноса.
  При изменении ширины rail левый content reserve меняется на ту же величину: gutter после rail
  остаётся равен правому viewport gutter, поэтому main canvas не теряет симметрию.
- Desktop utility block центрируется в rail как единая область, а не как набор строк разной ширины.
  Icon и label внутри theme button центрируются как единая группа; account name и role получают
  общий левый край внутри центрированной account-колонки `144px`, а logout занимает устойчивую
  правую колонку во второй строке. Нельзя
  независимо центрировать theme, name и meta: такой stack образует визуальную «горку». Logout
  остаётся самостоятельным focusable action.
- Desktop theme button всегда показывает спокойный `1px` contour. Для визуального центрирования
  измеряется фактическая pictogram geometry, а не более широкий служебный icon cell; pictogram и
  label должны образовывать единую группу по центру видимого button border.
- После расширения desktop rail типографика сохраняет уверенную, но не растянутую иерархию:
  primary labels — `13px`, secondary/theme — около `12.8px`, account name — `12.8px`, account meta —
  около `11.5px`. Свободное место справа не заполняют чрезмерным font-size и не ломают общие
  icon/label columns; длинные capability labels обязаны оставаться полностью видимыми.

## Cards и containers

Card оправдана при самостоятельной задаче, entity context, selection, elevation или важной границе
recovery. Rule, whitespace и typography предпочтительнее, если они уже сохраняют структуру. Card
inside card и универсальная `surface` вокруг каждого subsection запрещены.

Группа равноправных метрик сохраняет внутренний padding у всех элементов, включая крайние, и
явный tokenized gap между соседями. Нельзя убирать padding первой/последней метрики ради визуального
слияния: labels и values не должны прижиматься к границе родительского region.

## Tables и lists

- Строки выравнивают labels, values, units и actions; related data не дробятся на KPI cards.
- Dense desktop table сохраняет scan path и keyboard access. На mobile выбирается priority order,
  grouped rows или controlled disclosure, а не горизонтальный squeeze.
- Empty row не выглядит как populated zero. Row action остаётся рядом с сущностью и имеет понятный
  destructive/undo contract.
- Между соседними list/settings groups не резервируется пустая высота без content, action или
  смысловой паузы. Разделение строится одним spacing step и rule, а не суммой padding двух блоков.

## Dialogs, drawers и sheets

- Dialog используется для короткого blocking decision; drawer/sheet — для контекста, который можно
  закрыть без потери основного места.
- Нужны title, close action, focus trap/return, Escape, scroll lock и safe-area/keyboard behavior.
- Destructive confirmation описывает объект и последствие. Toast не перекрывает header/close или
  current mobile action.

## Demo и conversion copy

- Если подготовленные данные не переносятся в аккаунт, conversion не обещает «сохранить»,
  «продолжить без потери контекста» или другой continuity результата.
- Текст разделяет увиденную механику и будущую работу с собственными данными; CTA называет честный
  следующий шаг: вход и настройку чистого профиля.

## Charts и progress

- Progress показывает current/total и period. Color не является единственным различием series.
- Chart labels, axes, units, empty/insufficient states и methodology доступны без hover-only UI.
- Skeleton не изображает вымышленные data points. Reduced motion не скрывает финальное значение.

## Достаточность данных

- Канонический UI-паттерн — shared `DataConfidence` из
  `frontend/src/shared/ui/DataConfidence.tsx`. Локальные badges, status colors и расшифровка
  machine-readable `reason_keys` на страницах запрещены.
- Порядок всегда один: plain-language status → конкретные счётчики/период → короткое contextual
  disclosure → optional neutral next step. Фактическая метрика и primary action остаются выше по
  иерархии.
- Neutral surface и левая `3px` lime boundary одинаковы у `sufficient`, `limited`, `insufficient`
  и query-derived stale. Полоса — фирменная геометрия этого типа карточек, а не оценка качества
  данных. Состояния различаются текстом и иконкой, поэтому lime не превращает confidence в score.
- `limited` и `insufficient` не блокируют просмотр фактов. Missing не становится zero, а CTA ведёт
  к безопасному способу дополнить дневник, тренировку или замер.
- Disclosure остаётся inline в том же analytics/decision state, работает без hover и сохраняет
  `44px` touch target. Mobile Web и TMA используют один component tree.

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
- Заголовок post-workout summary остаётся в normal flow и не перекрывает факты, PR или feedback при
  scroll/full-page capture. На mobile его крайние действия имеют безопасные боковые отступы.
- Compact disclosure «Записанные результаты» центрирует label и не получает вертикальный padding
  card-секции. Legend post-workout feedback визуально отделён от первой кнопки минимум одним
  spacing step.

## Nutrition patterns

- Meal list, repeated actions и daily balance строятся alignment/rules, а не nested cards.
- Actual, target, remaining и units остаются одной системой. Превышение ориентира не маскируется
  success color.
- Quick add/Repeat остаются компактными, но доступными. Empty meal объясняет следующий шаг.
- Основное безопасное сохранение Nutrition использует `--v2-lime`/`--v2-on-lime`; выбранный режим
  остаётся нейтральным с lime boundary. Локальный primary нельзя строить только на `--accent`, потому
  что в Design V2 этот compatibility-token может быть намеренно нейтральным.
- Строки истории используют shared `DisclosureIcon` с фиксированной геометрией `28 × 28 px` и
  `flex: 0 0 28px`. Селекторы текстового содержимого `summary` должны адресовать конкретный content
  wrapper (`:first-child` или class), а не каждый прямой `span`, чтобы круг не растягивался в эллипс.

## Недельный контекст и выбор даты

- Канонический недельный блок приложения — shared-компонент `WeekStrip` из
  `frontend/src/shared/ui/WeekStrip.tsx`. Страницы `Сегодня`, `Питание` и будущие surfaces с
  семидневным контекстом переиспользуют его; локальные копии разметки, диапазона дат и CSS-сетки
  не создаются.
- Компонент имеет два смысловых режима. `overview` показывает недельный контекст и доменные
  статусы, а ссылкой делает только день с реальным доступным действием. `picker` выбирает дату,
  сохраняет явную навигацию между неделями и не смешивает выбранную дату с календарным сегодня.
- Любой `overview` с визуальными markers показывает над днями компактную текстовую легенду из того
  же shared component. Символ, форма или цвет не используются без расшифровки.
- В тренировочном контексте тип дня и статус — разные данные: `С` — силовая, `К` — кардио,
  `О` — отдых; отдельно объясняются `✓` выполнено, `•` запланировано, `›` в процессе и `—`
  пропущено. Если в день есть силовая и кардио, показываются оба типа.
- Все пиктограммы типа и статуса внутри `WeekStrip` используют canvas `16×16px` и одинаковую
  bounding geometry в легенде и маркерах дней. Недостаточно выровнять только внешний box:
  `Запланировано` рисуется заполненным кругом диаметром не менее `7px`, `В процессе` — SVG-chevron
  высотой не менее `9px` со stroke не тоньше `2px`, а остальные status glyphs сохраняют сопоставимый
  оптический вес. Семантический tone меняет цвет/surface, но не canvas и геометрию символа.
- На всех ширинах контекст недели остаётся слева в первой grid-колонке, а группа обозначений
  центрируется внутри всей свободной второй колонки — от правого края контекста до правого края
  `WeekStrip`. На compact widths каждая перенесённая строка центрируется в той же колонке и не
  вытесняет дни за границы viewport.
- `Отдых` выводится только после успешной загрузки и силового расписания, и cardio sessions. Ошибка
  или loading одного источника не превращаются в вымышленный день отдыха.
- Другие домены передают свою легенду: например, Nutrition расшифровывает заполненный, неполный,
  отмеченный без приёмов пищи и отсутствующий день, а не использует тренировочную семантику.
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
- **Density:** короткий empty/error/permission state без действия использует compact vertical
  padding; он не должен выглядеть как самостоятельная hero-card. Заголовок следующего account или
  settings section также не получает двойной отступ от parent gap и собственного padding.

## Запрет локальных visual systems

Нельзя вводить экранные цвета, radii, button family, loading/error shell, chart palette или motion,
если существующая semantic роль решает задачу. Новая роль сначала доказывается на нескольких
surfaces и только потом входит в shared Design V2 system.
