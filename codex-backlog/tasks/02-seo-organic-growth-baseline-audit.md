# TASK 02. SEO и organic growth - read-only baseline audit

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **SEO / Growth baseline**
- Приоритет: **02/93**
- Зависит от: `00`, `01`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$seo-auditor`, `$qa-engineer`, `$product-designer` при необходимости

## Цель

Провести ранний read-only аудит поисковой доступности и органического продвижения Your Fitness Coach до основной продуктовой переработки.

Цель - понять:

- что поисковые системы могут и должны индексировать;
- что должно оставаться закрытым от индекса;
- какие технические SEO-проблемы уже есть;
- какие публичные страницы реально нужны двум аудиториям: самостоятельным пользователям и тренерам;
- как измерять органический рост;
- какие изменения нужно заложить до дальнейшего redesign/feature work.

Аудит не должен обещать позиции или трафик.

## In scope

### 1. Источники истины

Перед выводами проверить актуальные официальные рекомендации:

- Google Search Central;
- Yandex Webmaster;
- Schema.org;
- web.dev/Core Web Vitals.

Если доступна внешняя сеть - использовать актуальные official docs, а не SEO-блоги и "секреты ранжирования".

Зафиксировать дату проверки.

### 2. Production + repository audit

Проверить фактический production URL и код:

- public routes;
- authenticated routes;
- Telegram-specific routes;
- Demo Mode, если уже существует;
- admin routes, если уже существуют;
- HTTP status;
- HTTPS;
- redirect/canonical host behavior;
- page source / rendered HTML;
- SPA/SSR/prerender behavior;
- `<title>`;
- meta description;
- robots meta;
- canonical;
- Open Graph;
- structured data;
- headings;
- internal links;
- image alt;
- sitemap;
- robots.txt;
- error/404 behavior.

Не делать вывод "Google всё отрендерит" без проверки фактического HTML/JS architecture.

### 3. Indexability policy matrix

Сформировать рекомендуемую матрицу минимум для:

- landing;
- будущих feature/product pages;
- страницы для trainers;
- будущих guides/articles;
- auth/login/register;
- authenticated app;
- private profile;
- workouts/history;
- nutrition diary;
- Coach workspace;
- Admin Workspace;
- Demo Mode;
- technical/error routes.

Для каждой категории:

```text
index?
follow?
canonical?
sitemap?
auth-required?
reason
```

По умолчанию private/user-specific/admin content не должен становиться поисковой поверхностью.

### 4. Search intent map

Не строить бессмысленный keyword dump.

Сформировать intent clusters для российского русскоязычного продукта:

#### Independent users

Например по смыслу:

- дневник тренировок;
- программа тренировок;
- отслеживание прогресса;
- дневник питания;
- КБЖУ;
- fitness tracker;
- fitness app;
- Telegram fitness app;
- AI fitness assistant - только если feature фактически подтверждена.

#### Trainers

Например:

- приложение для фитнес-тренера;
- ведение клиентов;
- программы тренировок для клиентов;
- контроль прогресса клиентов;
- учет тренировок клиентов.

Не заявлять search volume/competition без реального источника.

Разделить:

- informational;
- commercial/product;
- navigational/branded;
- trainer B2B/professional.

### 5. Public content gaps

Определить, какие intents невозможно закрыть текущим landing без keyword stuffing.

Предложить минимальную публичную IA:

- homepage;
- product/features;
- for trainers;
- knowledge/guides;
- legal/trust pages where applicable.

Не создавать отдельную страницу под каждую вариацию ключевой фразы.

### 6. Technical baseline

Зафиксировать:

- crawl/index blockers;
- duplicate URL risks;
- query-string risks;
- canonical risks;
- JS rendering risks;
- sitemap gaps;
- robots/noindex mistakes;
- incorrect 200/soft-404;
- structured-data issues;
- mobile issues;
- obvious Core Web Vitals risks.

### 7. Content quality / trust

Поскольку продукт связан с фитнесом и питанием, отдельно проверить будущие требования к публичному экспертному контенту:

- автор/редактор;
- дата публикации/обновления;
- источники для проверяемых health/fitness claims;
- отсутствие медицинских обещаний;
- отсутствие "гарантированного похудения";
- people-first usefulness;
- отсутствие массового AI-generated low-value content.

### 8. Organic growth baseline

Определить ранние каналы без платного продвижения:

- Google Search;
- Yandex Search;
- Telegram organic sharing;
- VK/сообщества или другие уместные organic channels;
- экспертный контент;
- естественные ссылки/упоминания;
- shareable product utilities, если реально появятся.

Не предлагать spam outreach, buying links, PBN, cloaking и массовую генерацию страниц.

### 9. Measurement baseline

Определить KPI, которые позже можно реально измерять:

- indexed canonical public pages;
- impressions;
- organic clicks;
- CTR;
- branded/non-branded queries;
- landing organic sessions, если analytics законно и фактически настроена;
- demo starts from organic;
- registrations/meaningful conversions from organic, если есть privacy-safe attribution.

Не придумывать текущие значения без данных.

## Out of scope

Не менять код/SEO metadata/robots/sitemap.

Не публиковать контент.

Не подключать analytics.

Не создавать Search Console/Yandex Webmaster accounts.

Не делать paid ads/media plan.

Не покупать ссылки.

Не генерировать сотни keyword pages.

Не превращать audit в redesign task.

## Проверки

Проверить минимум:

- production homepage source/render;
- existing robots.txt;
- existing sitemap;
- canonical/host redirects;
- public/private route inventory;
- current metadata;
- structured data presence;
- mobile rendering;
- basic Lighthouse/PageSpeed-compatible baseline, если доступно;
- current index exposure через безопасные search-engine diagnostics, если доступно.

Все raw outputs/screenshots/reports - `.artifacts/codex-audits/seo/`.

## Done when

Есть grounded SEO/growth baseline с P0-P3 findings.

Есть indexability matrix.

Есть search-intent map для independent users и trainers.

Есть технический список для task `03`.

Есть measurement/manual integration list для task `04`.

Есть IA/content brief для task `06`.

Есть organic promotion brief для task `09`.

Product code не изменён.

## Рекомендуемый commit

`docs(seo): audit organic search baseline`

## Процесс и отчёт

Это **read-only audit**.

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед началом проверить текущую feature-ветку. Не менять product code, tracked docs или конфигурацию.

Рабочие материалы складывать только в:

```text
.artifacts/codex-audits/seo/
```

и не коммитить.

Не переходить к следующему task.

В финальном отчёте:

- executive summary;
- P0-P3 findings;
- indexability matrix;
- public/private route matrix;
- search-intent map;
- technical risks;
- content/growth opportunities;
- measurement gaps;
- конкретные рекомендации для tasks `03`, `04`, `06`, `08`;
- какие проверки реально выполнялись.
