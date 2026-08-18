# TASK 45. Мастер подбора тренировочной программы

- Фаза: **Core UX**
- Приоритет: **45/93**
- Зависит от: `25`, `44`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Создать понятный пошаговый wizard поверх deterministic engine task `25`, не маскируя правила под AI.

## In scope

Entry points: Programs empty/new-user state и Templates/Programs; manual selection/create own остаётся доступен.

Steps: цель, уровень, силовых тренировок/неделю, место/оборудование, supported constraints. Product labels: Снижение жира, Рекомпозиция, Поддержание, Набор мышц, Увеличение силы. UI maps to canonical backend enums.

Result: recommended template, объяснение, schedule/frequency, equipment, level/goal, optional alternatives. Никаких fake percentages.

Flow: `wizard -> recommendation -> preview -> optional edit/copy through existing builder -> explicit start`. Back navigation не теряет answers. Prefill profile where trustworthy; wizard changes не обязаны молча менять profile.

No-match: изменить параметры / manual templates / create own. Mobile 360/390 first. Коротко объяснить, что подбор deterministic, не медицинская рекомендация.

## Out of scope

Не использовать AI, не генерировать content, не активировать автоматически, не блокировать manual builder и не делать injury diagnosis.

## Проверки

All goals/levels/frequencies, equipment, missing profile, back/forward, no-match, preview/edit/start, active program conflict, mobile/a11y.

## Done when

Пользователь может за несколько шагов получить, понять, изменить и явно начать подходящую template; ручной выбор сохранён.

## Рекомендуемый commit

`feat(ui): add deterministic program selection wizard`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Перед реализацией ещё раз проверить актуальный код, migrations, schemas, services, frontend и docs по текущему scope. Если функция уже реализована сильнее, чем предполагает task, не дублировать её: расширить существующую архитектуру или явно зафиксировать, что пункт уже закрыт.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: что уже существовало и было переиспользовано, изменения, ключевые файлы, migrations, formulas/permissions/content-source decisions, реально запущенные проверки, ограничения и commit hash.

## Beginner-friendly terminology

Program selection must not require knowledge of split/programming jargon.

If Full Body / Upper-Lower / Push-Pull-Legs appear, pair them with plain Russian explanation.
Ask about goal, experience, frequency, equipment and constraints in ordinary language.
