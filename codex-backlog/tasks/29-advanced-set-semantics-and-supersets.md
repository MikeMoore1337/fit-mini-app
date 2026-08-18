# TASK 29. Расширенная семантика подходов и supersets

- Фаза: **Training domain**
- Приоритет: **29/93**
- Зависит от: `24`, `27`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Различать разминочные/рабочие/drop-подходы и поддержать supersets без псевдоточных метрик.

## In scope

- Проверить текущие set/template/workout models.
- Разделить `set_kind` (`warmup|working|drop` или эквивалент) и optional `reached_failure`; RIR остаётся отдельным.
- Legacy sets мигрировать безопасно, не переписывая историю задним числом.
- Добавить nullable superset grouping + order на template/materialized workout level.
- Warm-up не считать рабочим объёмом; drop показывать явно; никаких `effective sets`.
- Поддержать copy/assignment/history/analytics compatibility.

## Out of scope

Без rest-pause/giant/cluster sets, auto failure detection, effective reps и отдельного UI.

## Проверки

Migration, legacy sets, combinations set_kind/RIR/failure, superset order, template copy, workout materialization, analytics.

## Done when

Backend/API различают типы подходов и supersets; старые данные работают.

## Рекомендуемый commit

`feat(workouts): add set semantics and superset grouping`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## User-facing terminology constraint

Technical enums may remain in code, but UI follows `PLAIN_LANGUAGE_UX.md`:
- `warmup` -> `Разминочный подход`;
- `working` -> `Рабочий подход`;
- `drop` -> `Дроп-сет` with explanation;
- failure -> clear Russian wording.

Do not force raw enum/English values into UI.
