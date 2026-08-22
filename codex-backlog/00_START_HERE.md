# Your Fitness Coach - backlog первого публичного релиза v10

Эта версия сохраняет production-качество, но делает lifecycle resource-aware: task сама задаёт минимально необходимый набор ролей/skills, review имеет конечный scope и только `BLOCKER/HIGH` блокируют завершение.

## Текущее состояние

- tasks `00-48` завершены;
- task `49` остановлена владельцем во время review-driven UI refinement и сейчас является **RESUME** task;
- её backend/functionality до остановки уже считались выполненными; продолжить нужно только текущий UI refinement по `Resume contract`;
- Design V2 остаётся текущим production source of truth;
- после завершения/commit task `49` следующая task - `49A`.

## Текущая задача

```text
49-trainer-context-comments-experience.md
```

Не начинать `49A`, пока `49` не завершена. Не сбрасывать текущий worktree целиком.

## Design alternatives flow после task 49

```text
49A  targeted brief/current-state delta
49B  exactly three cross-surface directions + renders
49C  compare V2/A/B/C + owner selection

KEEP_V2_UNCHANGED
  -> skip 49D-49F
  -> 49G closure

V2.1 / A / B / C / explicit hybrid
  -> 49D final responsive specification
  -> owner approval
  -> 49E production-realistic pilot
  -> owner manual test
  -> 49F final owner approval
  -> 49G conditional rollout + backlog alignment

49G -> 50A mobile/TMA quality foundation
```

## Что изменено в v10

- `Рекомендуемые skills` = core, `Условные skills` = только по trigger.
- `Основная роль` + `Дополнительные роли lifecycle` = точный маршрут task.
- Нет автоматической цепочки researcher/reviewer/QA.
- Первый independent review - единственный full review; после blocking fix только targeted recheck.
- `MEDIUM/LOW/NIT/OUT_OF_SCOPE` не блокируют commit и не создают новый backend/data/platform scope.
- Для tasks `49-79` роли и skills пересмотрены по фактическому контексту каждой task.

Подробности: `TASK_EXECUTION_LIFECYCLE.md`, `SKILL_ASSIGNMENT_MATRIX.md`, `BACKLOG_V10_CHANGELOG.md`.
