# TASK 46C.3. Cross-context auth and workout recovery remediation

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C.3/93 — после 46C.2**
- Зависит от: `46C.2`
- Canonical findings: `F-03`, `F-04`, `F-05`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$solution-architect`, `$security-engineer`, `$backend-engineer`, `$frontend-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Исключить ложный logout, потерю локальных workout mutations и невосстанавливаемый terminal retry в
multi-tab/WebView scenarios без ослабления server-side replay/idempotency protections.

## Owner-approved contract

- Queue/storage changes backward-compatible.
- Repeated finish собственной уже завершённой тренировки возвращает idempotent `200` с current
  completed representation.
- Repeated finish не создаёт повторных side effects.
- Frontend после finish/retry выполняет reconciliation и очищает локальный active state.

## Scope

1. Добавить надёжную cross-context refresh coordination для environments без Web Locks.
2. Перед refresh после ожидания coordinator повторно проверять token, полученный другим context.
3. Не ослаблять refresh rotation/replay revoke на backend.
4. Сделать enqueue/ack/rebase/clear active-workout queue атомарными между вкладками либо перейти на
   append-only per-context mutations с детерминированным merge.
5. Читать существующий persisted queue/snapshot format без потери данных; migration local storage
   должна быть versioned, recoverable и idempotent.
6. Repeated finish для completed owned workout возвращает current completed representation и не
   повторяет notifications, progression, timestamps или другие terminal side effects.
7. Frontend рассматривает initial success и idempotent retry одинаково: refetch/reconcile workout
   queries, clear queue/snapshot/rest state и показывает completed UI.
8. Ownership, scheduled-day validation и incomplete-set confirmation не ослаблять.

## Targeted regression

- Два contexts без `navigator.locks` одновременно refresh: один rotation, второй использует winner
  token, session family остаётся валидной.
- Actual replay attack по-прежнему отзывается server-side.
- Interleaved enqueue разных sets/operations из двух independent contexts не теряет mutation.
- Ack/rebase/clear не удаляют concurrent unapplied mutation.
- Legacy persisted queue/snapshot читаются после upgrade.
- Lost finish response -> retry -> `200` completed -> local state cleared.
- Repeated finish не повторяет side effects; чужая тренировка по-прежнему недоступна.

Запустить targeted frontend concurrency/storage/recovery tests, backend finish/idempotency/security
tests и небольшой integration contract test. Полный Playwright/backend suite без причины не запускать.

## Documentation

Синхронизировать `docs/web-auth.md` и `docs/offline-active-workout.md`, если изменятся documented
coordination, storage version или finish recovery semantics.

## STOP CONDITION

После закрытия `F-03`, `F-04`, `F-05`, targeted review, `git diff` и отдельного commit остановиться.
Не начинать `46C.4`.

## Рекомендуемый commit

`fix(workouts): make cross-context recovery lossless`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Указать browser compatibility, storage
migration behavior, checks, remaining limitations и commit hash.
