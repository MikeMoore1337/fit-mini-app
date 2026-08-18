# TASK 16. Пищевой дневник - backend/API

- Фаза: **Core data**
- Приоритет: **16/93**
- Зависит от: `15`
- Рекомендуемый reasoning: **Medium/High**

## Цель

Сделать полноценный локальный приватный пищевой дневник, который работает без внешнего provider.

## In scope

Поддержать пользовательскую дату, breakfast/lunch/dinner/snacks, food entries, массу/порцию, CRUD и агрегаты записи/meal/day. Целевые КБЖУ получать из существующего сервиса, не дублировать формулы.

API строить через service/domain layer, не вокруг таблиц. Соблюдать validation, status codes, pagination где нужна, auth/ownership и безопасные ошибки.

Критично: пользовательский день по timezone, а не только UTC. Проверить полночь, прошлую дату, будущую дату согласно явно выбранному правилу и одинаковую семантику Web/Telegram. Пищевой дневник считать приватным.

## Out of scope

Не делать основной UI, favorites/recent, recipes/copy, external provider, scanner, Today UI, adherence.



## Проверки

CRUD, изменение количества, meal/day aggregation, nutrition targets from existing service, cross-user isolation, timezone boundaries, empty day, invalid values, API contracts, основные query count/N+1 проверки.

## Done when

Локальный дневник полностью работает через БД, корректно агрегирует КБЖУ по пользовательскому дню и не зависит от внешнего каталога.

## Рекомендуемый commit

`feat(food): add nutrition diary backend`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
