# TASK 00. Read-only технический baseline продукта

- Статус: **COMPLETED — user-confirmed before backlog v3**

- Фаза: **Foundation**
- Приоритет: **00/93**
- Зависит от: нет
- Рекомендуемый reasoning: **High**

## Цель

Снять единый технический baseline существующего репозитория до Food/AI/redesign изменений и подготовить короткую карту точек интеграции. Этот audit заменяет повторный полный обзор репозитория в следующих задачах.

## In scope

Провести только read-only анализ:

- `AGENTS.md`, `README.md`, релевантный `docs/`, последние коммиты;
- frontend routing/navigation, shared UI/theme, Web/Telegram platform adapters;
- auth/RBAC, trainer-client relation;
- backend API/models/schemas/services/repositories/migrations;
- nutrition/КБЖУ, workout, progress, profile;
- timezone/user-day semantics;
- tests, logging, HTTP clients, cache/Redis/background jobs, feature flags;
- существующие food/chat/AI abstractions, если уже есть.

Составить компактную таблицу `Уже есть / Расширить / Создать` и карту реальных файлов/сервисов для задач 03-27. Отдельно отметить риски ownership, N+1, миграций и дублирования бизнес-логики.

## Out of scope

Не менять tracked files, не делать миграции, не исправлять найденные дефекты, не создавать food/AI/UI код. Не писать большой audit report в `docs/`.



## Проверки

Сохранить при необходимости приватный рабочий отчёт в `.artifacts/codex-audits/platform-baseline/`. Проверить `git diff` и убедиться, что tracked files не изменены.

## Done when

Следующие tasks могут начинаться с конкретных найденных точек интеграции, а не с повторного полного аудита. Commit не создаётся, если tracked files не менялись.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
