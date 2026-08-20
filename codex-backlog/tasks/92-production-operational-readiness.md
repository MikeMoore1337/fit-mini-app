# TASK 92. Production operational readiness

- Фаза: **Release Hardening**
- Приоритет: **92/93**
- Зависит от: `72`, `73`, `74`, `75`, `86`, `87`, `88`, `89`, `90`, `91`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$platform-engineer`, `$observability-engineer`, `$security-engineer`, `$privacy-engineer`, `$performance-engineer`, `$release-manager`, `$qa-engineer`, `$technical-writer`

## Цель

Подготовить приложение к реальной эксплуатации после завершения core product и AI:
ошибки должны быть диагностируемы, данные восстанавливаемы, deploy — проверяемым,
а падение внешнего сервиса не должно ломать весь продукт.

## In scope

1. Это readiness task, НЕ production deploy.
Не выполнять destructive operations с production data.

2. Health/readiness:
   - backend liveness;
   - DB readiness;
   - critical dependency status только там, где это действительно blocking;
   - AI/external food providers НЕ должны делать core app unhealthy, если они optional.

3. Configuration validation:
   - required production env vars;
   - incompatible flags;
   - secrets never logged;
   - fail-fast там, где безопаснее fail-fast.

4. Structured operational logging:
   - request/correlation id;
   - useful error context;
   - PII redaction;
   - no food diary contents;
   - no exact measurements unless strictly necessary and protected;
   - no AI raw conversation text in ordinary logs;
   - no tokens/secrets.

5. Error visibility:
   - frontend unexpected error boundary/reporting path;
   - backend 5xx aggregation;
   - background jobs/notifications failures;
   - provider failures.
Prefer existing/free/self-hosted capabilities; не добавлять обязательную paid observability dependency.

6. Database:
   - backup procedure;
   - restore procedure;
   - TEST restore on non-production/local/staging-equivalent data;
   - migration runbook;
   - failed migration recovery/rollback strategy where technically feasible;
   - schema backup/compatibility notes.

7. Deploy runbook:
   - build;
   - migrations;
   - start;
   - health/readiness;
   - targeted smoke;
   - rollback decision path.
Не выполнять production deployment автоматически.

8. External dependency degradation:
   - Open Food Facts/external catalogue unavailable;
   - AI provider unavailable/all free providers exhausted;
   - Telegram API issue;
   - OAuth provider issue.
Core unaffected areas должны продолжать работать.

9. Background jobs:
   - notification/reminder jobs observable;
   - idempotency;
   - stale job handling;
   - timezone processing.

10. Storage/local/offline:
   - active workout sync failures diagnosable;
   - export artifacts expire;
   - no orphaned temp files outside configured artifact/storage paths.

11. Security operations:
   - rate limiting/current abuse protections verified;
   - admin/root sensitive actions audit;
   - no debug/dev auth accidentally enabled in production config.

12. Capacity sanity:
   - use existing performance results;
   - no artificial load test against production;
   - define practical concurrency/resource assumptions and bottlenecks.

13. Documentation:
   - concise operator runbook in durable `docs/`;
   - incident checklist;
   - backup/restore;
   - deploy/rollback;
   - provider degradation.

14. Design V2 operational states:
   - frontend error boundary, degraded-provider и recovery UI переиспользуют фактические Approved Design V2 components/tokens;
   - readiness task не создаёт отдельный аварийный visual language и не меняет утверждённый дизайн;
   - targeted smoke использует реальные production-build light/dark Web/Mobile/TMA states и сохраняет evidence по conventions проекта.

## Carried finding acceptance: F46B-08

Task 92 обязана закрыть routed finding `F46B-08`, а не ограничиться общим backup/logging review.

Acceptance criteria:

- составлена sensitivity/retention/access matrix для audit events, API/worker logs и backups;
- для каждого класса указан конкретный TTL либо документированное обоснованное исключение;
- определены deletion/anonymization semantics для audit metadata после account deletion;
- определены backup retention, access controls и процедура удаления expired copies;
- non-production restore drill проверяет поведение ранее удалённых accounts: применяется
  tombstone/reconciliation либо явно ограниченное и документированное backup exception;
- восстановление не делает удалённый account активным незаметно и без operator decision;
- user/operator disclosure описывает реальные ограничения lifecycle без raw sensitive data;
- checks подтверждают retention job/policy boundaries и не удаляют необходимое security evidence.

Без этих критериев `F46B-08` и task 92 не считаются закрытыми.

## Out of scope

Не deploy в production.
Не modify production DB directly.
Не purchase monitoring services.
Не build Kubernetes/platform rewrite.
Не overengineer HA before actual demand.
Не collect sensitive telemetry for convenience.

## Проверки

Health/readiness; missing config; redaction; DB backup+non-prod restore;
migration failure path; frontend/backend error path; background job failure;
AI unavailable; food provider unavailable; Telegram/OAuth degradation;
dev-auth production guard; export cleanup; offline sync error observability.

## Done when

Есть проверенный операционный путь deploy/diagnostics/backup/restore/degradation,
и отсутствие optional provider не превращает весь YFC в недоступный сервис.

## Рекомендуемый commit

`chore(release): add production readiness safeguards`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными.
Текущий код, Git history и актуальный `docs/` — source of truth по их результатам.

Не проводить повторный полный аудит репозитория.
Не перечитывать все предыдущие task-файлы.
Не читать весь `codex-backlog/masters/` без необходимости.

Если текущий task явно относится к одному master-документу,
прочитать только этот master.

Если предыдущий audit уже исследовал нужную область и результат доступен,
переиспользовать его; точечно перепроверять только факты, которые могли измениться.

Сначала прочитать текущий task, затем исследовать только релевантный набор файлов
и подсистем, необходимый для корректного выполнения задачи.

Если требуемая функциональность уже существует:
- не реализовывать её заново;
- переиспользовать текущую архитектуру;
- закрыть только реальные gaps.

Не расширять scope самостоятельно.

Если для выполнения нужен крупный architectural change вне scope:
- не начинать его автоматически;
- зафиксировать follow-up;
- выполнить безопасную часть текущего task, если возможно.

Работать только в текущей feature-ветке.

Не:
- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- переходить к следующему task.

После реализации:
1. только профильные проверки согласно `AGENTS.md`;
2. не запускать полный test suite без необходимости;
3. проверить `git diff`;
4. создать один логический commit при tracked changes;
5. краткий финальный отчёт: reused / changed / files / migrations-config / checks / follow-ups / commit hash.
