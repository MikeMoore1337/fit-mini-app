# YFC Codex roles v2 - resource-aware

Роль задаёт ответственность конкретного агента/прохода, skill - профильный контракт, task - scope и результат.

## Доступные роли

1. `orchestrator` - маршрутизация только реально независимых streams.
2. `researcher` - узкое read-only исследование при настоящей неизвестности.
3. `implementer` - единственный primary production writer обычной task.
4. `independent-reviewer` - bounded review текущей task/diff; production-код не меняет.
5. `qa-verifier` - bounded risk-based verification; production-код не меняет.
6. `integration-release` - интеграция/release scope без feature expansion.

## Как выбирать

Начиная с task `49`, task-файл явно задаёт `Основная роль` и `Дополнительные роли lifecycle`. Это source of truth. Не запускать автоматическую цепочку из всех ролей и не создавать агента на каждый skill.

Code/diff reviewer использует `$code-reviewer` как base skill, QA - `$qa-engineer`; non-code design/decision gate не загружает `$code-reviewer` автоматически. Base skills можно не повторять в task metadata. После blocking fix повторный pass является targeted recheck, а не новым полным аудитом.

См. `../references/ROLE_ROUTING_GUIDE.md` и `codex-backlog/TASK_EXECUTION_LIFECYCLE.md`.
