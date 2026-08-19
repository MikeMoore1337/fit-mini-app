# TASK 46C. Критические технические исправления по результатам 46A/46B

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C/93 - выполнить после owner review tasks 46A/46B**
- Зависит от: `46A`, `46B`, явное подтверждение владельцем списка исправлений
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$commercial-product-builder`, `$solution-architect`, `$security-engineer`, `$privacy-engineer`, `$data-engineer`, `$backend-engineer`, `$frontend-engineer`, `$python-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Исправить только подтверждённые владельцем критические findings из tasks `46A` и `46B` до продолжения функционального backlog.

Эта task не является разрешением на общий refactor. Она закрывает production-риски, которые уже существуют или будут системно размножаться в tasks `47-93`.

## Preconditions

Перед началом должны быть доступны:

- `.artifacts/codex-audits/46a-production-quality/`;
- `.artifacts/codex-audits/46b-security-privacy-data/`;
- явный owner-approved список finding IDs в текущем запросе Codex.

Если owner-approved список отсутствует, не начинать изменения. Кратко перечислить кандидатов и остановиться.

## Разрешённый scope

Исправлять только:

- `P0` и `P1`;
- cross-user/client data leakage;
- privilege escalation или auth bypass;
- secret/token exposure;
- data-loss/data-corruption risk;
- unsafe migration/data invariant;
- подтверждённый lost update, duplicate write или race condition критического flow;
- сломанный API contract/core recovery path;
- системный `P2`, который неизбежно будет скопирован в новые tasks и явно одобрен владельцем.

## Запрещённый scope

Не делать:

- Design V2 или любые визуальные изменения, кроме необходимых security/error states;
- новые product features;
- косметический refactor;
- массовое переименование;
- смену framework/ORM/state manager;
- speculative performance optimization;
- новую инфраструктуру без необходимости;
- исправление `P3`;
- nice-to-have observability, которая относится к task `92`;
- заранее реализовывать tasks `47-93`.

## Порядок работы

### 1. Зафиксировать scope

Для каждого approved finding записать:

- finding ID;
- affected subsystem;
- минимальный fix;
- regression evidence;
- возможную migration/compatibility стоимость;
- rollback/forward-fix план, если затрагиваются данные.

Если approved findings затрагивают несколько независимых крупных подсистем и не помещаются в один безопасный change set, не смешивать их. Остановиться и предложить декомпозицию на `46C.1`, `46C.2` и т.д. с отдельными commits/checks.

### 2. Реализация

- исправлять root cause, а не маскировать симптом;
- сохранять backward compatibility, где она нужна;
- authorization проверять server-side;
- migrations делать воспроизводимыми и безопасными для существующих данных;
- retry/idempotency вводить только там, где операция безопасно повторяема;
- не раскрывать чувствительные details в client errors/logs;
- не ухудшать core flow без доказанной security-причины.

### 3. Тесты

Добавить targeted regression tests пропорционально риску:

- unit/domain;
- API/integration;
- authorization negative tests;
- migration/data compatibility;
- concurrency/idempotency;
- frontend recovery/error state;
- Web/TMA auth continuity, если затронуто.

Не запускать полный suite автоматически, если это запрещено `AGENTS.md`. Выполнить профильные проверки для каждого изменённого subsystem.

### 4. Независимый review

Перед завершением применить `$code-reviewer` к фактическому diff.

Повторно проверить:

- correctness;
- data integrity;
- security/privacy;
- compatibility;
- tests;
- accidental scope;
- sensitive logging;
- migration safety.

## Документация

Обновить durable `docs/` только когда fix меняет:

- architecture;
- API contract;
- security/privacy constraint;
- environment/config;
- migration/deployment/rollback procedure;
- документированное пользовательское поведение.

Raw audit reports не переносить в публичные docs.

## STOP CONDITION

После закрытия owner-approved списка остановиться.

Не переходить к Design V2 или task `47`.
Не исправлять новые findings без отдельного owner approval, кроме очевидной регрессии, внесённой текущим change set.

Если approved blockers отсутствуют, не создавать искусственные изменения. Зафиксировать `no remediation required`, проверить `git diff` и завершить task без commit.

## Done when

- каждый approved finding закрыт или явно заблокирован с доказанной причиной;
- root cause исправлен;
- соответствующие regression tests проходят;
- migrations/data changes имеют безопасную стратегию;
- независимый code review не выявил незакрытых P0/P1;
- нет unrelated refactor/feature work;
- документация синхронизирована только там, где это нужно;
- commits логически разделены согласно `AGENTS.md`.

## Рекомендуемый commit

Для одного однородного change set:

`fix(core): remediate approved production blockers`

Для нескольких одобренных независимых stages использовать отдельный логический commit на stage.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy. В финальном отчёте перечислить finding IDs, исправления, ключевые файлы, migrations/config, реально запущенные проверки, review findings, ограничения и commit hashes.
