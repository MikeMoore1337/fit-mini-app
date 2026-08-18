# TASK 44. Программы тренировок и каталог упражнений

- Фаза: **Core UX**
- Приоритет: **44/93**
- Зависит от: `05`, `23`, `25`, `28`, `29`, `30`, `35`, `38`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Сделать выбор, просмотр и редактирование программ понятными, а каталог упражнений - быстрым на mobile. Одновременно сделать работу с программами удобной для тренера и сократить повторную ручную работу.

## In scope

Переработать active program, list/templates, builder, days/exercises/order/editing, exercise catalog/search/filter и entry в shared exercise detail/technique, trainer/admin create states если существуют.

Пользователь различает active/template/own/coach-assigned. Builder группировать по дням; drag/drop только если безопасно и есть доступная альтернатива. Destructive actions отделены. Long forms разбиты на смысловые группы. Long names/media не ломают layout.


## Trainer program workflow

Для роли тренера отдельно проверить фактически поддерживаемый workflow и сделать его удобным. Где это уже поддерживается domain/API, trainer должен уметь:

- создавать и редактировать собственную программу;
- использовать существующий template;
- копировать/переиспользовать программу, если domain model это позволяет;
- добавлять/удалять/reorder упражнения;
- менять sets/reps/rest и другие существующие параметры;
- назначать программу закреплённому клиенту;
- изменять назначенную программу в рамках permissions;
- быстро переходить `client -> program -> client`.

Интерфейс должен ясно различать собственную trainer program/template и программу конкретного клиента.

Если reusable trainer templates/copying отсутствуют в backend/domain model, не имитировать их frontend-костылём - зафиксировать как product follow-up.

## Out of scope

Не менять program domain/permissions без необходимости, не добавлять AI generation/Trainer Copilot/paid video hosting/фиктивные упражнения и не создавать новую template/copy domain-функцию только ради UI.



## Проверки

Open active/template, create/edit, add/remove/reorder, long program, search/empty/error; trainer create/edit/assign flow, client -> program -> client, unrelated/former-client denial, если соответствующие возможности поддерживаются. Desktop/mobile Playwright + tests/typecheck/lint/build.

## Done when

Active program очевидна, builder не выглядит технической длинной формой, catalog быстро используется на телефоне, trainer program workflow требует минимум лишних переходов, trainer/client context понятен, permissions сохранены.

## Рекомендуемый commit

`feat(ui): redesign programs and trainer program workflows`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Split of responsibilities
Structured muscles/equipment/media приходят из `20/25`. Full expanded guide — task `46`. Deterministic recommender — task `25`, wizard — task `45`. Не реализовывать эти domain features frontend-костылями внутри builder.

## Backlog v3 integration: advanced programs
Builder поддерживает set semantics/supersets, program revisions/blocks и curated alternatives. Advanced controls — progressive disclosure.

## Final release integration: progression guidance

Task `58` дополняет Active Workout:
- suggestion не должна мешать logging;
- optional post-workout feedback короткий и dismissible;
- программа/веса не меняются автоматически.
