# TASK 19. Опциональный внешний food provider

- Фаза: **Core integration**
- Приоритет: **19/93**
- Зависит от: `15`, `17`
- Рекомендуемый reasoning: **High**

## Цель

Добавить заменяемый внешний каталог брендированных продуктов, не делая его обязательным для core app.

## In scope

Перед реализацией проверить актуальную официальную документацию Open Food Facts: API, rate limits, User-Agent, license/ODbL, attribution, caching/share-alike implications. Не доверять значениям из master без проверки.

Создать нейтральную `FoodProvider`-подобную абстракцию `search/get_by_barcode` в стиле проекта. Приоритет: local DB -> optional provider. Provider можно выключить/заменить без изменения domain logic.

Соблюдать provenance/атрибуцию и не смешивать ODbL данные с приватными user data так, чтобы происхождение терялось. Timeout, ограниченный safe retry, 429/5xx/network handling, понятный fallback. Не добавлять Redis, если он не нужен и не существует.

Добавить только реально нужные env vars; app нормально запускается с provider disabled.

## Out of scope

Не делать camera UI, не делать OFF обязательным, не использовать FatSecret как dependency, не делать unit tests зависимыми от реального API.



## Проверки

Fake/mock provider tests: local-first, search, barcode provider contract, timeout, 429/5xx, malformed response, disabled provider, fallback, provenance. Реальный API - только opt-in smoke, если уместно.

## Done when

Core diary полностью работает при недоступном provider; внешний каталог изолирован, заменяем и лицензионно документирован.

## Рекомендуемый commit

`feat(food): add optional external food provider`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
