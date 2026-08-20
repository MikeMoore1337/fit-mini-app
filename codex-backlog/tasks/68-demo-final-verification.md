# TASK 68. Demo Mode - E2E verification, cleanup и документация

- Фаза: **Demo hardening**
- Приоритет: **68/93**
- Зависит от: `67`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$qa-engineer`, `$code-reviewer`, при необходимости `$ui-audit`

## Цель

Провести сквозную проверку demo mode и убедиться, что authenticated Web/Telegram продукт не регрессировал.

## In scope

Проверить:

Public:
- landing/public entry;
- demo CTA;
- ordinary auth CTA.

Demo:
- indicator;
- fixtures;
- core navigation;
- temporary profile/calculation/program/workout/nutrition interactions;
- reset/reload;
- contextual persistence conversion;
- AI cannot be used;
- identity-bound actions cannot execute;
- no real-user mutation.

Authenticated Web:
- login/session;
- normal persistence;
- AI availability по обычным правилам;
- invitations/notifications permissions.

Telegram:
- authenticated Mini App не регрессировал;
- demo не masquerades as Telegram auth;
- demo->Telegram continuation корректен.

Transitions:
public->demo, demo->Web auth, demo->Telegram, reset, exit, authenticated->logout, no stale demo state.

Обновить durable docs: что такое demo, fixtures location, persistence policy, restrictions,
AI authenticated-only, safe extension rules.

Cleanup: debug flags/logs, dead prototype code, PII/production fixture data, hidden security TODO, i18n copy.

## Out of scope

Не deploy/merge. Не превращать stage в новый redesign. Full suite - только по AGENTS.md.

## Проверки

Relevant unit/integration/frontend/backend/typecheck/lint/format/targeted E2E. В browser visual pass сверить representative mobile+desktop light/dark states с Approved Design V2 по `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантным `docs/design/*v2*`: Demo не имеет отдельной palette, typography, radii, cards, navigation или generic SaaS conversion language. Screenshots/visual artifacts хранить по project conventions.

## Done when

Demo production-quality в проверенном scope; auth Web/Telegram не регрессировали; AI/side effects закрыты; docs актуальны.

## Рекомендуемый commit

`test(demo): complete demo mode verification`

## Процесс и отчёт

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.
Работать только в текущей выделенной feature-ветке. Не создавать и не переключать ветки,
не merge/rebase и не deploy в production без прямого указания владельца.
Не переходить к следующему task.

После изменений запустить только профильные проверки согласно `AGENTS.md`, проверить `git diff`
и создать один логический commit, если task меняет tracked files.

В финальном отчёте перечислить:
- изменения;
- ключевые файлы;
- миграции;
- реально запущенные проверки;
- ограничения;
- commit hash.
