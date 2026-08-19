# Новые промежуточные задачи после выполненной task 46

Добавьте содержимое этой папки `codex-backlog/` в существующую папку проекта с тем же именем.

Существующие tasks `00-93` архив не заменяет и не удаляет. Он добавляет:

- tasks `46A`, `46B`, `46B1` - ретроспективные audits и owner decision gate;
- umbrella `46C` и tasks `46C.1-46C.5` - пять owner-approved remediation change sets;
- tasks `46D-46I` - Design V2 с рендерами, owner checkpoints, pilot и rollout;
- task `46J` - точечную синхронизацию ещё не выполненных tasks `47-93`;
- `DESIGN_V2_INTEGRATION_NOTES.md` - общий контракт перехода.

## Порядок запуска

Начните с:

```text
Выполни `codex-backlog/tasks/46a-completed-scope-production-quality-audit.md`.

Соблюдай `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.
Не переходи к следующей задаче.
```

Каждую следующую task запускайте в отдельном чате/сессии. Tasks `46C.1-46C.5` выполняются строго
последовательно и каждая завершается отдельным commit/STOP. Task `46D` начинается только после
завершения всех пяти. Tasks `46E`, `46F`, `46G` и `46H` содержат обязательные остановки для выбора,
утверждения рендеров и ручной проверки.

Task `47` начинайте только после завершения `46J`.
