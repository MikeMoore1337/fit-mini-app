# TASK 24. RIR как необязательный показатель рабочего подхода

- Фаза: **Training domain**
- Приоритет: **24/93**
- Зависит от: `23`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$backend-engineer`, `$qa-engineer`

## Цель

Добавить RIR как полностью необязательный показатель подхода. На момент подготовки backlog `UserWorkoutSet` хранит reps/weight/completion, но отдельного RIR field нет.

## In scope

Добавить nullable RIR semantics на фактически выполненный set. Product values: `0 / 1 / 2 / 3 / 4+`; `None` означает, что RIR не использовался. Representation должна не притворяться, что `4+` — точное физиологическое значение 4.

Обновить set create/update/complete/resume/history/export schemas/API. Старые sets остаются валидными. RIR не влияет на completion, progression, calories или readiness. Сделать поле доступным task `27` и future AI без AI logic сейчас. Добавить короткое domain explanation RIR.

## Out of scope

Не делать RIR обязательным, не добавлять RPE conversion, auto-RIR, auto-progression или UI.

## Проверки

Null/0/1/2/3/4+, invalid values, old rows, save/resume/history/export, completion without RIR, API compatibility.

## Done when

RIR безопасно хранится и необязателен; старые тренировки не ломаются; `4+` не выдаётся за точную оценку.

## Рекомендуемый commit

`feat(workouts): add optional rir to completed sets`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.

## Plain-language RIR contract

`RIR` may remain an internal/API term. Primary UI label is `Повторы в запасе`.

Explain: `Сколько повторов вы ещё могли бы сделать с хорошей техникой после завершения подхода?`

Values:
- `0 — больше не смог бы`;
- `1 — ещё примерно 1 повтор`;
- `2 — ещё примерно 2 повтора`;
- `3 — ещё примерно 3 повтора`;
- `4+ — осталось много сил`.

The field remains optional unless an explicit advanced program requires it.
