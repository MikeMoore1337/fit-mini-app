# TASK 75. UI performance и motion hardening

- Фаза: **Cross-product hardening**
- Приоритет: **75/93**
- Зависит от: `13`, `28`, `46`, `50`, `68`, `71`, `73`, `74`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$performance-engineer`, `$frontend-engineer`

## Цель

Измерить и оптимизировать стоимость фактической Approved Design V2 implementation и motion на телефоне, не занимаясь premature optimization.

## In scope

Перед измерениями прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`. Измерить production build и оптимизировать только подтверждённые проблемы: JS/CSS bundle delta, font/image loading, animation/main-thread work, layout/reflow, large assets, landing hero, Design V2 surfaces/shadows, long lists, lazy boundaries, initial authenticated render, Admin Workspace user/trainer lists, Coach workspace summaries, Demo Mode fixture/state overhead, Nutrition/Progress lists.

Offscreen decorative animations не должны постоянно грузить CPU. Предпочитать transform/opacity. Проверить mobile backdrop-filter и large assets, включая canonical logo/favicon assets из task `07`: SVG не должен дублировать embedded raster data или тянуть внешние font/network dependencies. Не делать мигающие skeletons на мгновенных ответах. Сравнивать с доступным pre-redesign baseline/предыдущим build и фиксировать реальные измерения.


## Core Web Vitals / public SEO performance

Для canonical public pages отдельно проверить актуальные Core Web Vitals по official web.dev/Google Search documentation.

На момент составления backlog ориентиры "good" включают:

- LCP <= 2.5 s;
- INP <= 200 ms;
- CLS <= 0.1;

оценивать на 75th percentile field data, когда такие данные доступны.

Lab Lighthouse не выдавать за field performance.

При выполнении task перепроверить актуальные thresholds.

SEO/content не должен ухудшать performance через:

- огромные hero assets;
- layout shifts;
- heavy third-party scripts;
- excessive animation;
- unnecessary hydration/JS.

## Out of scope

Не переписывать backend, React/stack, не делать global dependency upgrade, не добавлять virtualization/Lighthouse dependency без реальной необходимости.



## Design V2 assets and effects

Approved Design V2 renders are design inputs only and must not be shipped as oversized production images. Production screenshots/mockups derived from real UI must use appropriate responsive formats/sizes, preserve intrinsic dimensions and avoid CLS. Legacy Landing PNG не участвуют в acceptance. Motion должен поддерживать hierarchy, causality или feedback, отключаться/упрощаться через `prefers-reduced-motion` и не добавлять тяжёлые декоративные effects.

## Проверки

Production build + asset comparison, landing/app/Mobile Web/TMA smoke, console errors/warnings, interaction responsiveness. Проверить, что unified Web/TMA design не реализован через дублирование больших platform-specific CSS/component bundles. Lighthouse использовать только если уже доступен без лишней инфраструктуры.

## Done when

Нет необоснованного существенного bundle growth, offscreen animation CPU work и заметных layout jumps; shared Web/TMA UI не дублирует тяжёлые visual assets/styles; изменения подтверждены измерениями.

## Рекомендуемый commit

`perf(ui): optimize redesigned interface`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать в текущей feature-ветке, не merge/deploy. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.


## Auth performance

Проверить login/auth public shell: no layout shift from provider assets, no heavy animation, minimal third-party JS before provider redirect.

## Exercise media performance
No eager WebM/animation, lazy load, poster/static fallback, cache, reserved dimensions/CLS, TMA bandwidth, reduced motion, public exercise page media weight. Heavy exercise assets не ухудшают Landing/Knowledge LCP.

## AI comes later
Этот task hardens основное приложение до AI UI. AI-specific frontend performance проверяется в task `90` и финальном task `93`.

## Final release integration: added performance surfaces

Проверить, что:
- onboarding не добавляет тяжёлый initial bundle без необходимости;
- export не блокирует UI/server worker надолго;
- notification scheduler не создаёт N+1/duplicate jobs;
- cardio history не ухудшает Progress queries.
