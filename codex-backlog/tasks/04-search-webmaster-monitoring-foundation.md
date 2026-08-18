# TASK 04. Google Search Console, Yandex Webmaster и SEO monitoring readiness

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **SEO operations**
- Приоритет: **04/93**
- Зависит от: `03`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$seo-auditor`, `$frontend-engineer`, `$qa-engineer`

## Цель

Подготовить Your Fitness Coach к управляемой индексации и измерению organic search через Google Search Console и Yandex Webmaster без хранения личных verification credentials в Git.

Разделить то, что Codex может реализовать в репозитории, и manual owner actions во внешних кабинетах.

## In scope

### 1. Verification readiness

Поддержать безопасный способ site ownership verification, совместимый с текущим deployment.

Предпочтение:

1. DNS verification как owner-controlled вариант, если инфраструктура позволяет;
2. либо env/config-injected meta verification;
3. либо static verification file, если это соответствует выбранному способу.

Не hardcode личные verification values в repository.

Добавить placeholders только в `.env.example`, если env действительно используется.

### 2. Search Console setup documentation

Создать durable doc, например:

```text
docs/seo/search-console-yandex-webmaster.md
```

с manual checklist:

- add canonical production property;
- verify ownership;
- inspect homepage/public URLs;
- submit canonical sitemap;
- проверить Page Indexing / URL Inspection;
- проверить Core Web Vitals;
- проверить Search performance;
- owner notification settings.

Не утверждать, что внешний account настроен, если Codex не может это подтвердить.

### 3. Yandex Webmaster

Manual checklist:

- add canonical HTTPS site;
- verify rights;
- sitemap;
- indexing diagnostics/searchable pages;
- security/violations;
- structured-data validator;
- primary/alternate host consistency.

Не подключать Metrica автоматически только ради SEO.

### 4. Search monitoring runbook

Добавить repeatable checklist после:

- major release;
- public URL change;
- migration;
- landing redesign;
- metadata change;
- sitemap change.

Отслеживать:

- indexed pages;
- excluded pages;
- crawl/index errors;
- duplicate/canonical issues;
- impressions/clicks/CTR;
- top queries/pages;
- brand vs non-brand where practically possible.

Не ставить vanity goal "все URL обязательно индексируются": sitemap/crawl не гарантируют indexing.

### 5. SEO smoke command/check

Если это вписывается в repo conventions, добавить лёгкий script/test command, проверяющий production/staging public SEO surface без destructive actions:

- robots;
- sitemap;
- canonical;
- status;
- no private URLs in sitemap;
- key metadata.

Все caches/reports по AGENTS - в `.artifacts/`.

### 6. Optional analytics boundary

Search Console и Yandex Webmaster не требуют добавления client-side analytics tag для базового SEO monitoring.

Если в проекте уже есть analytics/telemetry:

- документировать связь organic conversions с существующей telemetry;
- не дублировать tracking.

Если analytics нет:

- не внедрять новую third-party behavioral analytics систему скрыто;
- вынести privacy/legal-consent decision как explicit follow-up.

Yandex Metrica/Google Analytics могут быть рассмотрены отдельно только после решения по privacy/consent/data flow.

### 7. Search-engine submission

Документировать, как и когда submit/re-submit sitemap.

Не строить бессмысленную автоматическую отправку URL во все "search engines".

Не использовать Google Indexing API для обычных продуктовых страниц, если официальный use case не подходит.

## Out of scope

Не логиниться от имени пользователя во внешние сервисы.

Не хранить verification codes/secrets в Git.

Не подключать скрытую behavioral analytics.

Не внедрять cookie banner без отдельного privacy/analytics решения.

Не использовать unofficial indexing APIs/SEO submitters.

Не гарантировать индексацию.

## Проверки

- verification placeholders/config tests;
- no verification secret committed;
- docs completeness;
- SEO smoke command;
- sitemap canonical URL;
- Google/Yandex manual checklist;
- no accidental analytics tag;
- no private page in sitemap.

## Done when

Repository готов к безопасной ownership verification.

Есть понятные manual steps для Google Search Console и Yandex Webmaster.

Есть repeatable SEO monitoring runbook.

Есть lightweight SEO smoke check.

Никакие личные verification credentials или новые tracking systems не добавлены скрыто.

## Рекомендуемый commit

`chore(seo): add webmaster and monitoring readiness`

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
