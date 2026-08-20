# TASK 62. Demo Mode - аудит и архитектурное решение

- Фаза: **Demo foundation**
- Приоритет: **62/93**
- Зависит от: `48`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$ui-audit`, `$product-designer`, при необходимости `$security-engineer`

## Цель

Провести узкий аудит уже сформированного продукта и определить минимальную безопасную архитектуру публичного demo mode.

## In scope

Изучить landing/public entry points, Web routing, Telegram Mini App entry/auth behavior, session/auth state,
app shell/navigation, API/write paths, profile, nutrition/КБЖУ, pulse zones, programs/exercises, workout,
history/progress, AI Coach routes/components/API, trainer/client invitations, linking, notifications,
persistence, feature flags/application modes, tests и релевантный docs.

Определить:
1. application state `public/demo/authenticated`;
2. вход/выход из demo;
3. место prepared fixtures;
4. хранение временных edits;
5. какие writes симулируются локально;
6. какие side effects запрещены;
7. где блокируется AI Coach: UI/route/client/backend;
8. demo -> Web auth / Telegram continuation;
9. безопасен ли optional import пользовательских demo-вводов;
10. capability matrix и tests.

В design-решении зафиксировать, что Demo использует реальный Approved Design V2 app shell и feature components, а не отдельную marketing/demo theme. Для этого прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md`, релевантные `docs/design/*v2*` и проверить текущую production V2 реализацию в браузере; любое изменение канонического visual language вынести на owner checkpoint, а не проектировать внутри Demo.

Предпочитать centralized mode/capabilities вместо множества `if demo`.
Raw audit: `.artifacts/codex-audits/demo-mode/`.
Если решение долгоживущее и conventions проекта это предполагают - добавить короткую архитектурную заметку в docs.

## Out of scope

Не реализовывать полноценный demo mode, fixtures, CTA, migration или security fixes.
Не редизайнить auth и не создавать отдельное demo-приложение.

## Проверки

Проверить, что вывод основан на текущем коде и фактических Food/Redesign/AI подсистемах. Если tracked files не менялись - commit не создавать.

## Done when

Есть конкретная архитектура demo mode, capability matrix, persistence policy, AI boundary, auth handoff decision и тестовая стратегия.

## Рекомендуемый commit

`docs(demo): define demo mode integration plan`

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
