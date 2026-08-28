# Backlog v10 changelog - resource-aware lifecycle

Дата: 22.08.2026.

## Причина

Task `49` была остановлена после того, как independent review не нашёл `BLOCKER/HIGH`, но non-blocking medium findings запустили новый backend/data/Telegram scope и повторные роли. Это создало лишние циклы, расход контекста и риск scope creep.

## Что изменено

- Task `49` переведена в explicit `RESUME` с сохранением текущего worktree и запретом продолжать review-induced architecture по non-blocking findings.
- `TASK_EXECUTION_LIFECYCLE.md` обновлён до v2: только `BLOCKER/HIGH` блокируют, первый review - единственный full pass, далее только targeted recheck, количество циклов ограничено.
- Убрана автоматическая цепочка `researcher -> reviewer -> QA`; точные роли задаются task metadata.
- Для tasks `49-79` вручную пересмотрены core skills, conditional skills и дополнительные lifecycle-роли по фактическому контексту.
- Reviewer/QA base skills больше не дублируются во всех feature skill lists.
- Telegram/accessibility/security/data/architecture specialists подключаются только по реальному trigger.
- Dedicated review gates не дублируются в предыдущих implementation tasks.
- `SKILL_ASSIGNMENT_MATRIX.md`, routing guides, status/prompt/checklist/manifest синхронизированы с новой моделью.

## Совместимость

Tasks `00-48` не переигрываются. После завершения task `49` обычная последовательность продолжается с `49A`. Design V2 остаётся active source до owner decision/`49G`.
