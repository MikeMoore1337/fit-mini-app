# Design V2: направление Quiet Pace

## Статус документа

Quiet Pace — выбранный владельцем visual baseline Your Fitness Coach. Этот документ и связанные
reference renders фиксируют направление для финального owner checkpoint. Они не разрешают
production pilot сами по себе: изменение production frontend начинается только после отдельного
подтверждения владельцем light/dark/mobile references и запуска task `46G`.

Приоритет источников после утверждения Design V2:

1. фактическое product behavior и ограничения security, privacy, SEO и accessibility;
2. документы `docs/design/*v2*` и renders в `references/design-v2/`;
3. проверенная реализация shared tokens/components после pilot;
4. canonical logo и brand assets task `07`;
5. прежние документы и Landing PNG как historical input.

## Product thesis

Your Fitness Coach помогает человеку понимать, что делать сегодня, выполнять повторяемые действия
без лишнего трения и видеть честную динамику. Визуальный язык должен соединять спокойную уверенность
тренера с точностью рабочего инструмента: **quiet surface, precise data, visible pace**.

Дизайн не обещает «идеальное тело», магический score или автоматическую истину. Он показывает
текущий шаг, факты, методику и ограничения данных.

## Аудитории и ключевые результаты

- Самостоятельный пользователь быстро находит сегодняшнюю тренировку, питание и прогресс.
- Клиент тренера работает с тем же личным контекстом и понимает, что назначено и что выполнено.
- Тренер обрабатывает плотные списки и данные клиентов без отдельной «admin theme».
- Пользователь Mobile Web и Telegram Mini App видит одну и ту же продуктовую систему; платформа
  меняет интеграцию, а не бренд или информационную иерархию.

Критические композиции: Landing → `/login`, AppShell → Today, Active Workout, Nutrition,
Progress/analytics, program selection и exercise detail. Empty, loading, error, validation,
permission, expired session и offline/stale состояния являются частью направления, а не поздним
декором.

## Visual principles

1. **Текущий шаг раньше обзора.** На Today и Active Workout главное действие видно до вторичных
   фактов и настроек.
2. **Факты раньше обещаний.** Landing использует реальные product patterns, а аналитика показывает
   numerator/denominator, даты, единицы и ограничения.
3. **Плотность следует частоте действия.** Workout и Nutrition компактнее Landing и методических
   материалов. Mobile перестраивает порядок, а не уменьшает desktop.
4. **Surface имеет задачу.** Самостоятельный task region может получить фон и границу; список,
   таблица или последовательность чаще строятся alignment и rules.
5. **Lime показывает смысл.** Один ключевой primary action в локальном контексте получает lime fill;
   lime также отмечает progress endpoint, focus и подтверждённый status/sync, но не окрашивает всё
   интерактивное.
6. **Одна система на двух темах и платформах.** Light и Dark равноправны; TMA не получает отдельную
   палитру или component family.

## Что означает premium

Premium для YFC — это точная типографика, дисциплина интервалов, ясная иерархия, ограниченная
палитра, качественные числа и надёжные recovery states. Это не чёрный фон сам по себе и не набор
glow, glass, blur, огромных радиусов или декоративной анимации.

Интерфейс должен выдерживать длинные русские labels и реальные данные без ощущения template UI.
Landing может иметь более спокойные поля и controlled asymmetry; рабочие surfaces сохраняют
среднюю или высокую плотность.

## Правила узнаваемости

- Canonical Y/C/barbell mark и protected textual wordmark `YOUR FITNESS COACH` обязательны на
  Landing, `/login`, desktop AppShell, public shell и reference boards.
- Mark-only допустим в favicon, app icon, compact mobile navigation, loading mark и Telegram header,
  если имя приложения уже видно рядом.
- Характер YFC поддерживают current set, rest state, `текущий / всего`, workout notation,
  explainable program result и lime endpoint.
- Desktop contextual rail остаётся лёгким навигационным контекстом, а не тяжёлой admin sidebar.
- Typography остаётся humanist system sans с уверенным medium/strong rhythm и tabular numerals.

На pilot canonical implementation contract для lockup — shared component `canonical mark + protected
textual wordmark`. Создавать новые варианты SVG-логотипа или независимо набирать wordmark в каждом
экране нельзя. Изменение geometry самого знака task `07` не входит в Design V2.

## Approved и forbidden patterns

Утверждены:

- neutral-white Light и neutral near-black Dark;
- theme-native surfaces без инверсии крупных content cards;
- controlled asymmetry и разный rhythm Landing, data screens и mobile action flow;
- один lime primary CTA в локальном decision context; provider choices, navigation, secondary,
  recovery и destructive actions остаются семантически нейтральными или статусными;
- компактные rules/alignment для Nutrition, Progress и списков;
- спокойные borders, редкие shadows и небольшая control geometry;
- factual product crops без обязательного laptop/phone mockup.

Запрещены как default:

- green-black Dark и warm-paper Light из exploration;
- glow, glassmorphism, blobs, sparkles и декоративные gradients;
- card-inside-card, bento по умолчанию и одинаковые KPI cards;
- pill geometry для обычных buttons/navigation;
- synthetic fitness people, fake testimonials, ratings, metrics, prices или AI promises;
- generic `icon → title → text` сетки и одинаковый section rhythm;
- скрытие ограничений данных, ошибок или recovery ради «чистого» screenshot.

## Роль изображений и product proof

Главное изображение YFC — сам фактический продукт: текущая тренировка, дневник, динамика и объяснение
рекомендации. Crop обязан сохранять читаемые labels, units и state, иметь reserved dimensions и не
создавать CLS. Exercise media может быть только собственным или лицензированным; auto-play и
декоративные stock/AI people не являются частью направления.

## Decision table по owner feedback

| Статус | Решение |
|---|---|
| Принято | A / Quiet Pace, compact rail, tabular numerals, neutral Light, near-black Dark, theme-native surfaces и один lime primary CTA в локальном контексте |
| Изменено | Неопределённый full-logo контракт сведён к shared lockup из canonical mark task `07` и protected textual wordmark; после production pilot Dark neutral surfaces немного осветлены, success приведён к lime family, active navigation усилена neutral surface, а exercises получили самостоятельные boundaries |
| Отклонено | B и C как production themes, green-black Dark, warm-paper Light, inverted content cards, serif/italic и pill buttons |
| Требует реализации позже | Shared tokens/components, production motion, реальный focus order, screen-reader и keyboard/safe-area проверка в pilot |
| Невозможно без product behavior | Автоматически скрывать navigation во время workout или добавлять новые statuses/metrics; такие решения не входят в визуальную спецификацию |

Отклонений от явного owner feedback нет. Изменение lockup — не новый знак, а единый способ применять
уже сохранённый canonical logo без расхождения между surfaces.

## Human-made tests

- **Brand Swap:** без workout notation, current-set rhythm, lime endpoint и YFC lockup направление
  заметно теряет характер.
- **Screenshot:** Landing, Workout, Nutrition и Progress используют разную плотность и композицию,
  а не один dashboard template.
- **Card:** контейнер остаётся только там, где задаёт task/entity context; dense data организованы
  rules и alignment.
- **Decoration:** заметный элемент обязан поддерживать бренд, иерархию, данные или действие.
- **Designer Intent:** scale, spacing, radius, color и motion должны быть объяснимы частотой действия,
  читаемостью или системной ролью.
- **Rhythm:** спокойный Landing, компактный working app и one-hand mobile flow не схлопываются в
  одинаковую последовательность блоков.

## Legacy transition

`codex-backlog/references/landing/landing-reference-dark.png` и
`landing-reference-light.png` остаются historical input. Они не задают hero, card layout,
testimonials, product imagery, section order или rhythm. Lime + neutral palette сохраняются только
в контракте Design V2. Старые визуальные указания tasks `01`, `05` и historical masters не
переопределяют этот документ. Canonical logo task `07` сохраняется без изменений.
