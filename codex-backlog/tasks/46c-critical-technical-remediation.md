# TASK 46C. Umbrella: owner-approved technical remediation gate

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C/93 — umbrella после 46B1, завершить до 46D**
- Зависит от: `46A`, `46B`, `46B1`, явное owner decision от 2026-08-19
- Состоит из: `46C.1`, `46C.2`, `46C.3`, `46C.4`, `46C.5`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Назначение umbrella

Task `46C` больше не является одним implementation change set. Она фиксирует утверждённый
владельцем remediation scope и порядок пяти независимых tasks. Саму umbrella-task отдельно не
реализовывать и не использовать как разрешение смешать findings в одном commit.

Каждая дочерняя task выполняется:

- в отдельной Codex-сессии;
- только в `feature/yfc-platform-v2`;
- после проверки своей зависимости;
- с профильными checks;
- с отдельным логическим commit;
- с обязательной остановкой до следующей task.

## Утверждённый allowlist

Только следующие canonical findings входят в remediation gate:

- `F46B-01`, `F46B-02`;
- `F-01`, `F-02`, `F46B-07`;
- `F-03`, `F-04`, `F-05`;
- `F46B-03`, `F46B-04`;
- `F46B-05`, `F46B-06`.

Все остальные findings не входят в task `46C` без нового явного owner approval.

## Утверждённая декомпозиция и порядок

```text
46B1 owner decision
  -> 46C.1 Root/Admin/Trainer authorization boundaries
  -> 46C.2 Measurements, concurrency and dependent state
  -> 46C.3 Cross-context auth/workout recovery
  -> 46C.4 Account export and browser privacy lifecycle
  -> 46C.5 HTTP limits and safe logging boundary
  -> 46D Design V2 baseline audit
```

| Task | Canonical findings | Результат |
|---|---|---|
| 46C.1 | `F46B-01`, `F46B-02` | независимые Root/Admin/Trainer capabilities и least-privilege boundaries |
| 46C.2 | `F-01`, `F-02`, `F46B-07` | единая chronology/concurrency политика замеров и согласованные dependent queries |
| 46C.3 | `F-03`, `F-04`, `F-05` | безопасные cross-context refresh/queue и idempotent workout finish recovery |
| 46C.4 | `F46B-03`, `F46B-04` | полный versioned export и browser-storage lifecycle |
| 46C.5 | `F46B-05`, `F46B-06` | согласованные body limits, safe diagnostic logging и корректный cache assertion |

## Future routing вне 46C

- `F46B-08` закреплён за task `92` с отдельными retention/access/restore acceptance criteria.
- `F-06` закреплён за task `93` с real migrated PostgreSQL API+UI critical flows.
- `F46B-09` закреплён за task `93` с SQLite/PostgreSQL account-deletion regression.

## Общие ограничения

- Не добавлять findings сверх allowlist.
- Не начинать Design V2 до завершения всех `46C.1`–`46C.5`.
- Не объединять commits дочерних tasks.
- Не deploy, не использовать production data и не запускать production migrations.
- Не ослаблять auth, replay protection, cache headers, validation, tests или privacy boundaries.
- Raw audit reports остаются в `.artifacts/` и не переносятся в public docs.

## Completion gate

Umbrella `46C` считается завершённой только когда:

- каждая task `46C.1`–`46C.5` завершена отдельным commit;
- каждый approved finding имеет regression evidence;
- migration/config/compatibility effects каждой task явно отражены в её отчёте;
- нет незакрытых P0/P1 или approved data-loss/privacy blockers;
- выполнен финальный targeted review совокупного remediation scope;
- task `46D` запускается только после подтверждения всех пяти commits/checks.

## STOP CONDITION

Этот файл — coordination contract. Не реализовывать application changes при выполнении umbrella.
Запускать только конкретную следующую дочернюю task и останавливаться после неё.

## Процесс

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не создавать и не переключать ветки, не
merge/rebase, не deploy и не переходить автоматически к следующей task.
