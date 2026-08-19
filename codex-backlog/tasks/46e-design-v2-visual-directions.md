# TASK 46E. Design V2 - три визуальных направления и рендеры

- Фаза: **Design V2 exploration**
- Приоритет: **46E/93 - owner checkpoint**
- Зависит от: `46D`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-discovery`, `$product-designer`, `$ui-audit`; `$frontend-engineer` только для изолированных render prototypes

## Цель

На основе аудита `46D` подготовить три действительно разных профессиональных visual directions для единого бренда Your Fitness Coach:

- public Landing;
- Web-приложение;
- Mobile Web;
- Telegram Mini App как та же mobile-композиция с platform adaptation.

Сначала показать владельцу рендеры и получить выбор. Production frontend на этом этапе не менять.

## Критические ограничения

- Запрещено изменять production frontend, routes, shared components, tokens, styles и assets.
- Запрещено начинать rollout или «заодно улучшать» текущие экраны.
- Все prototypes/renders хранить только в `.artifacts/`.
- Не создавать отдельный визуальный язык для TMA.
- Не копировать Apple, Linear, Stripe, Whoop, Oura, Fitness Online или другой продукт.
- Не делать три варианта, отличающиеся только цветом, radius или font weight.
- Не генерировать fake testimonials, fake ratings, fake metrics, цены, тарифы и несуществующие функции.
- Не выдавать концептуальный UI за уже реализованный product behavior.

## Обязательные входные данные

Использовать:

- `46D` audit и `design-v2-brief.md`;
- фактические product flows и data density;
- canonical logo task `07`;
- действующие light/dark theme requirements;
- `DESIGN_V2_INTEGRATION_NOTES.md`;
- старые Landing PNG только как legacy color/input reference;
- реальные screenshot/content patterns приложения.

## Базовые требования ко всем направлениям

Каждое направление должно быть:

- современным;
- human-made, а не generic AI SaaS;
- визуально дорогим без демонстративной роскоши;
- restrained + precise + confident;
- узнаваемым как Your Fitness Coach;
- функциональным для плотных fitness/nutrition данных;
- одинаково убедительным в light и dark;
- пригодным для desktop и mobile;
- доступным и реалистично реализуемым в текущем стеке;
- совместимым с SEO/performance constraints Landing;
- совместимым с реальной информационной архитектурой продукта.

Lime и graphite/neutral палитру разрешено сохранить и развить. Lime должен использоваться осмысленно как брендовый сигнал, primary action, selected/progress/success accent, а не механически на каждой иконке и границе.

## Три направления

Предложить три визуальные системы с существенно разными:

- art direction;
- typography/composition;
- density;
- surface model;
- navigation treatment;
- data visualization language;
- imagery/product presentation;
- rhythm and scale;
- motion principles.

Допустимые отправные идеи, но не обязательные названия:

1. **Refined Performance** - точный, спортивный, технологичный, data-led.
2. **Premium Minimal** - спокойный, строгий, типографичный, с минимальным visual noise.
3. **Editorial Product System** - более выразительная композиция и storytelling без рекламного шаблона.

Если после аудита подходят другие направления, использовать их, но объяснить различия.

## Анти-AI требования

Не использовать по умолчанию:

- фиолетово-синие градиенты;
- glow/neon;
- glassmorphism;
- bento grid только ради моды;
- одинаковые rounded cards во всех секциях;
- cards inside cards;
- pill UI everywhere;
- icon-in-circle + title + paragraph для каждой функции;
- гигантский пустой hero;
- floating blobs/sparkles;
- centered heading перед каждой одинаковой секцией;
- synthetic fitness people как основной визуальный материал;
- generic laptop/phone composition без продуктовой причины;
- пять звёзд и вымышленные отзывы;
- чрезмерные shadows/radii;
- одинаковую композицию каждого экрана.

Нужны controlled asymmetry, visual rhythm, variation of scale/density и ясные focal points, если это уместно конкретному направлению.

## Обязательные representative surfaces

Для каждого visual direction подготовить не только moodboard, но и применённый дизайн минимум к следующим surfaces:

1. Landing hero + минимум две разные storytelling sections.
2. `/login` или auth entry.
3. AppShell + Today desktop.
4. Active Workout mobile.
5. Nutrition diary с плотными данными.
6. Progress/analytics.
7. Programs или program-selection wizard.
8. Representative Mobile Web/TMA screen.

Достаточно объединять несколько surfaces в один presentation board, но каждый пункт должен быть читаемо показан.

Минимум для каждой концепции:

- desktop light;
- desktop dark;
- mobile light или dark;
- ключевые interaction/state examples;
- typography/colors/spacing/surface summary.

## Способ создания рендеров

Предпочтительный воспроизводимый вариант:

1. создать изолированные static HTML/CSS prototypes в `.artifacts/design-v2/exploration/<direction>/`;
2. использовать реальные тексты, значения и структуры продукта без подключения production APIs;
3. открыть prototypes через доступный Playwright/browser tooling;
4. снять PNG/WebP renders на representative viewports;
5. не добавлять prototype dependencies в production package;
6. не коммитить `.artifacts/`.

Если доступен Figma или другой согласованный canvas, его можно использовать дополнительно, но итоговые renders и rationale всё равно сохранить локально. Не зависеть от возможности генерации изображений.

## Результат по каждому направлению

Подготовить:

- краткую visual thesis;
- что делает направление узнаваемым;
- typography direction;
- palette и роль lime;
- grid/spacing/density;
- cards/surfaces/radii;
- charts/data visualization;
- imagery/product screenshot treatment;
- motion principles;
- desktop/mobile composition;
- strengths;
- trade-offs/implementation risks;
- Brand Swap Test result;
- почему это не generic AI UI.

## Сравнение

Сделать итоговую матрицу по критериям:

- соответствие аудиториям;
- premium perception;
- product clarity;
- brand distinctiveness;
- information density;
- mobile/TMA suitability;
- accessibility;
- implementation risk;
- performance risk;
- longevity.

Дать одну профессиональную рекомендацию, но не выбирать за владельца.

## Артефакты

Сохранить в:

`.artifacts/design-v2/exploration/`

Рекомендуемая структура:

```text
.artifacts/design-v2/exploration/
├── direction-a/
├── direction-b/
├── direction-c/
├── comparison.md
├── recommendation.md
└── index.md
```

## STOP CONDITION

После предоставления трёх направлений обязательно остановиться.

Не выбирать направление автоматически.
Не изменять tracked production files.
Не создавать design system в `docs/`.
Не переходить к task `46F`.
Не создавать commit.

Владелец должен явно:

- выбрать направление;
- отклонить все направления; или
- указать, какие элементы объединить и что исправить.

## Done when

- представлены три существенно разных направления;
- каждое показано на реальных representative surfaces;
- light/dark/mobile не сведены к простому recolor/resize;
- старые Landing references не воспроизведены как шаблон;
- преимущества и ограничения честно описаны;
- production code и tracked files не изменены;
- владелец получил достаточные материалы для осознанного выбора.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Использовать реальный browser render, а не только текстовое описание. В финальном сообщении дать ссылки/пути на boards/renders, краткое сравнение и рекомендацию, затем остановиться.
