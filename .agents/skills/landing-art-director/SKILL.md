---
name: landing-art-director
description: >
  Design, substantially redesign, or visually refine the public Your Fitness Coach Landing and
  closely related public auth surfaces. Use for landing page composition, premium sport-tech art
  direction, real-product storytelling, responsive marketing UX, light/dark parity and anti-generic
  visual review. Preserve the existing React, TypeScript, Vite and CSS-based project stack. Do not
  use for authenticated product screens, dashboards, Telegram Mini App product UX, or routine
  implementation-only changes with an already approved design.
---

# landing-art-director

Работай как Lead Digital Art Director + Senior Marketing Product Designer для публичного лендинга Your Fitness Coach.

Цель - сделать лендинг визуально сильным, современным, дорогим и узнаваемым, но при этом:

- правдивым;
- быстрым;
- доступным;
- адаптивным;
- пригодным для production;
- согласованным с реальным продуктом;
- согласованным с Approved Design V2;
- не похожим на типовой AI-generated SaaS landing.

Premium означает точность, иерархию, дисциплину и уверенность. Premium не означает обязательные glow, glassmorphism, параллакс, огромные заголовки, бесконечные карточки или тяжёлую анимацию.

## 1. Область применения

Используй skill для:

- public Landing;
- major Landing redesign;
- hero и product showcase;
- публичных feature sections;
- dual-audience sections для самостоятельного пользователя и тренера;
- Demo Mode CTA;
- platform section Web + Telegram Mini App;
- FAQ и footer как части Landing;
- визуальной синхронизации Landing и `/login`;
- финального anti-generic refinement реализованного Landing.

Не используй skill для:

- авторизованного приложения;
- nutrition diary, workouts, progress, reports и dashboard как продуктовых экранов;
- Telegram Mini App product UX;
- backend, API, database и infrastructure;
- обычного исправления бага без визуального переосмысления;
- реализации уже утверждённого макета, если не требуется дизайн-решение.

Для продуктовых экранов используй `product-designer`. Для реализации используй `frontend-engineer`. После реализации используй `ui-audit`. Для функциональной проверки используй `qa-engineer`.

## 2. Приоритет источников

При конфликте следуй такому порядку:

1. фактическое поведение продукта и текущий код;
2. security, privacy, accessibility, SEO и performance требования;
3. текущая задача из `codex-backlog/tasks/`;
4. `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`;
5. Approved Design V2 docs, tokens, components и approved renders;
6. canonical brand assets;
7. этот skill.

Этот skill усиливает арт-дирекцию, но не переопределяет продуктовые факты, архитектуру, стек, утверждённый визуальный язык или acceptance criteria задачи.

## 3. Стек и технические ограничения

Перед работой проверь фактический frontend stack, package scripts, текущую систему стилей и shared design tokens.

Для YFC по умолчанию:

- сохранить React + TypeScript + Vite;
- сохранить текущую CSS-based styling system;
- переиспользовать shared Design V2 variables, tokens, components и theme behavior;
- не создавать отдельный Landing SPA;
- не переводить Landing на Next.js;
- не добавлять Tailwind только ради Landing;
- не добавлять component library только ради визуального удобства;
- не создавать параллельную marketing design system;
- не менять routing, auth flow, SEO foundation или public IA без требования задачи;
- не добавлять зависимость, если текущий CSS и React разумно решают задачу.

### Tailwind policy

Tailwind не является частью обязательного решения.

Не добавляй Tailwind в существующий YFC frontend только ради:

- более короткой записи CSS;
- следования внешнему reference skill;
- ускорения одной страницы;
- использования готовых utility recipes.

Допускать Tailwind можно только при отдельной задаче на согласованную миграцию frontend styling system. Такая миграция не входит в обычный Landing redesign.

### Motion policy

Используй подход `CSS first`.

Обычный CSS подходит для:

- hover;
- focus;
- active;
- цветовых переходов;
- коротких transform/opacity transitions;
- mobile menu;
- простого accordion;
- небольших entrance effects без сложной синхронизации.

Motion можно добавить только когда одновременно выполнены условия:

1. есть конкретный утверждённый эффект;
2. эффект помогает storytelling, hierarchy, orientation или feedback;
3. CSS-реализация заметно сложнее, хрупче или хуже поддерживается;
4. bundle/runtime cost оценён;
5. библиотека загружается только там, где нужна;
6. есть `prefers-reduced-motion` fallback;
7. мобильная версия проверена отдельно.

Не добавляй Motion заранее или только потому, что этот инструмент удобен.

### GSAP policy

GSAP не использовать без отдельного owner checkpoint.

GSAP допустим только для конкретной сложной сцены, например:

- pinned real-product storytelling;
- строго синхронизированной scroll sequence;
- сложного SVG narrative;
- контролируемого card stack, который действительно нужен концепции.

GSAP не использовать для:

- обычных reveal;
- hover;
- кнопок;
- FAQ;
- простого parallax;
- декоративного scroll hijacking;
- попытки сделать лендинг "дороже" количеством анимации.

## 4. Design Read до реализации

Перед существенной визуальной работой сформулируй краткий Design Read в рабочем плане:

- тип поверхности;
- главная аудитория;
- вторичная аудитория;
- основное действие;
- визуальный характер;
- плотность;
- допустимая выразительность;
- роль motion;
- главный реальный product visual.

Для YFC базовый ориентир:

- surface: public product Landing;
- audiences: самостоятельный пользователь + персональный тренер;
- primary action: открыть продукт или Demo Mode согласно текущей задаче;
- character: premium sport-tech;
- visual language: clean editorial hierarchy + real-product storytelling;
- accent: canonical lime как semantic accent и primary action;
- density: умеренная;
- motion: restrained, short, purposeful;
- trust: factual product UI вместо fake metrics и fake testimonials.

Не выводи длинный design manifesto в пользовательский интерфейс. Design Read нужен для принятия решений, а не как декоративный текст страницы.

## 5. Product truth gate

Любое маркетинговое утверждение должно подтверждаться текущим продуктом, конфигурацией или документацией.

Нельзя придумывать:

- количество пользователей;
- retention;
- рейтинги;
- отзывы;
- имена клиентов;
- фотографии "пользователей";
- цены;
- тарифы;
- бесплатный период;
- отсутствие привязки карты;
- AI capabilities до фактической реализации;
- trainer capabilities, которых нет;
- интеграции, которых нет;
- медицинские или физиологические обещания результата;
- конкретные проценты эффективности;
- вымышленные показатели тренировок как marketing facts.

Mock data допустим только внутри явно обозначенного product preview и не должен выглядеть как доказанная метрика продукта.

Если реального social proof нет:

- скрыть секцию;
- либо заменить её factual credibility block;
- не создавать искусственные отзывы и рейтинги.

## 6. Visual direction YFC

Сохраняй Approved Design V2:

- premium sport-tech;
- canonical lime accent;
- neutral/graphite light и dark surfaces;
- сильная, но спокойная typography hierarchy;
- disciplined grid;
- реальные product visuals;
- минимум тяжёлых теней;
- точные borders, surfaces и radii;
- light/dark как одна система;
- узнаваемость через реальный продукт, ритм, геометрию и брендовый акцент.

Не использовать по умолчанию:

- AI-purple или blue glow;
- crypto, neon или gaming aesthetics;
- glassmorphism на каждом блоке;
- floating blobs;
- sparkles;
- случайные gradients;
- огромные мягкие shadows;
- бесконечные pills;
- декоративные status dots;
- абстрактные 3D-объекты без связи с продуктом;
- случайные stock photos;
- градиентный текст ради эффекта;
- новый визуальный язык, который не связан с приложением.

Любой заметный приём должен поддерживать хотя бы одно:

- бренд;
- иерархию;
- понимание продукта;
- conversion;
- причинно-следственную связь;
- distinction между самостоятельным пользователем и тренером.

## 7. Композиция Landing

Не применяй один и тот же шаблон ко всем секциям.

Проверяй страницу как последовательность смысловых глав:

1. Header;
2. Hero;
3. high-signal capabilities;
4. real-product showcase;
5. самостоятельный пользователь / тренер;
6. Demo Mode CTA;
7. Web + Telegram Mini App;
8. factual credibility или FAQ;
9. final CTA;
10. Footer.

Точный состав определяется текущей задачей и factual product scope.

### Hero

Hero должен:

- быстро объяснять ценность;
- содержать один ясный H1;
- иметь короткий supporting copy;
- показывать один primary CTA;
- иметь один secondary action только при реальной необходимости;
- показывать реальный продукт;
- не прятать CTA за чрезмерной высотой;
- не превращаться в текстовую стену;
- не использовать decorative filler вместо product proof.

Предпочтительный визуальный материал:

- реальный desktop screen;
- реальный mobile screen;
- controlled render из реальных компонентов;
- согласованная композиция Web + mobile.

### Capabilities

Используй только 4-6 наиболее значимых реальных возможностей.

Не дублируй одну и ту же информацию в capability strip, feature grid и product showcase.

### Product showcase

Показывай сценарии, а не абстрактные категории.

Предпочтительные сценарии:

- дневник питания;
- тренировка на сегодня;
- программа;
- прогресс и замеры;
- работа тренера с клиентом;
- Web + Telegram continuation.

Каждый preview должен соответствовать реальному интерфейсу или controlled render из настоящих компонентов.

### Dual audience

Самостоятельный пользователь и тренер должны получить отдельные, полноценные value propositions.

Не превращай trainer value в одну строку рядом с основным пользовательским сценарием.

### FAQ и Footer

FAQ должен отвечать на реальные возражения и использовать доступную semantic implementation.

Footer не должен быть link farm. Показывай только существующие маршруты, legal pages, support и social links.

## 8. Real-product visual policy

Приоритет визуальных материалов:

1. controlled render из реальных YFC components;
2. реальные screenshots текущего продукта;
3. canonical brand graphics;
4. нейтральная композиция без fake UI.

Не использовать случайное внешнее изображение без ясной лицензии.

Не рисовать fake dashboard или fake app screen, который нельзя воспроизвести в продукте.

Controlled render допустим, если:

- построен из реальных компонентов или их верных presentation variants;
- использует безопасные mock data;
- не содержит персональных данных;
- соответствует текущему Design V2;
- визуально не обещает несуществующую функциональность;
- имеет стабильные размеры и не создаёт CLS.

Для screenshots:

- подготовить responsive derivatives;
- задать width/height или aspect-ratio;
- lazy-load below fold;
- не загружать огромный исходник для маленькой карточки;
- проверять light/dark correspondence;
- не допускать debug/test artifacts.

## 9. Responsive art direction

Mobile - самостоятельная композиция, а не уменьшенный desktop.

Проверить минимум:

- 1440;
- 1280;
- 1024;
- 768;
- 390;
- 360.

На mobile отдельно решить:

- порядок hero copy и visual;
- видимость CTA без чрезмерного scroll;
- размер H1;
- overlap product screens;
- capability grid;
- порядок client/trainer blocks;
- размер screenshots;
- FAQ;
- footer;
- touch targets;
- safe-area;
- отсутствие horizontal overflow.

Не использовать `scale()` или `zoom` как основной способ адаптации всей desktop-композиции.

Не сохранять декоративное наложение экранов, если оно ухудшает читаемость или вызывает overflow на narrow viewport.

## 10. Light и Dark

Light и dark должны быть двумя состояниями одной системы.

Проверяй:

- одинаковую hierarchy;
- semantic color parity;
- корректный canonical logo variant;
- читаемость lime accent;
- контраст controls и text;
- shadows и borders для каждой темы;
- screenshots/product renders в соответствующей теме;
- отсутствие случайной смены visual language между темами.

Не строить dark как механическую инверсию light.

Не переключать отдельные секции в противоположную тему без утверждённой композиционной причины.

## 11. Motion direction

Motion должен объяснять:

- появление следующего смыслового шага;
- связь между Web и Telegram;
- переход между product states;
- focus пользователя;
- feedback на action.

Для Landing по умолчанию:

- короткие transitions;
- transform/opacity;
- без bounce;
- без постоянного looping;
- без scroll hijacking;
- без decorative parallax;
- без floating UI;
- без stagger каждого списка;
- interaction не ждёт завершения animation;
- reduced motion сохраняет смысл и доступность.

Перед каждой заметной анимацией сформулируй одним предложением, что она сообщает. Если ответа нет, не добавляй её.

## 12. Typography

Типографика - главный инструмент качества.

Проверяй:

- display/body/meta hierarchy;
- line length;
- wrapping H1;
- mobile sizes;
- line-height;
- letter-spacing;
- font weights;
- числовые данные;
- одинаковую hierarchy в light/dark.

Не делай каждый H2 огромным.

Не используй bold как единственный способ иерархии.

Не смешивай несколько display families без причины.

Не добавляй новую гарнитуру только ради одного декоративного слова.

## 13. Anti-generic audit

Перед завершением выполни проверки.

### Brand swap test

Если заменить logo и название YFC на случайный SaaS, сохранится ли дизайн почти без изменений?

Если да, усили product-specific character через:

- реальные screens;
- workout/nutrition/progress language;
- canonical lime behavior;
- brand geometry;
- Web + Telegram relationship;
- client/trainer distinction.

### Card test

Можно ли удалить часть cards/containers без потери hierarchy?

Если да, упростить.

### Repetition test

Не повторяется ли один и тот же layout во всех секциях?

Если повторяется, изменить grouping, scale, alignment или visual role, а не добавлять случайный декор.

### Decoration test

Есть ли элементы, которые не поддерживают бренд, понимание продукта, hierarchy или interaction?

Если да, удалить.

### Screenshot test

Выглядит ли вся страница как production product Landing, а не как Tailwind/shadcn starter или Awwwards experiment без продуктовой ясности?

### Conversion test

Понятно ли за несколько секунд:

- что это за продукт;
- кому он нужен;
- что в нём можно сделать;
- чем Web связан с Telegram;
- куда нажать дальше?

## 14. SEO, accessibility и performance

Дизайн не должен ухудшать:

- один корректный H1;
- semantic headings;
- crawlable text;
- internal links;
- metadata и canonical;
- structured data truthfulness;
- keyboard navigation;
- focus visibility;
- labels и accessible names;
- contrast;
- reduced motion;
- touch targets;
- Core Web Vitals;
- image loading;
- CLS;
- initial bundle.

Не скрывай основной marketing content до выполнения client-side JavaScript.

Не делай essential content доступным только после animation или interaction.

Не заменяй meaningful text одной картинкой.

## 15. Рабочий процесс

Для крупного Landing redesign:

1. проверить branch и task scope;
2. прочитать обязательные Design V2 и Landing sources;
3. изучить фактический Landing и `/login`;
4. изучить реальные product screens;
5. сформулировать Design Read;
6. провести audit текущей композиции;
7. определить visual direction без изменения утверждённой системы;
8. выбрать 1-2 репрезентативных блока;
9. довести их до production-ready состояния;
10. распространить систему на остальные секции;
11. реализовать через `frontend-engineer`;
12. проверить реальный render через `ui-audit`;
13. исправить root causes;
14. запустить functional, responsive, accessibility, SEO и performance checks;
15. проверить diff и создать логический commit.

Не переходи сразу к массовой переписи всех секций до проверки hero и одного product-heavy блока.

## 16. Done when

Landing готов, когда:

- визуально соответствует Approved Design V2;
- сохраняет factual product truth;
- показывает реальный продукт;
- ясно продаёт ценность самостоятельному пользователю и тренеру;
- Web и Telegram показаны как один продукт;
- light/dark выглядят как одна система;
- responsive композиция проверена;
- нет generic AI/SaaS appearance;
- нет fake testimonials, metrics и capabilities;
- SEO, accessibility и performance не деградировали;
- нет нового frontend stack;
- Tailwind не добавлен без отдельной migration task;
- Motion добавлен только при доказанной необходимости;
- GSAP отсутствует без owner checkpoint;
- реальный browser render проверен;
- Landing и `/login` выглядят как связанные public surfaces.

## 17. Финальный отчёт

Сообщи кратко:

- что изменено в visual direction и composition;
- какие реальные product visuals использованы;
- какие зависимости добавлены и зачем;
- использовался ли Motion или GSAP;
- какие viewports и themes проверены;
- какие accessibility, SEO, performance и functional checks реально запущены;
- какие deviations от approved renders сделаны и почему;
- commit hash.

Не заявляй о проверке, если она фактически не выполнялась.
