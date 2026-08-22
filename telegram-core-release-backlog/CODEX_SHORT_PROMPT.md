# Короткий промпт Codex

Для задач этого пакета:

```text
Выполни `telegram-core-release-backlog/tasks/<имя-task>.md`.

Соблюдай `AGENTS.md`, `telegram-core-release-backlog/GLOBAL_RULES.md`
и полный task lifecycle.

Telegram tasks 00 и 01 уже выполнены и не должны переисполняться.
Все остальные предыдущие Telegram tasks относительно запускаемой задачи также считаются выполненными.
Не переходи к следующей task.
```

`Полный task lifecycle` определён в `telegram-core-release-backlog/TASK_EXECUTION_LIFECYCLE.md`.

## Для task 02

Отдельное подтверждение на bounded reversible изменения name/About/Description/avatar/commands/Menu Button через Bot API не требуется: сам запуск task `02` владельцем является разрешением согласно task и `TELEGRAM_AUTOMATION_BOUNDARY.md`.

Это не разрешение на deploy, token rotation, изменение username, Web Login/Main Mini App через BotFather, proxy-tunnel или массовые сообщения.
