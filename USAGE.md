# Использование YFC Codex lifecycle v3

Архив уже содержит согласованный набор:

```text
AGENTS.md
.agents/
  roles/
  skills/
  references/
codex-backlog/
  GLOBAL_RULES.md
  TASK_EXECUTION_LIFECYCLE.md
  tasks/
    done/
```

Дополнительные snippet-файлы не нужны. Содержимое архива копируется в корень репозитория с сохранением структуры.

## Обычный запуск

Для task достаточно короткого prompt:

```text
Выполни `codex-backlog/tasks/<task>.md`.

Соблюдай `AGENTS.md`, `codex-backlog/GLOBAL_RULES.md`
и полный task lifecycle.

Все предыдущие tasks считаются выполненными.
Не переходи к следующей task.
```

Task сама задаёт primary role, core skills, conditional skills и дополнительные lifecycle-роли. Не перечисляй их вручную в prompt.

## Текущая task — 56

Подтверждённый выполненный диапазон `00-55` хранится в `codex-backlog/tasks/done/`. Следующий запуск:

```text
Выполни `codex-backlog/tasks/56-unified-weekly-review-adaptive-energy.md`.

Соблюдай `AGENTS.md`, `codex-backlog/GLOBAL_RULES.md`
и полный task lifecycle.

Все предыдущие tasks считаются выполненными.
Не переходи к следующей task.
```

После task `56` следующей будет `57`, но она выполняется в отдельной сессии.

## Resource-aware схема

```text
обычная task:
primary role + core skills
  -> targeted checks
  -> только явно указанный independent review
  -> BLOCKER/HIGH fix при наличии
  -> targeted recheck
  -> только явно указанная QA
  -> commit

MEDIUM/LOW/NIT/OUT_OF_SCOPE
  -> non-blocking follow-up
  -> без нового workstream
```

Conditional skill загружается только после фактического trigger. Для обычного review/QA используется base skill роли и максимум 1-2 профильных skills.
