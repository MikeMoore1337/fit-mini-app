# Role routing guide v3

Canonical review/QA severity, recheck limits, commit/finalization и lifecycle находятся в `codex-backlog/TASK_EXECUTION_LIFECYCLE.md`.

Этот файл отвечает только за выбор роли.

## Роли

| Роль | Когда использовать |
| --- | --- |
| `orchestrator` | Несколько реально независимых streams, сложная convergence/integration planning |
| `researcher` | Отдельная неизвестность, которую выгодно закрыть read-only |
| `implementer` | Production implementation |
| `independent-reviewer` | Независимая проверка готового diff/decision |
| `qa-verifier` | Фактическая risk-based behavioral verification |
| `integration-release` | Merge/integration/release convergence |

## Правила

- Обычная feature-task имеет одного primary writer - `implementer`.
- Не использовать `orchestrator` для локальной feature-task.
- Не создавать `researcher` для обычного чтения файлов implementer'ом.
- `independent-reviewer` и `qa-verifier` не объединяются: review проверяет diff/contract, QA - поведение.
- `integration-release` не заменяет `release-manager`; роль задаёт ответственность, skill - профессиональный workflow.
- Не создавать отдельные роли `designer`, `motion-designer`, `ai-engineer`, `security-reviewer` и т.п. Их знания выражаются skills.
- Task metadata остаётся основным маршрутом для backlog task.
