# Codex prompt template v10

Use one fresh Codex chat per task. Select model/reasoning manually according to `MODEL_SELECTION.md`.

```text
Выполни `codex-backlog/tasks/NN-task-name.md`.

Соблюдай `AGENTS.md`, `codex-backlog/GLOBAL_RULES.md` и полный task lifecycle.
Перед любой visual work прочитай `codex-backlog/ACTIVE_DESIGN_SOURCE.md`.
Для tasks `49A-49G` также соблюдай `codex-backlog/DESIGN_ALTERNATIVES_EXPLORATION_CONTRACT.md`.
Для client-facing task соблюдай `codex-backlog/MOBILE_TMA_FIRST_CONTRACT.md` и mobile/TMA acceptance текущей задачи.

Перед началом проверь `feature/yfc-platform-v2`.
Открой только текущую task, её primary role и core skills. Conditional skills - только по фактическому trigger.
Выполни только дополнительные lifecycle-роли, явно указанные task.
Не запускай полный audit/suite и не подключай новые роли "для надёжности" без требования task/доказанного риска.
Только BLOCKER/HIGH блокируют завершение; non-blocking findings не расширяют scope.
Не deploy production. Не переходи к следующей task.
```

## Current start

Task `49` была остановлена владельцем и продолжается как resume:

```text
Выполни `codex-backlog/tasks/49-trainer-context-comments-experience.md`.
```

Сначала соблюдать её `Resume contract` и сохранить неидентифицированные пользовательские изменения worktree. После её завершения следующая task - `49A`.
