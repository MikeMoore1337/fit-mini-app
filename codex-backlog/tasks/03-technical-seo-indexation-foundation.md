# TASK 03. Technical SEO и indexation foundation

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **SEO foundation**
- Приоритет: **03/93**
- Зависит от: `02`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$frontend-engineer`, `$backend-engineer`, `$qa-engineer`

## Цель

Исправить подтверждённые технические SEO/indexability проблемы из task `02` и создать устойчивый фундамент для Google и Yandex до дальнейшего развития продукта.

SEO architecture должна чётко разделять публичный индексируемый marketing/content surface и private application surface.

## In scope

### 1. Indexability policy

Реализовать/централизовать policy из task `02`.

Публичные страницы индексировать только если они:

- имеют самостоятельную пользовательскую ценность;
- доступны без auth;
- содержат фактический контент;
- имеют canonical URL.

Private/authenticated/admin/user-specific pages не должны становиться поисковыми landing pages.

Особенно проверить:

- login/register;
- authenticated application routes;
- profile;
- workout history;
- nutrition diary;
- Coach workspace;
- Admin Workspace;
- Demo Mode.

Для Demo Mode по умолчанию предпочитать `noindex`, если task `02` не доказал отдельную поисковую ценность. Demo остаётся conversion tool, а не SEO duplicate surface.

### 2. robots.txt

Сделать корректный `robots.txt`.

Помнить:

- robots.txt управляет crawling;
- robots.txt не использовать как единственный способ исключения HTML-страницы из индекса;
- index exclusion для доступной HTML-page делать через корректный `noindex`/auth policy.

Добавить Sitemap directive, если sitemap используется.

Не блокировать crawler от ресурсов, необходимых для rendering публичных страниц.

### 3. Sitemap

Сделать deterministic sitemap только для canonical indexable public URLs.

Не включать:

- auth;
- private app;
- user-specific URLs;
- admin;
- duplicate/filter/query URLs;
- demo, если он `noindex`;
- drafts.

`lastmod` указывать только если он отражает реальное meaningful content update.

### 4. Canonical / host / redirects

Выбрать фактический canonical production origin.

Проверить:

- HTTPS;
- www/non-www;
- trailing slash policy;
- duplicate route variants;
- query params;
- old public URLs.

Использовать redirects там, где URL действительно перемещён.

Self-canonical для canonical public pages.

Не canonicalize разные по смыслу страницы на одну только ради "SEO".

### 5. Metadata foundation

Создать reusable route-aware SEO metadata layer для public pages:

- title;
- description;
- canonical;
- robots;
- Open Graph;
- social image, если фактически есть.

Не использовать один title/description на всех публичных URL.

Не делать keyword stuffing.

Private routes должны получать безопасную non-index policy централизованно.

### 6. JavaScript SEO

Проверить текущий frontend stack.

Для indexable public pages обеспечить, насколько это возможно в текущей архитектуре:

- crawler-visible meaningful HTML;
- корректные links `<a href>`;
- deterministic status;
- metadata, доступные crawler;
- отсутствие зависимости от user interaction для появления основного текста.

Если текущий SPA действительно требует prerender/SSR для публичной search surface, выбрать минимальный совместимый подход.

Не переписывать весь app новым framework только ради SEO.

### 7. Structured data

Добавлять JSON-LD/Schema.org только для фактически видимого контента.

Рассмотреть по уместности:

- `Organization`;
- `WebSite`;
- `SoftwareApplication`;
- `BreadcrumbList` на вложенных public pages.

Не создавать:

- fake ratings;
- fake reviews;
- fake offers/prices;
- fake authors;
- markup, не соответствующий странице.

Structured data должен валидироваться и не использоваться как обещание rich result.

### 8. Error/status behavior

Публичные несуществующие URL должны отдавать корректное error behavior.

Не оставлять soft-404 с `200 OK`, если route реально отсутствует.

Проверить redirect loops/chains.

### 9. Mobile / Core Web Vitals guardrails

Не выполнять финальный performance epic, но зафиксировать SEO guardrails:

- responsive public content;
- отсутствие layout shifts из-за hero/media;
- image dimensions/aspect ratio;
- font/loading strategy;
- минимизация blocking work;
- никакого тяжёлого SEO-only JS.

Текущие официальные CWV targets перепроверять в official docs при выполнении task.

### 10. Automated SEO checks

Добавить быстрые deterministic checks для ключевых public/private route contracts:

- canonical presence;
- unique title;
- robots policy;
- sitemap excludes private;
- sitemap URLs return expected status;
- structured data parse;
- no accidental private URL exposure.

Использовать существующий test stack.

## Out of scope

Не создавать content hub - task `06`.

Не подключать Search Console/Yandex Webmaster - task `04`.

Не делать final landing redesign - позже отдельный task.

Не менять app stack целиком.

Не добавлять fake schema fields.

Не индексировать authenticated/private data.

Не обещать позиции в поиске.

## Проверки

Минимум:

- `robots.txt` syntax/behavior;
- sitemap XML validity;
- sitemap contains only intended canonical public URLs;
- canonical host/redirect checks;
- public metadata checks;
- private route `noindex`/auth checks;
- 404 behavior;
- structured-data validation locally where possible;
- production build;
- route-level SEO tests;
- mobile/public render smoke.

Если production не трогается в текущем task - явно отделить local/staging verification от production follow-up.

## Done when

Есть единый technical SEO layer.

Public/private indexability policy реализована.

Canonical/robots/sitemap согласованы.

Private application data не попадает в sitemap/search surface.

Public pages имеют route-aware metadata.

Structured data truthful.

Есть быстрые regression checks.

## Рекомендуемый commit

`feat(seo): establish crawl and indexation foundation`

## Процесс и отчёт

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке.

Не:

- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- переходить к следующему task.

После изменений:

1. запустить только профильные проверки согласно `AGENTS.md`;
2. проверить `git diff`;
3. исправить проблемы текущего scope;
4. создать один логический commit при tracked changes;
5. оставить проект в рабочем состоянии.

В финальном отчёте перечислить:

- что сделано;
- ключевые файлы;
- SEO/indexability decisions;
- реально запущенные проверки;
- результаты;
- manual follow-ups;
- ограничения;
- commit hash, если был.
