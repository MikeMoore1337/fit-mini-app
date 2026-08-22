# Global rules

- Follow root `AGENTS.md`.
- Work only in `feature/yfc-platform-v2`.
- One public bot and one polling owner.
- Never expose tokens, raw initData, support text or sensitive user data in logs.
- Preserve `/start link_<token>`, signed TMA auth and login proxy-tunnel/TLS.
- Do not rotate/revoke tokens or change BotFather/production without owner action.
- No news/channel/digest scope.
- Run focused tests, inspect diff, one logical commit, do not start next task.


## Полный task lifecycle

Перед каждой task обязательно прочитать и выполнить `telegram-core-release-backlog/TASK_EXECUTION_LIFECYCLE.md`.

Фраза владельца `полный task lifecycle` ссылается именно на этот контракт. Он управляет основной ролью, optional researcher, independent review, QA verification, исправлениями, профильными проверками, итоговым diff и одним логическим commit.

Lifecycle не расширяет scope task и не отменяет owner checkpoints, Trigger/evidence gates, conditional/skip conditions, security/privacy rules или запрет внешних production actions без разрешения.

## Skills: обязательный контракт выбора

Каждая task содержит точный набор `Рекомендуемые skills`. Перед реализацией открыть соответствующие `.agents/skills/*/SKILL.md` из архива `your-fitness-coach-agents-v3.zip` и корневой `AGENTS.md`. `$telegram-engineer` обязателен для всех задач; security/privacy/platform/observability/accessibility skills использовать там, где они перечислены. Skill не расширяет scope task.
