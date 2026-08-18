# TASK 17. Свои продукты, recent/favorites и локальный поиск

- Фаза: **Core data**
- Приоритет: **17/93**
- Зависит от: `16`
- Рекомендуемый reasoning: **Medium**

## Цель

Ускорить ежедневное добавление знакомых продуктов и подготовить локальную выдачу до внешнего provider.

## In scope

Добавить/расширить:
- CRUD пользовательского продукта: название, КБЖУ на 100 г или порцию, serving, barcode при необходимости;
- recent foods;
- favorites;
- frequently used только если корректно и недорого выводится из истории;
- локальный search ranking: recent -> favorites -> own -> system -> local branded.

Autocomplete/search: debounce contract на frontend/API, минимальная длина запроса, cancellation/stale handling в UI позже, server-side limit/pagination. Сначала PostgreSQL normalization/trigram/full-text только по реальной необходимости. Не подключать отдельный search server.

Приватность пользовательских продуктов и cross-user isolation обязательны.

## Out of scope

Не делать Open Food Facts, camera scan, recipes/copy, dashboard/adherence или полный Nutrition UI.



## Проверки

CRUD own food, ownership, favorites, recent ordering, ranking local search, reasonable limits, index/query behavior. Проверить, что знакомый продукт можно быстро добавить через API без external source.

## Done when

Локальная продуктовая библиотека и поиск дают быстрый deterministic path без внешней зависимости.

## Рекомендуемый commit

`feat(food): add personal foods and fast local search`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
