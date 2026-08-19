# Design V2: responsive и platform parity

## Принцип

Web, Mobile Web и Telegram Mini App используют одну YFC Design System, одну пару YFC Light/YFC
Dark и общую information architecture. Mobile — отдельная композиция по приоритетам, а не
уменьшенный desktop. TMA отличается platform integration, но не продуктовой темой.

## Desktop composition

- Landing использует controlled asymmetry: promise и factual product proof читаются вместе.
- AppShell сохраняет compact contextual rail и отдаёт основную ширину текущей работе.
- Today имеет одно главное действие и вторичный factual context рядом, а не равноправную сетку KPI.
- Nutrition, Progress и trainer data используют columns, rules и alignment; wide space не заполняется
  декоративными cards.
- Program wizard отделяет решение, причины и preview; exercise detail разделяет media и технику.

## Mobile Web composition

- Порядок определяется задачей: current action → required inputs → status/recovery → secondary
  context.
- Landing показывает promise, primary CTA, factual proof и короткое evidence до длинного narrative.
- Active Workout оптимизирован под одну руку; current set выше дополнительных настроек.
- Nutrition сначала показывает daily balance и затем meals; Progress сначала outcome, затем evidence
  и methodology по запросу.
- Tables превращаются в priority rows или controlled disclosure. Горизонтальный scroll допустим
  только для данных, где сравнение столбцов важнее линейного чтения.
- Touch target — минимум `44 px`; длинные русские labels проверяются на `360 px`.

## Telegram Mini App parity

TMA сохраняет geometry, typography, spacing, hierarchy, controls, states и motion Mobile Web.
Допустимые Telegram-specific различия:

- safe area и viewport, управляемый Telegram;
- Telegram `BackButton`, `MainButton` или haptics, если они не дублируют/ломают YFC action hierarchy;
- источник системной theme preference при сохранении ручного выбора пользователя;
- signed `initData` launch вместо browser `/login` при валидном запуске;
- platform chrome, которое не создаёт второй app header без необходимости.

Недопустимы отдельная TMA palette, другой component family, иная структура данных или скрытые
permissions. Telegram state не является trusted authorization boundary.

## Safe area, keyboard и navigation

- Fixed/sticky controls учитывают `env(safe-area-inset-*)` и не перекрывают system/Telegram chrome.
- При открытой keyboard текущий field, error и primary action остаются достижимыми без ловушки scroll.
- Bottom navigation не перекрывает input и current workout action. Автоматическое скрытие nav требует
  отдельного product behavior decision и не предписывается этой спецификацией.
- Dialog/sheet возвращает focus, корректно блокирует background scroll и учитывает dynamic viewport.
- Orientation и resize не должны терять введённые данные или менять account context.

## Representative breakpoint evidence

Reference prototype проверен на `1440`, `1280`, `768`, `390` и `360 px` в обеих темах. Это evidence
для ключевых composition transitions, а не требование создать пять hard-coded layouts.

Implementation выбирает breakpoints по моменту, когда композиция перестаёт работать:

- wide desktop → compact desktop/tablet;
- rail/two-column → stacked content;
- desktop data comparison → mobile priority flow;
- paired Mobile Web/TMA presentation → один фактический mobile screen.

Промежуточные ширины проверяются вокруг каждого реального transition; horizontal overflow не
маскируется `overflow-x: hidden`.

## Theme и platform verification

Для каждого критического flow проверяются:

- Light, Dark и `Как в системе`, включая сохранение ручного выбора;
- desktop, 768 transition, 390 и 360;
- populated, loading, empty, error, validation, disabled и relevant offline/session state;
- keyboard, visible focus, long labels, large values и missing data;
- safe area, mobile keyboard, bottom navigation и recovery;
- отсутствие разных data semantics между Web и TMA.

Reference screenshots доказывают visual intent, но не заменяют production browser/e2e проверку
real focus order, screen reader semantics, viewport keyboard, Telegram API, CLS и network recovery.
