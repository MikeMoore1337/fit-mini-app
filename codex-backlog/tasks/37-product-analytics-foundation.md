# TASK 37. Privacy-safe product analytics foundation

- Фаза: **Product platform**
- Приоритет: **37/93**
- Зависит от: `06`, `13`, `22`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Понимать funnels и использование продукта без утечки чувствительных fitness/nutrition данных.

## In scope

- Переиспользовать SEO/measurement stack 02-04 где уместно.
- Provider-neutral event contract.
- Events: landing/demo/login/onboarding/program/workout/food_logged/measurement/check-in и key conversions.
- Запрещено в payload: food contents, exact weight/measurements/macros, trainer comments, AI conversation text, secrets/raw IDs без необходимости.
- Dev/test separation, SPA dedupe, event versioning.
- Consent/legal path исследовать по актуальным официальным требованиям; не делать legal guess.
- Core instrumentation позже task 57.

## Out of scope

Без BI warehouse, sensitive session replay, full request logging и paid dependency by default.

## Проверки

Duplicate events, sensitive payload regression, dev/test, provider unavailable, schema validation.

## Done when

Есть безопасный единый contract для продуктовой телеметрии.

## Рекомендуемый commit

`feat(analytics): add privacy-safe product event foundation`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
