# TASK 25. Детерминированный подбор тренировочной программы

- Фаза: **Training recommendation domain**
- Приоритет: **25/93**
- Зависит от: `23`, `24`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$qa-engineer`, `$product-designer`

## Цель

Создать прозрачный deterministic program-selection engine для самостоятельного пользователя поверх существующих templates. Не использовать LLM/AI.

## In scope

### Reuse current templates
Проверить `ProgramTemplate.goal`, `level`, days/exercises, public/system template semantics, self assignment, profile goal/level/workouts_per_week, equipment metadata task `23` и фактические Full Body/Upper-Lower/PPL-like templates. Не создавать duplicate program system.

### Inputs
Минимум: цель (fat loss/recomposition/maintenance/muscle gain/strength), experience, силовых тренировок в неделю, место/оборудование, supported structured constraints если они реально существуют. Не делать injury diagnosis questionnaire.

### Explicit decision table
Правила deterministic/explainable. Примеры: beginner+2-3 days часто Full Body; 3-4 days Full Body/Upper-Lower depending on real template fit; higher frequency/experience может дать Upper-Lower/PPL; strength goal только если есть strength-oriented templates. Equipment mismatch исключает incompatible template.

### Compatibility/ranking
Смотреть не только split-name, а goal/level/days/equipment/constraints. При нехватке metadata расширить template metadata минимально и migration-safe.

### Result
Возвращать recommended template ID/title/reason/fit facts/limitations/optional alternatives. Никаких fake `93% match`.

### Workflow contract
`recommend -> preview -> optional copy/edit -> explicit start`. Не активировать автоматически. No-match = controlled state + manual selection/create own.

### Tests/docs
Unit tests decision table, tie-breaking, missing data, no-match.

## Out of scope

Не использовать AI, не генерировать program contents динамически, не активировать программу без explicit action, не выдавать pseudo-precision fit score.

## Проверки

Goals×levels×2/3/4/5+ days, equipment mismatch, missing profile, no match, ties, legacy templates, deterministic repeated result.

## Done when

Есть объяснимый deterministic recommender существующих templates; manual flow сохранён; UI сможет preview/edit/start рекомендацию.

## Рекомендуемый commit

`feat(programs): add deterministic template recommender`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
