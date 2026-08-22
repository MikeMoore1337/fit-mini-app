# Global rules

- Follow root `AGENTS.md`.
- Work only in `feature/yfc-platform-v2`.
- One public bot and one polling owner.
- Never expose tokens, raw `initData`, support text or sensitive user data in logs.
- Preserve `/start link_<token>`, signed TMA auth and login proxy-tunnel/TLS.
- No news/channel/digest scope.
- Run focused tests, inspect diff, one logical commit, do not start next task.
- Read `TELEGRAM_AUTOMATION_BOUNDARY.md` before every task that touches Telegram profile/BotFather/platform settings.


## Completed prerequisite freeze

Telegram tasks `00-current-state-audit-architecture.md` and `01-single-bot-support-feedback.md` were already completed before this package was created.

Rules:

- do **not** rerun tasks `00` or `01`;
- do **not** recreate their reports or commits;
- treat the current repository state and their completed results as source of truth;
- task `02` may make only changes required by its own public UX/profile synchronization scope;
- if task `02` discovers a regression in functionality implemented by `01`, fix only the concrete regression required for `02` and document it - do not redesign or replay task `01`;
- historical task files `00` and `01` are intentionally not included in this package.

## Maximum autonomy rule

Не создавать owner checkpoint для действий, которые текущая task разрешает и которые можно безопасно выполнить официальным Bot API после exact identity check.

В частности task `02` должна автоматизировать name/About/Description/profile photo/commands/Menu Button вместо перекладывания их на владельца.

Если владелец явно попросил Codex выполнить task `02`, это является explicit approval для bounded reversible Bot API metadata writes, перечисленных в самой task, только при `getMe.username == "your_fitness_coach_bot"`.

Это не разрешает token rotation, deploy, BotFather Main Mini App/Web Login changes, proxy changes, массовую рассылку или новые Telegram modes.

Если external write невозможно из-за отсутствующего token/network/tooling:

- не блокировать завершение реализации;
- реализовать и протестировать sync contract;
- оставить одну точную команду/действие для последующего запуска в подходящей среде;
- не просить владельца вручную повторять поля, которые уже автоматизированы.

## BotFather rule

BotFather рассматривается как owner-only fallback только для настроек, которых нет в безопасном Bot API contract.

Codex не должен просить доступ к личной Telegram Web-сессии владельца для автоматизации BotFather.

## Полный task lifecycle

Перед каждой task обязательно прочитать и выполнить `telegram-core-release-backlog/TASK_EXECUTION_LIFECYCLE.md`.

Фраза владельца `полный task lifecycle` ссылается именно на этот контракт. Он управляет основной ролью, optional researcher, independent review, QA verification, исправлениями, профильными проверками, итоговым diff и одним логическим commit.

Lifecycle не расширяет scope task и не отменяет security/privacy rules, Trigger/evidence gates и conditional/skip conditions.

## Skills: обязательный контракт выбора

Каждая task содержит точный набор `Рекомендуемые skills` и, где нужно, `Условные skills`. Перед реализацией открыть только реально применимые `.agents/skills/*/SKILL.md` и корневой `AGENTS.md`. `$telegram-engineer` обязателен для всех задач. Skill не расширяет scope task.
