# Integration tests

Сюда помещаются межсервисные сценарии, которым одновременно нужны backend,
Telegram bot или другие runtime-компоненты. Тесты отдельных приложений находятся
рядом с ними: `backend/tests` и `bot/tests`.

`test_migrated_stack.py` проверяет не ORM-схему из `Base.metadata.create_all`, а
PostgreSQL-схему, созданную Alembic. Затем он проходит по цепочке
`readiness -> SPA -> public API -> dev login -> authenticated API` без перехвата
HTTP-запросов frontend.

Обычный локальный pytest пропускает этот сценарий. Canonical-запуск находится в
`.github/workflows/ci.yml`: CI сначала собирает frontend и выполняет
`alembic upgrade head`, затем устанавливает `RUN_MIGRATED_STACK_TEST=1` и запускает
этот файл отдельно. Для ручного запуска нужны те же безопасные test-переменные и
отдельная PostgreSQL-база; production-базу использовать нельзя.
