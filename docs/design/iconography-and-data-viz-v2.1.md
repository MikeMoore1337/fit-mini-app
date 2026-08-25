# Иконографика и визуализация данных Design V2.1

## Статус решения

Этот документ расширяет активный `DESIGN_V2_1 Quiet Pace`. Владелец выбрал единую compact/mobile
геометрию графиков v2 и гибридный набор пиктограмм v1/v2. Логотип YFC и официальные provider marks
не входят в эту систему и не перерисовываются.

## Иконографика

- Канонический renderer: `frontend/src/shared/ui/Icon.tsx`.
- Сетка: `24×24`; поддерживаемые optical sizes: `16`, `20`, `24`.
- Все функциональные glyphs используют `currentColor`, round cap/join и общий stroke `1.8`.
- Базовые actions, navigation, confidence, statuses, product и `WeekStrip` имеют уникальные
  семантические имена. Одинаковая семантика не получает page-local SVG, Unicode или CSS substitute.
- `nav-exercise-catalog` использует выбранный владельцем разреженный силуэт открытой папки с одной
  гантелью: внешний контур означает каталог, внутренний — упражнения; повторяющаяся grid-геометрия
  не используется.
- `AppNavigationIcon`, `CloseIcon`, `TrashIcon`, `ChevronIcon`, `CheckIcon`, `DisclosureIcon`,
  `ThemeIcon`, `DataConfidence` и `WeekStrip` являются адаптерами над тем же renderer.
- Icon-only action всегда получает accessible name от control и touch target не меньше `44px`.
  Декоративная иконка скрыта от accessibility tree; самостоятельная смысловая иконка передаёт
  `label`.
- Active state использует neutral surface, усиленный label и lime boundary. Цвет не заменяет форму
  или подпись.
- YFC brand assets и Google/Yandex/Telegram/VK/Apple marks остаются защищёнными исключениями.

## `WeekStrip`

Тип активности и статус дня — разные glyphs. `strength`, `cardio` и `rest` больше не кодируются
буквами. `completed`, `planned`, `in-progress`, `skipped`, `nutrition-incomplete`,
`nutrition-fasted` и `nutrition-missing` имеют разные формы на одном optical canvas. Легенда и
полный accessible name сохраняются, поэтому состояние не зависит от цвета.

## Shared data-viz primitives

Канонический слой: `frontend/src/shared/ui/DataViz.tsx`.

- `TimeSeriesChart` — Nutrition, масса/антропометрия и print/PDF;
- `QuantitativeProgress` — числовой прогресс к цели;
- `TaskProgress` — выполненные элементы конечной задачи;
- `StepProgress` — этапы workflow, но не количественная цель;
- `RankedBars` — ранжированное сравнение на общей видимой шкале.

Нельзя называть `7 420 / 10 000 шагов` workflow step progress: это quantitative target.

## Правдивость данных

- `missing` остаётся отсутствием: точка не рисуется и соседние подтверждённые точки через такой
  интервал не соединяются.
- Подтверждённый `0` остаётся видимой нулевой точкой.
- Target имеет dashed geometry; actual — solid line и ring marker; смена target получает отдельную
  вертикальную метку и подпись.
- X-position использует реальные даты, а не порядковый номер точки.
- Y-scale строится по подтверждённым actual/target значениям. Нулевая baseline включается только
  для метрик, где она помогает чтению, например калорий.
- Одна точка остаётся одной точкой; insufficient/empty/error/stale не получают fake series.
- Business formulas, API aggregates и provenance не меняются визуальным слоем.

## Responsive и interaction

Mobile Web и mocked TMA используют compact v2 composition: короткая legend, минимум три X-label и
adjacent selected detail. Desktop использует тот же язык, но получает больше фактической ширины —
не отдельную v1-систему и не растянутый mobile SVG.

Точки выбираются touch/click, focus и стрелками клавиатуры. Важное значение всегда дублируется
рядом с графиком и не требует hover. `prefers-reduced-motion` отключает transition, а
`forced-colors` сохраняет solid/dashed/marker различия.

## Text/table и print

Каждый `TimeSeriesChart` содержит таблицу тех же подтверждённых данных. На экране она доступна
assistive technology, а в print/PDF становится видимой. Print использует grayscale-safe solid,
dashed и ring geometry и не зависит от tooltip или выбранного interactive state.

## Запреты

- Не добавлять generic chart dependency без отдельной доказанной необходимости.
- Не вставлять reference SVG графиков из design package: в них текст переведён в outlines.
- Не создавать page-local `line/polyline/circle` chart grammar или новый CSS progress meter.
- Не использовать emoji, Unicode arrows/stars/plus/minus и CSS-generated functional glyphs.
