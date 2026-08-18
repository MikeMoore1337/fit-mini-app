# TASK 33. Адаптивная оценка энергозатрат и калорийности

- Фаза: **Nutrition analytics**
- Приоритет: **33/93**
- Зависит от: `22`, `32`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

После накопления истории deterministic-способом уточнять стартовую оценку энергозатрат по logged intake и тренду массы.

## In scope

- Перед реализацией исследовать актуальные доказательные подходы; не копировать proprietary algorithm.
- Inputs: logged energy intake, smoothed weight trend, goal/current target, data sufficiency.
- Insufficient data => no confident calibration.
- Output: estimate/range, period, sufficiency, deterministic rationale, optional proposed target change.
- Trend smoothing documented/tested.
- Target change только preview + explicit confirmation + history.
- Smartwatch calories не source of truth. AI не участвует.

## Out of scope

Без one-day TDEE, medical diets, proprietary copying, automatic changes.

## Проверки

Sparse/noisy/full data, maintenance/gain/loss, no-change/proposal, accept/reject, formula tests.

## Done when

Приложение осторожно калибрует энергозатраты и не меняет цели без подтверждения.

## Рекомендуемый commit

`feat(nutrition): add adaptive expenditure calibration`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
