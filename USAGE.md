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

## Текущая task - 49B1

User-confirmed completed range: `00-49B`. Следующий запуск:

```text
Выполни `codex-backlog/tasks/49b1-current-ui-consistency-mobile-first-normalization.md`.

Соблюдай `AGENTS.md`, `codex-backlog/GLOBAL_RULES.md`
и полный task lifecycle.

Все предыдущие tasks считаются выполненными.
Не переходи к следующей task.
```

`49B1` сначала делает один evidence-based audit текущего rendered Design V2 и component foundation, замораживает finding set, затем исправляет только доказанные consistency/mobile defects. После неё следующая task - `49C`.

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
