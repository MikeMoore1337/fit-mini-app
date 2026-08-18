# TASK 73. Лендинг - premium refresh по утверждённым light/dark референсам

- Фаза: **Marketing UX**
- Приоритет: **73/93**
- Зависит от: `02`, `03`, `04`, `05`, `06`, `07`, `09`, `13`, `38`, `39`, `40`, `41`, `43`, `44`, `45`, `46`, `48`, `49`, `50`, `51`, `52`, `53`, `54`, `55`, `57`, `65`, `68`, `72`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Пересобрать public Landing в финальном premium sport-tech направлении по утверждённым пользователем референсам, сохранив factual product truth, SEO, accessibility и лёгкую реализацию.

Landing должен выглядеть как один зрелый коммерческий продукт в light и dark темах и ясно продавать ценность двум аудиториям:

1. самостоятельному пользователю;
2. персональному тренеру.

Не копировать PNG пиксель-в-пиксель и не переносить из них вымышленные тексты/данные. Использовать их как визуальный source of truth по композиции, плотности, hierarchy и характеру оформления.

## Обязательные источники перед началом

Прочитать и учитывать:

- `codex-backlog/LANDING_REFERENCE_NOTES.md`;
- `codex-backlog/references/landing/landing-reference-dark.png`;
- `codex-backlog/references/landing/landing-reference-light.png`;
- `codex-backlog/BRAND_ASSET_NOTES.md`;
- canonical logo assets из task `07`;
- SEO/public IA результаты tasks `02`, `03`, `04`, `06`, `09`;
- фактический текущий Landing и `/login`;
- реальные product screens после product UX/TMA tasks.

Если старый `masters/premium-redesign-master.md` расходится с новыми landing references, новые references имеют приоритет, если это не нарушает security/privacy/SEO/product truth.

## 1. Visual direction

Визуальная цель:

- premium sport-tech;
- lime accent + нейтральные светлая/тёмная поверхности;
- clean typography и выраженная hierarchy;
- аккуратные cards/surfaces, тонкие borders, умеренные radii;
- минимум тяжёлых теней;
- без neon/glassmorphism/crypto/gaming эстетики;
- dark и light - полноценные варианты одной системы, а не две разные страницы;
- canonical logo из task `07`, без нового редизайна mark/wordmark.

Сохранить характер референса: много воздуха, ясная сетка, product UI как главный визуальный материал, lime применяется дозированно для акцента и CTA.

## 2. Header

Ориентир - компактный desktop header из референсов:

- слева canonical logo + wordmark;
- по центру/рядом основные public anchors/routes;
- справа `Войти` как secondary action;
- один lime primary CTA;
- mobile navigation - доступный menu pattern.

Состав ссылок брать из фактической public IA. Не копировать `Тарифы`, `Цены`, `О проекте` и другие пункты, если соответствующих production pages/sections нет.

Header не должен быть визуально тяжелее hero.

## 3. Hero

Собрать hero по композиционному принципу референса:

### Left

- крупный двухуровневый headline;
- ключевая смысловая строка/фраза выделена lime;
- короткий supporting copy;
- один primary CTA;
- secondary `Посмотреть демо` / эквивалент из task `65`;
- компактные factual trust/value markers только если они подтверждены продуктом.

### Right

Крупный real-product composition:

- desktop/web screen + mobile screen;
- использовать реальный UI текущего продукта или controlled render из реальных компонентов;
- screens должны быть согласованы с light/dark theme;
- не рисовать маркетинговый mock UI, которого нет в приложении;
- не создавать CLS при загрузке.

### Product message

До AI block основной смысл hero:

`тренировки + питание + прогресс + работа с тренером в одном продукте`.

AI Coach нельзя выдавать за доступную production feature до завершения tasks `76-91`. После task `90` разрешён небольшой factual copy update без второго redesign.

## 4. Capability strip

Сразу под hero - компактный ряд/сетка из примерно 5-6 возможностей с простыми line icons в духе референсов.

Выбирать только высокосигнальные реальные функции, например:

- питание/КБЖУ;
- программы тренировок;
- прогресс/замеры;
- работа с тренером;
- уведомления;
- cardio/пульсовые зоны только если фактически реализованы к этому моменту.

Не дублировать ниже полный feature list.

На mobile блок должен превращаться в читаемую сетку без horizontal overflow.

## 5. Product showcase - «Что умеет Your Fitness Coach»

Секция в стилистике четырёх крупных product cards из референса.

Предпочтительные реальные сценарии:

1. дневник питания;
2. тренировка/программа;
3. прогресс/замеры;
4. работа с тренером/client flow.

Для каждой карточки:

- короткий title;
- 1-2 строки объяснения;
- крупный реальный mobile screenshot/product render;
- одинаковая визуальная грамматика;
- screenshots не должны содержать случайные test/debug данные, персональные реальные данные или несуществующий UI.

## 6. Для клиентов / Для тренеров

Сделать отдельную крупную dual-audience section по структуре референса.

### Для клиентов

Показывать только фактическую ценность:

- программы и тренировки;
- питание/КБЖУ;
- progress/measurements;
- adherence/check-ins;
- связь с тренером, если пользователь работает с ним;
- Web + Telegram.

### Для тренеров

Trainer value proposition должен быть полноценным:

- client list/invitations;
- client status/activity overview;
- client detail;
- программы и изменения;
- workout history;
- progress/measurements;
- adherence;
- nutrition summary только при корректном permission/access;
- Web + Telegram Mini App.

Не обещать Trainer Copilot, AI-анализ client base, AI reports или автономное изменение программ.

### Images

Референс использует изображения спортсменов. Не загружать случайные изображения из интернета.

Использовать их только если в проекте есть легальный production asset/source с понятной лицензией. Иначе сохранить структуру секции, но заменить people images на реальные product visuals/нейтральную brand composition.

## 7. Demo Mode CTA

Сделать отдельный выразительный horizontal CTA в духе референсов:

- короткий title;
- 1-2 строки;
- один CTA;
- visually distinct, но не конкурирует с hero CTA.

Формулировки должны соответствовать фактическому Demo Mode после tasks `62-68`.

AI Coach:

- не доступен в user demo и trainer demo;
- не делать real provider calls;
- не показывать fake functional chat;
- допустим только static product preview, явно не выдаваемый за рабочий demo AI.

## 8. Platform section

Секция по структуре трёх cards из референсов:

- Web application;
- Telegram Mini App;
- responsive/adaptive interface.

Главный message: это один продукт и одна учётная запись/данные, если это подтверждено auth/account architecture, а не три отдельных продукта.

Использовать реальные product images/screens.

## 9. Social proof - запрет на выдуманные отзывы

В PNG присутствуют карточки отзывов со звёздами и именами. Они являются только композиционным примером.

Пока нет реального проверяемого social proof:

- не создавать вымышленных пользователей;
- не генерировать лица/аватары «клиентов» как будто это реальные люди;
- не придумывать отзывы, оценки, число пользователей или retention;
- секцию можно скрыть или заменить factual credibility section без ложного social proof.

Если к моменту task `73` реальные отзывы уже есть в разрешённом источнике, использовать только подтверждённые тексты с согласованной privacy policy.

## 10. FAQ

Сделать clean accordion в структуре, близкой к референсу.

FAQ должен:

- отвечать на реальные вопросы пользователя;
- быть основан на фактическом продукте;
- не обещать несуществующие тарифы/подписки/integrations;
- иметь доступную keyboard semantics;
- сохранять crawlable text;
- при необходимости поддерживать FAQ structured data только если это соответствует актуальным требованиям поисковых систем и текущему SEO foundation.

## 11. Footer

Сделать clean multi-column footer:

- canonical logo;
- короткое factual описание;
- product/public links;
- company/legal links только к реально существующим страницам;
- support/contact только реальные;
- social links только реальные.

Не копировать email/username/copyright year из reference PNG как данные.

## 12. Landing + Auth visual system

Landing и `/login` - одна public product surface.

Обязательный flow:

```text
Landing -> Войти -> /login -> Telegram / Google / Яндекс / VK ID -> product
```

Task обязан final-sync auth shell после premium redesign:

- использовать canonical full logo light/dark из task `07`;
- logo/typography/colors/surfaces/radii/shadows/light-dark/motion согласованы;
- `/login` спокойнее hero, но явно тот же бренд;
- provider branding не искажать;
- reset/verify, если используются, наследуют auth shell;
- auth logic/provider protocols не переписывать;
- `/login` остаётся `noindex` и вне sitemap;
- Demo и Login CTA не конкурируют;
- mobile Landing -> Login выглядит как один продукт.

Landing visual QA не завершён, если `/login` остался в старой стилистике.

Favicon/brand metadata остаются canonical из task `07`; Landing task не создаёт отдельный favicon.

## 13. SEO integration

Landing redesign должен сохранить и усилить SEO foundation, а не заново его изобретать.

Обязательно:

- сохранить canonical public URL и redirect policy;
- сохранить route-aware metadata;
- не ломать `robots.txt`/sitemap;
- не менять indexability private routes;
- сохранить crawlable semantic content;
- один понятный H1;
- internal links к фактическим public feature/trainer/guide pages;
- titles/descriptions/OG соответствуют финальному visible content;
- structured data соответствует visible content;
- не удалять meaningful public text ради screenshots/animation;
- основной marketing content не должен существовать только после client-side interaction;
- при изменении public URL - safe redirect/canonical migration;
- не создавать duplicate variants по campaign params.

После redesign повторить SEO smoke checks и проверить rendered HTML, metadata, canonical, structured data, sitemap и mobile experience.

## 14. Light / Dark contract

Обе темы должны следовать утверждённым references:

- dark: глубокие нейтральные surfaces + white/soft-gray text + lime accents;
- light: white/very-light surfaces + dark text + тот же lime accent;
- одинаковая visual hierarchy;
- logo variant выбирается из canonical assets task `07`;
- screenshots/product renders по возможности соответствуют текущей теме;
- не использовать pure inversion фильтры для переключения screenshots/icons.

Theme switching использовать из task `08`.

## 15. Motion

Допустимы только лёгкие эффекты:

- subtle section reveal;
- progress animation;
- completed set/rest timer demo;
- очень медленное decorative hero movement;
- CTA microinteraction.

Использовать CSS/Web APIs/lightweight React state.

Обязательно `prefers-reduced-motion`.

Не использовать scroll-jacking, heavy parallax, Three.js/WebGL, autoplay video или тяжёлую animation library без уже существующей оправданной зависимости.

## 16. Responsive implementation

Проверить как минимум:

- 1440;
- 1280;
- 1024;
- 768;
- 390;
- 360.

На mobile:

- hero идёт последовательным content flow;
- CTA виден до чрезмерного scroll;
- mockups не перекрывают text/actions;
- capability strip становится grid;
- showcase cards не обрезаются;
- client/trainer section становится вертикальной;
- platform cards перестраиваются;
- FAQ/footer без horizontal scroll;
- mobile menu доступно с keyboard/screen reader.

Не уменьшать desktop landing целиком через scale/zoom.

## 17. Content truth gate

Reference PNG не является источником factual data.

Перед переносом проверить любые элементы вроде:

- `14 дней бесплатно`;
- `без привязки карты`;
- цены/тарифы;
- email/Telegram username;
- testimonials/ratings;
- конкретные числа пользователей;
- AI Coach availability;
- любые конкретные app metrics.

Если факт не подтверждён текущим продуктом/конфигурацией/документацией, не показывать его.

## AI Coach как marketing feature после AI block

После завершения tasks `76-91` допускается **точечное** обновление Landing copy/product screenshot, чтобы показать реально работающий AI Coach:

- вопросы по тренировкам;
- фитнес/питание/спортивное питание в рамках policy;
- объяснение КБЖУ и backend calculations;
- учёт доступного user context;
- app help.

Не раскрывать конкретных LLM providers, внутренний LLM Router и fallback-детали на marketing Landing.

Не делать второй Landing redesign после AI block.

## Out of scope

- новый frontend stack;
- отдельный Landing SPA только ради дизайна;
- новый logo/favicon;
- Three.js/WebGL;
- autoplay heavy video;
- тяжёлая animation library;
- literal copy другого бренда;
- выдуманный social proof;
- выдуманные trainer/AI capabilities;
- Trainer Copilot;
- AI в Demo Mode;
- provider calls из Landing preview;
- случайные нелицензированные stock images.

## Проверки

### Functional

- header navigation;
- Login flow;
- primary CTA;
- Demo CTA;
- FAQ;
- public links;
- mobile menu;
- theme switch/inheritance;
- no broken links.

### Visual

- light/dark;
- 1440/1280/1024/768/390/360;
- сравнить composition/hierarchy с обоими утверждёнными references;
- canonical logo;
- readable text/CTA;
- real product visuals;
- no overflow;
- no accidental legacy styles.

Visual QA не означает pixel-perfect copy: задача - сохранить утверждённое направление и улучшить его под реальный продукт/responsive constraints.

### Accessibility

- keyboard;
- focus states;
- semantic heading order;
- contrast;
- accessible accordion/menu;
- touch targets;
- reduced motion.

### Performance

- no avoidable CLS;
- responsive image sizes;
- lazy loading below fold;
- не грузить огромные source screenshots там, где нужен responsive derivative;
- production build;
- targeted Lighthouse/Core Web Vitals smoke, если infrastructure уже есть.

### SEO

- rendered content;
- title/description;
- canonical;
- OG/share preview;
- sitemap/robots unaffected;
- structured data factual;
- internal links.

## Done when

- Landing явно узнаваем как реализация утверждённых light/dark references;
- структура hero/capabilities/showcase/client-trainer/demo/platform/FAQ/footer реализована или осознанно адаптирована под factual product truth;
- canonical logo из task `07` используется корректно;
- favicon не дублируется и не переопределяется;
- light/dark выглядят как одна premium design system;
- product screenshots соответствуют реальному приложению;
- нет выдуманных отзывов/рейтингов/пользователей/цен/условий;
- Landing ясно продаёт самостоятельный и trainer сценарии;
- Demo Mode показан корректно;
- AI не рекламируется как работающий до завершения AI block;
- Landing и `/login` визуально связаны;
- SEO/a11y/responsive/performance checks не деградировали;
- production build проходит.

## Рекомендуемый commit

`feat(landing): implement approved premium light dark direction`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать в текущей feature-ветке, не merge/deploy. Не переходить к следующему task.

После изменений:

1. запустить только профильные проверки;
2. проверить diff;
3. сохранить visual artifacts только в `.artifacts/landing/`;
4. создать один логический commit;
5. в финальном отчёте перечислить изменения, ключевые файлы, реально запущенные проверки, visual deviations от reference и их причины, ограничения и commit hash.
