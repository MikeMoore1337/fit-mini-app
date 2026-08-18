# TASK 06. Public SEO information architecture и content foundation

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **SEO / Public content**
- Приоритет: **06/93**
- Зависит от: `02`, `03`, `04`, `05`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$seo-auditor`

## Цель

Создать минимальную публичную search-oriented information architecture поверх технической SEO-базы и актуальной дизайн-системы.

Цель - дать самостоятельным пользователям и тренерам полезные canonical public pages, способные отвечать на разные search intents без создания thin/doorway/keyword-spam страниц.

## In scope

### 1. Public IA

На основе task `02` утвердить минимальный набор public surfaces.

Пример по смыслу, адаптировать к реальному продукту:

```text
/
├── features / возможности
├── training / тренировки
├── nutrition / питание
├── progress / прогресс
├── for-trainers / для тренеров
├── knowledge / база знаний
└── exercises / публичная энциклопедия упражнений
```

Не создавать маршрут только потому, что "под такой keyword можно сделать страницу".

Каждая indexable page должна иметь отдельную пользу/intent.

### 2. Product truth

Публичный content должен описывать только фактически существующий продукт на момент task.

Если будущая feature ещё не реализована:

- не продавать её как working;
- не создавать fake screenshots;
- либо не публиковать страницу;
- либо держать draft/non-indexable до реализации.

Особенно это касается:

- AI Coach;
- Demo Mode;
- advanced nutrition;
- будущих trainer/admin capabilities.

Поздние tasks обновят public story после фактической реализации.

### 3. Two audiences

Явно поддержать:

#### Independent users

Value around:

- training;
- personal programs;
- nutrition;
- progress;
- unified Web + Telegram experience.

#### Trainers

Value around:

- client management;
- program workflow;
- progress/adherence;
- Coach workspace;

только в объёме фактически существующих возможностей.

Trainer content не должен быть маленьким paragraph внутри unrelated user page, если intent требует отдельной meaningful page.

### 4. Content page template

Создать reusable semantic template для public product/guide pages:

- one clear H1;
- meaningful H2/H3;
- intro answering intent;
- body sections;
- relevant screenshots/media;
- internal links;
- factual CTA;
- author/reviewer/update metadata для editorial guides where applicable;
- canonical/meta/OG through task `03` SEO layer;
- breadcrumbs where useful.

Не делать headings ради keywords.

### 5. Guides / knowledge foundation

Если текущий stack позволяет без тяжёлого CMS, создать maintainable content mechanism:

- existing page/content system;
- Markdown/MDX/content files;
- либо другой простой repo-native approach.

Не добавлять CMS/SaaS только ради SEO.

Создать только небольшой initial set evergreen cornerstone content, если можно сделать качественно и фактологично.

Не массово генерировать статьи.

### Knowledge architecture contract

Заложить один maintainable content source, который later task `50` сможет использовать для Public Web и contextual App/TMA rendering. Categories минимум: training, nutrition, cardio, recovery, exercises. Предусмотреть author/reviewer/sources/updated/related metadata. Не массово заполнять базу сейчас. Public exercise pages позже должны брать factual metadata из exercise domain, а не копировать technique text.

### 6. Fitness/nutrition editorial rules

Публичные guides по фитнесу/питанию должны:

- быть полезными человеку;
- отделять общие fitness/nutrition сведения от медицинской рекомендации;
- не обещать лечение;
- не обещать гарантированное похудение/результат;
- указывать источники для значимых проверяемых claims;
- иметь дату review/update;
- не копировать чужие тексты;
- не быть AI paraphrase commodity content.

Если содержание требует medical expertise, не публиковать его без соответствующего review/source process.

### 7. Internal linking

Создать естественную link architecture:

```text
Landing
-> Feature page
-> Relevant guide
-> Product CTA
```

и обратные contextual links.

Не использовать одинаковые exact-match anchors повсюду.

Не создавать orphan indexable pages.

### 8. Structured data

Для каждой public type использовать только truthful schema из task `03`.

Guide/article markup - только если page действительно article/guide.

BreadcrumbList - только при реальной hierarchy.

Не добавлять fake author/review/rating.

### 9. Public UX

Search visitor должен:

- сразу понять, куда попал;
- получить ответ на intent до aggressive CTA;
- легко перейти к продукту;
- видеть Web/Telegram positioning;
- не столкнуться с auth wall сразу на informational page.

### 10. Future integration points

Оставить понятные точки, которые поздние tasks смогут дополнить:

- Demo CTA после Demo Mode;
- AI Coach page/section после AI implementation;
- final premium landing;
- updated trainer story;
- screenshots реального стабилизированного product UI.

Не делать fake placeholders indexable.

## Out of scope

Не создавать сотни SEO pages.

Не использовать programmatic keyword permutation.

Не добавлять AI-generated article farm.

Не публиковать несуществующие product capabilities.

Не добавлять medical/pharma content.

Не подключать внешний CMS без необходимости.

Не переписывать app architecture.

## Проверки

- every indexable page has unique purpose;
- unique title/H1/canonical;
- no duplicate/thin pages;
- no orphan pages;
- internal links crawlable;
- mobile;
- structured data valid;
- no private data;
- no fake capability;
- build;
- targeted SEO route tests;
- accessibility smoke.

## Done when

Есть понятная public IA для самостоятельного пользователя и trainer audience.

Indexable pages имеют реальную пользу и не дублируют друг друга.

Есть maintainable content foundation.

Health/fitness editorial rules зафиксированы.

Internal linking работает.

Поздние product tasks смогут обновлять public content без переделки SEO architecture.

## Рекомендуемый commit

`feat(seo): add public search information architecture`

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
