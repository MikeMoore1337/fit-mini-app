# TASK 46A. Аудит production-качества выполненного scope 00-46

- Фаза: **Retrospective production gate**
- Приоритет: **46A/93 - выполнить сразу после подтверждённой task 46**
- Зависит от: `46`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$commercial-product-builder`, `$solution-architect`, `$code-reviewer`, `$backend-engineer`, `$frontend-engineer`, `$python-engineer`, `$data-engineer`, `$qa-engineer`

## Цель

Провести ограниченный read-only аудит фактически реализованного продукта после tasks `00-46` по актуальным production skills.

Задача не повторяет старые tasks и не требует переписывать рабочие подсистемы. Нужно найти только реальные системные проблемы, которые:

- уже нарушают correctness/reliability;
- создают риск потери или повреждения данных;
- будут размножаться в tasks `47-93`;
- делают будущую разработку заметно дороже или небезопаснее;
- противоречат текущей архитектуре, API-контрактам или тестовым инвариантам.

## Критические ограничения

- Только read-only анализ.
- Не менять production-код, migrations, schemas, styles, tests или docs.
- Не выполнять tasks `00-46` повторно.
- Не предлагать rewrite проекта, смену стека или большой рефакторинг ради чистоты.
- Не проводить глубокий security/privacy аудит - это отдельная task `46B`.
- Не проводить визуальный редизайн - это отдельный блок `46D-46I`.
- Не делать полный performance/observability/release audit - это остаётся в tasks `75`, `92`, `93`.

## Источники истины

Использовать:

- текущий код;
- Git history и commits, относящиеся к завершённым tasks;
- актуальный `docs/`;
- root `AGENTS.md`;
- `codex-backlog/GLOBAL_RULES.md`;
- профильные tests и configuration.

Старые task-файлы открывать только точечно, когда без них нельзя установить исходный acceptance contract.

## In scope

### 1. Архитектура и границы ответственности

Проверить:

- не дублируется ли доменная логика между frontend/backend/services/repositories;
- нет ли нескольких источников истины для формул, статусов и derived state;
- соблюдаются ли фактические module/domain boundaries;
- нет ли god-components/god-services и циклических зависимостей, которые уже мешают развитию;
- не появились ли локальные обходы существующих abstractions;
- соответствуют ли новые части текущему deployment/runtime устройству проекта.

### 2. API и contracts

Проверить:

- request/response contracts и validation;
- backward compatibility завершённых flows;
- normalized error behavior;
- pagination/filter/sort semantics, где применимо;
- server-side enforcement критических бизнес-правил;
- double submit, duplicate requests, retries и idempotency;
- stale requests/race conditions на frontend;
- сохранение recoverable input после ошибок.

### 3. Данные и migrations

Проверить:

- ownership и связи данных;
- DB constraints и application invariants;
- transaction boundaries;
- nullable/default/backfill semantics;
- unsafe migrations и несовместимость со старыми данными;
- cascade/orphan behavior;
- timezone/user-day semantics;
- query patterns, N+1 и unbounded operations;
- согласованность units/precision для питания, тренировок и прогресса.

### 4. Надёжность и ошибки

Проверить:

- partial failure;
- swallowed exceptions;
- retries небезопасных операций;
- network/provider failures;
- offline active-workout recovery;
- lost updates и duplicate writes;
- cleanup временных данных;
- понятные loading/error/empty/stale/retry states для завершённых UI flows.

### 5. Тестовая стратегия

Проверить пропорционально риску:

- критические unit/integration/API/component/e2e tests;
- negative/error/recovery branches;
- migration/data compatibility tests;
- regression tests для ранее исправленных существенных дефектов;
- отсутствие тестов, которые проверяют implementation detail вместо пользовательского/доменного поведения;
- flaky или бессмысленно дублирующее покрытие.

Не запускать полный suite автоматически. Использовать существующие targeted checks только для подтверждения конкретных выводов.

### 6. Документация и operability baseline

Проверить только опасный drift:

- setup/env/commands;
- API contracts;
- migrations;
- архитектурные ограничения;
- documented user-visible behavior;
- logging/error paths, достаточные для диагностики критического сбоя.

Полный observability и production readiness остаются в task `92`.

## Классификация findings

Каждый finding должен содержать:

- severity: `P0`, `P1`, `P2`, `P3`;
- конкретный файл/подсистему;
- воспроизводимый сценарий или доказательство;
- реальное последствие;
- минимальное исправление;
- категорию решения:
  1. `fix in 46C`;
  2. `already covered by future task`;
  3. `post-release improvement`;
  4. `not a defect / no action`;
- риск размножения проблемы в будущих tasks.

Не повышать severity из-за субъективной архитектурной эстетики.

## Артефакт

Сохранить приватный отчёт в:

`.artifacts/codex-audits/46a-production-quality/`

Минимальный состав:

- `summary.md`;
- `findings.md`;
- `coverage.md`;
- при необходимости targeted test output.

Не переносить сырой audit report в публичный `docs/`.

## STOP CONDITION

После аудита обязательно остановиться.

Не исправлять findings.
Не переходить к task `46B` или `46C`.
Не создавать commit, если tracked files не менялись.

## Done when

- scope `00-46` проверен по актуальным production-критериям без повторной реализации;
- findings доказательны и приоритизированы;
- отделены реальные blockers от будущих/nice-to-have улучшений;
- сформирован короткий список кандидатов для owner-approved task `46C`;
- `git diff` не содержит tracked changes.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy. В финальном сообщении кратко указать coverage, число findings по severity, список кандидатов для `46C`, реально запущенные проверки и путь к приватным артефактам.
