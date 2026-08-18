# TASK 27. Расширенная тренировочная аналитика без псевдометрик

- Фаза: **Core analytics**
- Приоритет: **27/93**
- Зависит от: `21`, `23`, `24`, `26`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$qa-engineer`

## Цель

Расширить существующий analytics layer отсутствующими training metrics с явными формулами, не переписывая текущие adherence/volume/PR.

## In scope

Сначала переиспользовать current `services/analytics.py`: при подготовке backlog он уже считает adherence/streak/weight change/weekly completed workouts/weekly volume/PR/timeline.

Добавить exercise-specific progression: performed dates, completed set count, reps, weight, max/best where meaningful, session/set volume, optional RIR history. Если current model не различает warm-up/working sets, не притворяться — считать `completed sets` или явно определить новую модель отдельно.

Volume formula: completed `reps × external load`, period = sum. Документировать ограничения bodyweight/assisted movements.

Muscle distribution только после task `23`: честно считать primary-set exposure и secondary-set exposure separately либо аналогично. Не применять 0.5/0.7 coefficients и не создавать `effective sets` без validated model.

RIR: допускается distribution/reporting buckets и recent values. Нельзя readiness/fatigue/recovery/effective reps/predicted failure.

Trainer detail может получать extended data только при existing relationship access; client list не тянет full history.

Для каждого derived metric: formula, units, missing data, excluded statuses, limitations. Periods 7/30/90 + bounded exercise history, indexes/no N+1.

## Out of scope

Не делать pseudoscientific scores, 1RM prediction, calorie burn from lifting, arbitrary muscle coefficients или AI analysis.

## Проверки

Existing analytics regression, empty/long history, weight/reps trend, RIR mixed/missing, bodyweight limitation, muscle exposure, 7/30/90, trainer isolation, query/index behavior.

## Done when

Exercise progression/set count/RIR/muscle exposure доступны backend; formulas/limitations документированы; псевдометрик нет.

## Рекомендуемый commit

`feat(progress): extend deterministic training analytics`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.
