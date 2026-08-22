# Использование YFC Codex lifecycle v2

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

## Текущая task 49 - resume

После обновления этих правил продолжай остановленную task отдельной сессией тем же коротким prompt для:

```text
codex-backlog/tasks/49-trainer-context-comments-experience.md
```

Codex должен сначала прочитать `Resume contract` и текущий незакоммиченный diff. Он не должен продолжать review-induced migration/idempotency/Telegram architecture из non-blocking findings. После успешного завершения/commit task `49` следующей становится `49A`.

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
