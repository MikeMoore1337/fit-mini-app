# TASK 15. Food domain foundation

- Фаза: **Core data**
- Приоритет: **15/93**
- Зависит от: `00`
- Рекомендуемый reasoning: **High**

## Цель

Создать независимый, нормализованный food domain как источник истины для пищевого дневника и будущих интеграций.

## In scope

Переиспользовать существующие модели либо создать минимально необходимые сущности для продукта: name, brand, barcode, energy/protein/fat/carbs/fiber при наличии, standard serving/unit, source/provenance/external id, system/branded/user type, user owner, trust/status, timestamps.

Пользовательские продукты приватны по умолчанию. Внешние данные логически различимы от внутренних/приватных. Создать/переиспользовать детерминированный расчёт КБЖУ по массе/порции.

Спроектировать воспроизводимый import pipeline для базовых системных продуктов. Не импортировать сомнительные значения: источник и лицензия должны быть проверены до фактического наполнения; если подходящий источник не выбран - реализовать pipeline без сомнительного seed.

Миграции безопасные, без выдуманного backfill. Добавлять только обоснованные uniqueness/index constraints.

## Out of scope

Не делать food diary entries/UI, recent/favorites, recipes, external HTTP provider, camera scan, dashboard, adherence.



## Проверки

Unit tests пересчёта КБЖУ/порций, validation, ownership user foods, source/barcode constraints, migration tests/upgrade path. Обновить долгосрочную food-domain документацию только по архитектуре/правилам, не копируя реализацию.

## Done when

Есть единый food foundation, независимый от конкретного API, с provenance/privacy и тестируемыми расчётами.

## Рекомендуемый commit

`feat(food): establish food domain foundation`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
