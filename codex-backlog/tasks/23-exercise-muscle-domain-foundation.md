# TASK 23. Exercise domain: muscles, equipment, alternatives и guide metadata

- Фаза: **Training domain**
- Приоритет: **23/93**
- Зависит от: `22`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$qa-engineer`

## Цель

Нормализовать уже существующую exercise metadata так, чтобы её можно было честно использовать в программах, аналитике и базе знаний, не переписывая текущий каталог/guide с нуля.

## In scope

### Current-state first
Проверить `Exercise`, custom/personalized exercise semantics, `source_exercise_id`, guide service, catalog schemas/API, seed/import pipeline и migrations. На момент подготовки backlog `Exercise.primary_muscle` уже существует, а `exercise_guides.py` уже содержит secondary muscle profiles и формирует muscles payload — это нужно переиспользовать.

### Canonical muscle taxonomy
Ввести устойчивые identifiers/relations для `primary` и `secondary` muscles. Модель должна допускать несколько мышц при реальной необходимости. Никаких fractional contribution вроде 0.7/0.3 без отдельной обоснованной модели.

### Migration/backfill
Переиспользовать current `primary_muscle`, secondary data из guide profiles и trusted seed data. Backfill deterministic/idempotent/testable, custom exercises не получают выдуманные мышцы.

### Equipment
Проверить текущий `equipment`. Если plain string недостаточен для recommender/filtering, добавить controlled canonical equipment identifiers (bodyweight/dumbbell/barbell/bench/cable/machine/kettlebell/cardio/other) только по фактическому каталогу.

### Alternatives
Добавить curated relation exercise -> alternatives, если её ещё нет. Не считать любое упражнение той же мышцы равноценной заменой.

### Extended guide metadata
Подготовить structured fields для primary/secondary muscles, equipment, safety notes, alternatives, source/license и media reference. Technique/breathing/mistakes не дублировать в несовместимой второй модели.

### API/data quality
Catalog/detail/guide API отдаёт stable identifiers. Custom exercises могут иметь partial metadata. Проверить duplicate relations, self-alternative, indexes и source/license preservation. Не копировать Fitness Online data/assets.

## Out of scope

Не делать expanded UI, media pipeline, muscle-volume analytics, program recommender или AI classification. Не вводить сомнительные коэффициенты secondary muscle contribution.

## Проверки

Migration/backfill, custom exercise partial metadata, duplicate relations, catalog/detail serialization, alternatives, personalized copies, source/license, indexes/query counts.

## Done when

Есть единая structured muscle/equipment/alternative model; существующая guide-информация переиспользована; custom exercises деградируют корректно; frontend/analytics получают stable identifiers.

## Рекомендуемый commit

`feat(training): normalize exercise muscles and metadata`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
