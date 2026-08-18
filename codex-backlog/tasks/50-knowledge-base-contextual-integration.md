# TASK 50. База знаний: public SEO pages + contextual app integration

- Фаза: **Knowledge / SEO / Product UX**
- Приоритет: **50/93**
- Зависит от: `03`, `06`, `23`, `28`, `38`, `40`, `43`, `46`, `49`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$seo-auditor`, `$qa-engineer`

## Цель

Превратить ранний SEO content foundation в реальную Базу знаний и один reviewed source для Public Web, приложения и TMA.

## In scope

Переиспользовать content architecture task `06`, не создавать второй CMS.

Canonical public routes минимум: `/knowledge/`, `/knowledge/<slug>`, `/exercises/`, `/exercises/<exercise-slug>`. Categories: тренировки, питание, кардио, восстановление, упражнения.

Architecture поддерживает topics: RIR, отдых между подходами, training frequency, Full Body vs Split, прогрессия, отказ, КБЖУ, белок, дефицит, рекомпозиция, питание до/после, пульсовые зоны. Не обязательно публиковать все статьи за одну task — лучше несколько качественных cornerstone materials.

Article metadata: slug/title/description/category/summary/body/author-or-reviewer/published-updated/sources/related content/app contexts.

Public exercise pages не копируют guide в отдельные SEO texts: собираются из factual task `20/34` metadata/technique/media. Custom/private exercises не становятся public.

SEO через task `03`: title/description/canonical/OG/crawlable links/Breadcrumb/Article only where truthful/sitemap published only/no fake ratings.

Contextual links: RIR -> Что это?, exercise -> техника, КБЖУ -> расчёт, pulse -> зоны, analytics -> metric explanation, program wizard -> split/frequency article where useful.

TMA использует тот же reviewed source в mobile in-app renderer/sheet/page, без отдельной content DB и без необходимости рендерить весь SEO shell. Предпочитать один source для Public Web/App/TMA/future AI.

Editorial: people-first, sources for meaningful claims, no diagnosis/treatment/pharmacology/guaranteed results, update/review workflow.

## Out of scope

Не создавать social/article comments, pharmacology, mass AI articles, copied Fitness Online/FatSecret text, separate TMA database или Trainer Copilot.

## Проверки

Published/draft/noindex, canonical/sitemap, article/exercise routes, custom exercise not public, internal/context links, TMA rendering, source parity, structured data/a11y.

## Done when

База знаний — реальная продуктовая и SEO surface; Public Web/TMA используют один reviewed source; exercise pages фактические; contextual Что это? links работают.

## Рекомендуемый commit

`feat(knowledge): add contextual public fitness knowledge base`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
