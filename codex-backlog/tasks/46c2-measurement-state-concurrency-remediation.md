# TASK 46C.2. Measurement state and concurrency remediation

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C.2/93 — после 46C.1**
- Зависит от: `46C.1`
- Canonical findings: `F-01`, `F-02`, `F46B-07`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$solution-architect`, `$data-engineer`, `$backend-engineer`, `$frontend-engineer`, `$python-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Создать одну серверную chronology/concurrency политику замеров и гарантировать согласованность
current nutrition/progress state и frontend dependent queries.

## Owner-approved contract

- Новые future-dated measurements запрещены относительно timezone владельца данных.
- Existing future rows не удаляются, но исключаются из current/latest/nutrition derivation.
- Historical measurements разрешены.
- После create/update/delete current state пересчитывается по последнему допустимому measurement.
- Trainer defaults используют timezone клиента.
- Concurrent same-day save использует atomic PostgreSQL upsert, last committed write wins, одну row
  и никогда не отдаёт unhandled 500.

## Scope

1. Выделить единый measurement domain/service для personal и coach create/update/delete.
2. Валидировать `measured_on <= today_for_user(owner)` на trusted backend boundary.
3. Не удалять и не переписывать existing future rows. Исключить их из current/latest progress,
   nutrition input и других authoritative current consumers; historical export сохраняет rows.
4. После любого create/update/delete выбирать последний допустимый weight-bearing measurement и
   согласованно пересчитывать текущий nutrition/profile-derived state через существующую
   authoritative формулу. Не дублировать формулу в router/frontend.
5. Если допустимого weight-bearing measurement не осталось, использовать текущий документированный
   profile/nutrition fallback; не придумывать значение и не удалять nutrition target.
6. Реализовать PostgreSQL atomic upsert для `(user_id, measured_on)` с last committed write wins.
   SQLite/test behavior должен быть семантически совместим и не скрывать PostgreSQL race.
7. Trainer UI/API default date вычислять по timezone клиента, не браузера тренера.
8. Централизовать query-key factories/invalidation для measurements, personal progress, trainer
   analytics и nutrition/adherence summaries, реально зависящих от mutation.

## Migration и compatibility

- Existing unique constraint переиспользовать; новая migration не ожидается.
- Никакого destructive backfill existing future rows.
- API должен вернуть controlled validation error для новой future date.
- Если обнаружится необходимость schema change, сначала подготовить forward-fix/rollback и не
  запускать migration против production.

## Targeted regression

- Personal и coach future create/update отклоняются по owner timezone boundary.
- Historical save разрешён, но не заменяет current nutrition input при более новом допустимом весе.
- Existing future fixture не появляется в latest/current derivation и не удаляется.
- Create/update/delete последнего допустимого weight row детерминированно обновляет current state.
- Trainer/client timezone midnight boundary.
- Два concurrent personal writes и client+trainer writes в isolated PostgreSQL дают одну row,
  last committed values и ни одного 500.
- Measurement/nutrition mutations refetch нужные personal/trainer dependent summaries.
- Ownership и unrelated trainer negative paths сохраняются.

Запустить targeted backend domain/API/PostgreSQL concurrency tests, frontend component/query tests,
typecheck/lint и generated API drift при изменении schema. Полный suite без необходимости не запускать.

## Documentation

Обновить только documentation chronology/timezone/current-state и API validation, если текущий
durable contract станет неточным.

## STOP CONDITION

После закрытия `F-01`, `F-02`, `F46B-07`, targeted review, `git diff` и отдельного commit
остановиться. Не начинать `46C.3`.

## Рекомендуемый commit

`fix(progress): enforce measurement chronology and atomic writes`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Отдельно сообщить migration/data
implications, tests on PostgreSQL, compatibility behavior и commit hash.
