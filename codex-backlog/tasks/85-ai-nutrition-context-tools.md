# TASK 85. AI Coach: персональный nutrition context

- Фаза: **AI Coach**
- Приоритет: **85/93**
- Зависит от: `22`, `32`, `33`, `52`, `77`, `82`, `84`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Дать read-only Coach безопасный доступ к пищевому дневнику и nutrition analytics конкретного пользователя.

## In scope

- Tools: current goal/targets, today consumed/remaining, 7/14/30 summaries, macro adherence/coverage, meal patterns, bounded raw detail when needed, weight trend, adaptive expenditure, training context.
- Backend считает, LLM интерпретирует.
- Use cases: `Что мне ещё можно сегодня поесть?`, `Почему перебираю калории?`, `Посмотри питание за 2 недели`, `Стоит ли менять калорийность?`.
- Recommend/explain only; no writes. Data confidence required.

## Out of scope

Без medical dietetics, eating-disorder coaching, pharmacology, autonomous writes и cross-user diary access.

## Проверки

User isolation, empty/partial/full diary, remaining macros, bounded retrieval, prompt injection in food text.

## Done when

Coach анализирует питание конкретного пользователя на backend facts/confidence.

## Рекомендуемый commit

`feat(ai): add personal nutrition context tools`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
