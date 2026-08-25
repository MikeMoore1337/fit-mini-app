# Design V2.1 — контракт Landing и `/login`

## Визуальная целостность

Landing и `/login` используют один canonical logo, Inter/system sans, semantic Light/Dark
токены V2, controls с радиусом `12px`, lime focus/primary action и плоские
окантованные регионы. Целостность не означает повтор композиции Landing внутри auth flow.

Двухплоскостная композиция `/login` не импортирует colors из Direction A. Обе
плоскости сопоставлены production-контракту Design V2: Light canvas/surface/lime
`#F4F5F2 / #FFFFFF / #9EE02B`, Dark `#101310 / #161916 / #A8E83A`. Текст, border и semantic
error states берут theme tokens из `frontend/src/styles/design-system.css`.

## Landing — выбранный Quiet Pace

### Информационная архитектура

1. Header: canonical lockup, фактическая navigation, `Войти`.
2. Hero: один H1 (`Знайте, что делать сегодня.`), краткое фактическое объяснение,
   primary CTA `Открыть приложение` и optional secondary explanation.
3. Фактический product proof: текущая тренировка с весом, повторами и отдыхом; fixture не
   выдаётся за marketing fact.
4. Раздел с одним primary action: Today как следующий шаг, а не notification feed.
5. Честный раздел progress/evidence с ограничениями.
6. Только реальные high-signal capabilities.
7. Product workflow и продолжение в Web/TMA.
8. Раздельная ценность для самостоятельного пользователя и тренера.
9. Фактический contact/final CTA и сдержанный footer.

Запрещены fake metrics, testimonials, prices, trial, AI, wearables, social, marketplace и
недоступные features. Текст остаётся crawlable HTML; на странице один H1, headings
сохраняют semantic order.

### Desktop-композиция

- На `1440/1280/1024` используется editorial rhythm с двухколоночным hero, если размеры tracks
  это позволяют.
- Product proof — читаемые данные, а не decorative dashboard mock.
- Геометрия следует смыслу раздела: rules, split narrative, evidence region и audience planes вместо
  повторяющихся сеток из трёх cards.
- На `768` copy предшествует proof, а proof занимает всю ширину; header menu остаётся доступным
  для keyboard/touch.

### Mobile-композиция

- На `430/390/360`: promise → primary CTA → читаемый proof текущей тренировки; затем secondary narrative.
- Нет transform/scale для desktop proof, clipping через negative margin и overlapping floating cards.
- Первая последовательность объясняет продукт, следующее действие и первое доказательство
  без пустого hero в несколько экранов.
- Mobile menu закрывается после route selection, `Escape` или outside action, возвращает focus и имеет
  строки `>=44px`.
- Light/Dark используют соответствующие product render/theme.

### Motion и assets Landing

- Разрешены только transitions для header/menu, buttons и disclosures; CSS-first и
  `prefers-reduced-motion` safe.
- Для product proof зарезервирована геометрия; hero content не ждёт JavaScript animation.
- Raster evidence ниже fold получает responsive derivative и lazy loading без новой dependency.
- Header action `Войти` является primary conversion action Landing и использует lime fill с
  `on-lime` текстом в Light и Dark; theme/menu controls остаются нейтральными.
- Platform context `Web и Telegram Mini App` находится рядом с primary CTA, а neutral demo CTA
  открывает production demo-cabinet с явными `cabinet`, `scenario` и `section`, не legacy demo.
- Строки demo-сценариев используют одинаковый горизонтальный inset; privacy section не продолжает
  нижнюю линию поверх собственной скруглённой границы финального CTA-блока.
- Workflow использует одну section boundary, одинаковый внутренний padding шагов, открытые внешние
  края и только внутренние разделители. Парные audience CTA используют lime-primary в Light и Dark.
- Platform boundary замкнута со всех сторон; lime остаётся direction marker слева. Footer privacy
  ведёт в публичный содержательный раздел до авторизации, а операции с конкретным аккаунтом
  объясняются как доступные после входа.
- Описания в парных audience surfaces `Занимаетесь самостоятельно?` и `Вы тренер?` используют
  одинаковый `text-primary`: различие сценариев задаётся композицией и lime-маркером, а не снижением
  контраста одного из текстов.

## `/login` — выбранные A surfaces и V2 type

### Desktop

- Split `1.04fr/.96fr`: слева continuation plane, справа auth plane.
- Desktop-сцена использует тот же container, что и landing: `min(1180px, calc(100% - 48px))`.
  На широких viewport, включая `2K`, полноэкранные фоновые плоскости сохраняются, но контент не
  растягивается и не прижимается к внешним краям; граница фоновых плоскостей продолжает совпадать
  с границей tracks центрированной сцены.
- Левая плоскость использует более сильный V2 dark/surface contrast из approved board; правая остаётся
  спокойной theme-native plane. В Dark их semantic relationship не инвертируется механически.
- Continuation group центрирована по вертикали. `Вернитесь к своему плану.` — `35px`, одна строка
  и не менее `22px` inline clearance. Supporting copy не обещает автоматическое слияние accounts.
- Auth stack центрирован по обеим осям. Eyebrow/title/context/provider выровнены по provider track
  `300px`; полные provider labels остаются на одной строке, а error/helper могут занимать до
  `360px` для читаемого recovery.
- Четыре provider actions остаются вертикальным stack. Лишние header/home/theme controls для
  V2.1 исключены.
- В continuation plane логотип выбирается по локальной тёмной поверхности (`dark` asset), а не по
  глобальной Light/Dark теме страницы.

### Tablet/mobile

- На `<1024` split становится одной document column. Mobile title — `Войти и продолжить`;
  continuation context остаётся фактическим и не занимает отдельный viewport.
- Mobile header показывает полный lockup `YOUR FITNESS COACH` без дублирующей кнопки `Войти`:
  пользователь уже находится на экране входа.
- Provider actions занимают всю ширину, их высота `>=48px`, а внешний gutter — не менее `16px`.
- Loading и error остаются in-flow. Light loading и Dark error в approved board — только representative
  states: оба состояния обязаны работать в обеих темах.
- При открытой keyboard active control/error/action остаются видимыми, content может scroll.

### Providers и OAuth return

- Providers: Telegram, Google, Яндекс, VK ID — ровно по runtime configuration.
- Каждый внешний provider action показывает узнаваемый фирменный знак в официальной палитре;
  знак остаётся видимым на desktop/mobile и в Light/Dark. Нельзя заменять его общей пиктограммой,
  первой буквой, emoji или скрывать ради более нейтрального списка.
- Provider color ограничен компактным icon carrier; сама action сохраняет theme-native YFC surface,
  читаемый текст и lime direction marker. Иконка декоративна, а доступное имя задаёт полный label.
- Нажатие provider блокирует duplicate submit и сохраняет allowlisted return context.
- Cancellation возвращает focus на исходный provider.
- Provider unavailable, invalid state и conflict объясняют безопасное recovery без silent identity merge.
- OAuth success ведёт по validated internal path; external/open redirect запрещён.
- Valid TMA launch пропускает browser provider stack и входит в platform auth loading/error.

## Финальные evidence и ограничения

- Frozen renders покрывают Landing desktop/mobile Light/Dark и `/login` desktop/mobile Light/Dark с
  loading/error representation.
- Static boards подтверждают только composition, typography и hierarchy. Keyboard, focus order, OAuth
  return, provider configuration, TMA auth и responsive overflow проверяются runtime-тестами.
