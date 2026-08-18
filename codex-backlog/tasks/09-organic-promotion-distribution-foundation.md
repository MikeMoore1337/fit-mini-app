# TASK 09. Organic promotion, content distribution и acquisition measurement foundation

- Фаза: **Organic Growth**
- Приоритет: **09/93**
- Зависит от: `04`, `06`, `07`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$seo-auditor`, `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Создать практический zero/low-cost organic promotion foundation для Your Fitness Coach после появления корректной public search surface.

Продвижение должно приводить релевантных самостоятельных пользователей и trainers через полезный контент, поисковую видимость, естественные упоминания и shareable product surfaces - без black-hat SEO и спама.

## In scope

### 1. Organic acquisition strategy

Создать durable `docs/seo/organic-growth-playbook.md` или эквивалент.

Разделить аудитории:

- independent fitness users;
- personal trainers.

Разделить acquisition channels:

- Google organic;
- Yandex organic;
- Telegram organic;
- VK/communities;
- экспертные публикации/упоминания;
- естественные backlinks;
- direct/referral.

Не добавлять paid media в scope.

### 2. Search/content roadmap

На основе intent map task `02` и public IA task `06` создать приоритизированный content backlog.

Для каждой идеи:

- audience;
- intent;
- user problem;
- unique angle / why this site has something useful to add;
- target public page or guide;
- internal-link destination;
- product CTA;
- evidence/review requirement;
- status.

Не указывать fictitious keyword volume.

Приоритет отдавать cornerstone content и реальному опыту/экспертизе, а не количеству статей.

### 3. Expert-led content model

Для fitness/nutrition content закрепить:

- author/byline where appropriate;
- reviewer when needed;
- source links/citations;
- last updated;
- fact-check step;
- correction/update process.

AI может помогать drafting/editing, но массовая публикация auto-generated low-value pages запрещена.

### 4. Organic distribution

Для каждого meaningful new guide/product update определить ethical distribution checklist:

- Telegram channel/community sharing where appropriate;
- VK/community sharing where appropriate;
- собственные social profiles;
- relevant professional trainer communities;
- direct sharing of genuinely useful resources.

Не автоматизировать массовые сообщения.

Не спамить комментарии/форумы.

Не создавать fake accounts/reviews.

### 5. Earned links

Backlink strategy должна строиться на link-worthy value:

- оригинальные guides;
- полезные calculators/tools, если они реально публичны;
- методические материалы для trainers;
- research summaries с корректными sources;
- product data/insights только при безопасной агрегации.

Запрещены:

- buying links;
- PBN;
- link farms;
- массовые reciprocal schemes;
- hidden links.

### 6. Shareability

Для canonical public pages:

- корректный Open Graph;
- social preview/brand visuals используют canonical logo assets из task `07`, не перерисовывают бренд;
- social image;
- human-readable title/description;
- stable URL;
- copy-link/share UX только если уместно.

Не создавать separate duplicate URL под каждый social source.

### 7. UTM convention

Определить минимальный стандарт:

```text
utm_source
utm_medium
utm_campaign
utm_content
```

с naming conventions для собственных organic distributions.

Не сохранять UTM как чувствительные profile данные без необходимости.

Если в проекте уже есть privacy-safe analytics/telemetry - связать campaign attribution с ней.

Если нет - документировать convention и не внедрять скрытый tracker.

### 8. Conversion funnel

Определить measurable organic funnel:

```text
search/referral impression
-> public page
-> product/demo CTA
-> demo/auth
-> meaningful product activation
```

Измерять только то, что реально доступно.

Search impressions/clicks - через webmaster tools.

Product conversion - только через существующую/одобренную telemetry.

### 9. AEO/GEO boundary

Не создавать отдельные "AI search hacks".

Для visibility в generative search придерживаться тех же основ:

- crawlable content;
- clear structure;
- unique useful information;
- truthful metadata;
- sources;
- expertise;
- current content.

Не создавать query-fanout pages массово.

### 10. Release integration

Добавить lightweight checklist, чтобы новые public feature/content pages не выходили без:

- metadata;
- canonical;
- index policy;
- internal links;
- source/review check;
- share preview;
- measurement plan.

Не превращать этот checklist в тяжелый release blocker для private application code.

## Out of scope

Не paid ads.

Не cold spam.

Не buying links/PBN.

Не fake reviews/testimonials.

Не automated mass outreach.

Не массовая генерация SEO-статей.

Не скрытая analytics.

Не обещать top-1/search traffic.

Не создавать отдельную fake "GEO optimization" систему.

## Проверки

- content roadmap не содержит thin keyword permutations;
- distribution playbook разделяет user/trainer audiences;
- UTM convention documented;
- share metadata работает;
- public URLs canonical;
- no duplicate campaign URLs;
- no tracker added без explicit decision;
- no black-hat tactics;
- editorial/fact-check process documented.

## Done when

Есть практический organic growth playbook.

Есть content roadmap с фокусом на реальную пользу.

Есть ethical distribution process.

Есть earned-link strategy без black-hat.

Есть UTM/measurement convention.

User и trainer acquisition рассматриваются отдельно.

SEO/growth можно вести системно после каждого релиза.

## Рекомендуемый commit

`docs(growth): establish organic acquisition playbook`

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

## Knowledge-base growth integration
Использовать будущие `/knowledge/` и `/exercises/` как long-term organic assets: cornerstone explainers, legal technique pages, trainer methodology, contextual internal links. Не создавать long-tail permutation farm.
