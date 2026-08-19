---
name: python-engineer
description: >
  Implement or refactor Python code using the repository's supported Python version, typing,
  tests, linting, async conventions and project tooling. Use whenever Python source is materially
  changed; pair with domain-specific skills when the task is primarily backend, data or QA.
---

# python-engineer

Используй этот skill при изменении Python-кода.

## Сначала изучи проект

Определи по репозиторию:

- поддерживаемую версию Python;
- package/dependency manager;
- `pyproject.toml`/tool configuration;
- test runner и project wrappers;
- lint/format/type-check tools;
- async/sync модель;
- существующие package/module conventions.

Не подменяй проектные команды привычными командами, если репозиторий уже предоставляет wrappers
или scripts.

## Реализация

- используй возможности версии Python, которую реально поддерживает проект;
- сохраняй meaningful typing и не расширяй типы до `Any` без причины;
- предпочитай явную обработку ошибок и детерминированное освобождение ресурсов;
- не блокируй async event loop синхронным I/O без конкретного основания;
- следуй существующим framework/ORM/library patterns вместо параллельных абстракций;
- не добавляй зависимость, если текущий стек разумно решает задачу.

## Проверки

Используй существующие команды проекта. Для каждого этапа запускай минимально релевантный набор,
а перед завершением существенной Python-задачи - более широкий набор проверок затронутой области.

Типичные категории, если они настроены в проекте:

- unit/integration tests;
- lint;
- formatting check;
- static type checking;
- package/build verification.

Не утверждай, что проверка прошла, если команда фактически не запускалась.

## Артефакты

Соблюдай repository-wide правила для caches, coverage, test artifacts и temporary files.
Не создавай новые scratch paths в корне проекта, если проект уже определяет место для артефактов.
