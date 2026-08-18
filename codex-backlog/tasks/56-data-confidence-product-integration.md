# TASK 56. Data confidence в аналитике и рекомендациях

- Фаза: **Core UX / Explainability**
- Приоритет: **56/93**
- Зависит от: `32`, `43`, `51`, `52`, `55`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Показывать ограничения данных там, где они реально влияют на вывод.

## In scope

- Reusable sufficient/limited/insufficient state; concrete reason such as `4/14 days`; nutrition/weight/anthropometry/training; helpful CTA; no blocking; same metadata later AI.

## Out of scope

Без universal score, shame/gamification и AI.

## Проверки

Full/partial/empty across major analytics; mobile/a11y.

## Done when

Пользователь понимает, где данным можно доверять, а где их мало.

## Рекомендуемый commit

`feat(ui): surface data confidence`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## Plain-language confidence wording

`confidence`, `coverage`, `sufficient/limited/insufficient` are internal concepts.

UI says:
- `Данных достаточно для оценки`;
- `Вывод пока предварительный`;
- `Пока мало данных`;
- `За последние 14 дней дневник заполнен только за 4 дня`.

Do not expose raw status codes or English labels.
