# TASK 46. Расширенная карточка упражнения и визуальная техника

- Фаза: **Core UX**
- Приоритет: **46/93**
- Зависит от: `23`, `28`, `44`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Развить существующий ExerciseGuideDialog/catalog detail до полноценной карточки упражнения без переписывания техники и изображений с нуля.

## In scope

Переиспользовать existing guide: technique steps, breathing, mistakes, images, source/license и имеющуюся muscle metadata.

Показывать по наличию: title, media task `28`, technique, breathing, mistakes, safety notes, primary muscles, secondary muscles, equipment, alternatives. Missing metadata не заменять выдумками.

Muscles из task `23`, без contribution percentages. Alternatives открывают existing catalog/detail и не называются медицински эквивалентными.

Один shared detail/guide experience открывается из catalog, program builder, active workout, history и later public exercise route. Не плодить разные technique components.

Media lazy/poster/fallback/reduced motion; no eager large downloads. Source/license attribution сохраняется аккуратно.

## Out of scope

Не копировать Fitness Online content/assets, не делать paid video, muscle analytics или medical contraindication engine. Public SEO pages окончательно task `50`.

## Проверки

Full/partial guide, custom exercise, no guide, muscles, alternatives, media fallback, reduced motion, open from all contexts, modal/lightbox a11y/mobile.

## Done when

Existing guide стал полноценной shared exercise card с muscles/equipment/alternatives/safety/media и корректным Web/mobile/TMA behavior.

## Рекомендуемый commit

`feat(ui): expand exercise guide and technique experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.

## Terminology and explanations

Technique instructions remain understandable.
Prefer `Основные мышцы`, `Дополнительные мышцы` and plain movement cues.
Uncommon anatomical/training words get concise explanations.
