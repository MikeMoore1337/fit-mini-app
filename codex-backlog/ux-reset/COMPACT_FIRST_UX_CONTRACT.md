# Compact-first UX contract - progressive disclosure across YFC

Этот contract обязателен для нового UX-reset и должен стать долговечным правилом YFC. Его цель - убрать ощущение «полотна», снизить визуальную и когнитивную нагрузку и при этом **не удалять полезную функциональность**.

## Базовый принцип

По умолчанию показывать только то, что нужно пользователю для текущего решения или действия.

- **Primary action/current operation** - всегда видимы и не прячутся за disclosure.
- **Secondary/detail/advanced information** - compact/collapsed по умолчанию, если без неё можно выполнить текущую задачу.
- **Большой самостоятельный detail flow** - отдельный screen/sheet/detail route вместо бесконечно раскрывающейся карточки.
- Compact-first не означает «скрыть всё». Если пользователь постоянно обязан раскрывать секцию для базового действия, это неправильный disclosure.

Целевой паттерн:

```text
выразительный compact summary/action card
                  ↓ tap
спокойный functional detail content
```

## Decision rule для каждой секции

Перед реализацией любого always-open блока ответить:

1. Нужен ли его контент для primary action **прямо сейчас**?
2. Нужны ли эти данные для сравнения сразу с соседними данными?
3. Требует ли пользователь редактировать их постоянно в текущем flow?

Если ответ «нет» - предпочитать collapsed summary, contextual disclosure либо detail screen.

### Always visible

Оставлять открытыми:

- текущий primary CTA;
- inputs/controls активной операции;
- критичный status/error/validation feedback;
- данные, без которых невозможно осмысленно завершить текущий шаг;
- текущий workout logging row/таймер/`Готово`, когда пользователь уже выполняет упражнение.

### Collapsed/compact by default

Обычно сворачивать:

- дополнительные параметры;
- историю и подробную статистику;
- справочные пояснения;
- schedule/settings detail;
- power-user controls;
- вторичные summaries;
- optional wellbeing/reminder blocks, когда они не требуют действия.

### Отдельный detail screen вместо accordion

Предпочитать отдельный экран/sheet, если после раскрытия появляется:

- длинная форма;
- много самостоятельных действий;
- большой график/history/list;
- несколько внутренних подразделов;
- контент, который сам становится полноценным пользовательским flow.

## Ограничения disclosure

- Не делать `accordion -> accordion -> accordion`.
- Максимум один явный уровень expandable content внутри конкретной summary card. Если нужен следующий уровень - использовать detail screen/sheet.
- Не прятать validation/error state так, чтобы пользователь не понимал, почему действие не выполняется.
- Не схлопывать секцию автоматически посреди ввода/редактирования.
- Не добавлять server-side persistence expanded/collapsed state без продуктовой необходимости.
- Не использовать disclosure как способ спрятать плохую IA.

## Compact card contract

Collapsed card должна позволять быстро понять содержание без раскрытия. Где применимо, она содержит:

- короткий title;
- 1 ключевой status/metric/summary;
- максимум один очевидный quick action, если он действительно нужен;
- понятный disclosure affordance (`chevron`, label или весь корректно размеченный header);
- semantic visual family из Task 123.

Не заполнять compact card декоративными подписями ради плотности.

## Visual wow и compactness

Compact-first - не повод сделать интерфейс стерильным. Наоборот, collapsed summary/action cards - основной носитель premium sport-tech характера:

- semantic gradient/pattern;
- iconography;
- progress/metric visualization;
- subtle status treatment;
- короткий purposeful motion/transition;
- корректные light/dark variants.

Expanded/detail content должен быть спокойнее, чтобы inputs, таблицы, списки и logging оставались читаемыми.

Не делать каждую карточку уникальной по цвету. Использовать semantic families: `training`, `nutrition`, `progress`, `wellbeing`, `neutral/system`.

## Mobile/TMA compactness

Mobile Web и TMA - primary constraint.

На representative initial state пользователь должен без длинной прокрутки увидеть:

- где он находится;
- primary action/current status;
- несколько наиболее важных summary/action surfaces.

Не вводить искусственный универсальный pixel/scroll threshold: content различается. Вместо этого проверять, что vertical scroll создаётся **полезным контентом**, а не постоянно раскрытыми вторичными секциями.

Desktop не должен становиться просто широким длинным полотном: использовать reflow/columns/bento только когда это улучшает hierarchy и scanability.

## Interaction и accessibility

Для expandable controls:

- semantic button/control;
- `aria-expanded` + связь с controlled content, где применимо;
- keyboard activation/focus;
- touch target соответствует mobile contract;
- screen reader понимает collapsed/expanded state;
- при раскрытии не теряется focus и не происходит неожиданный scroll jump;
- motion учитывает `prefers-reduced-motion`;
- transitions не блокируют interaction.

## Применение по основным разделам

### Сегодня

Compact action/summary cards вместо длинной ленты подробностей. Primary workout/action видим сразу. Nutrition/Hydration/Wellbeing - компактно и только по релевантности.

### Программа тренировок

Программа/дни/тренировки представлены компактными summaries. Создание программы показывает базовый action layer, advanced settings раскрываются по требованию.

### Активная тренировка

Текущие logging controls остаются открытыми. Technique/history/notes/RIR/set type/alternatives и прочие вторичные данные - contextual/collapsible/detail.

### Питание

Day summary и быстрые действия компактны. Приёмы пищи/detail/history/reports не должны одновременно разворачивать страницу без необходимости. Food search/list rows остаются функциональными и спокойными.

### Прогресс

Summary/bento отвечает на «что изменилось». Подробные графики, periods/history/detail открываются по intent. Missing data != zero.

### Профиль

Основные разделы - компактные section cards/rows. Schedule, Notification Center и другие большие вторичные блоки - disclosure/detail, а не permanently expanded полотна.

## Future task placements

- **81 Hydration:** compact Today quick action/summary; detail/history в Nutrition.
- **82 Sleep/Mood:** compact optional check-in; history/insights в Progress.
- **84 Reminders:** compact configuration summaries в Profile/Notifications; Today только actionable state.
- **111 Progress bento:** компактные meaningful summaries; detail charts/history по раскрытию/detail screen; не bento ради каждого числа.

## Anti-patterns

Запрещены без явного обоснования:

- десятки always-expanded cards подряд;
- карточка, которая после раскрытия содержит несколько новых accordion levels;
- скрытый primary CTA;
- раскрытие секции только чтобы увидеть единственное базовое действие;
- длинные стены helper text;
- большое количество одинаково акцентных cards;
- превращение compactness в icon-only mystery UI;
- удаление функции только ради уменьшения высоты страницы.

## Release/QA contract

UI task не считается выполненной только потому, что все функции помещены на экран. Для representative Mobile/TMA/Desktop states проверить:

- primary action легко находится;
- secondary sections не создают необязательное «полотно»;
- collapsed summary понятен без раскрытия;
- важные details находятся предсказуемо;
- disclosure работает touch/keyboard/screen reader;
- expanded state не ломает layout/keyboard/safe-area;
- нет nested-disclosure trap;
- semantic wow сосредоточен на meaningful compact surfaces, а functional detail остаётся читаемым.
