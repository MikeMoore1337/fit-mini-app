# TASK 63. Demo Mode - first-class application mode и capability boundary

- Фаза: **Demo foundation**
- Приоритет: **63/93**
- Зависит от: `62`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$frontend-engineer`, `$qa-engineer`

## Цель

Ввести demo как полноценное состояние приложения без изменения обычного authenticated Web/Telegram поведения.

## In scope

Реализовать centralized distinction:
- unauthenticated/public;
- demo;
- authenticated.

Добавить быстрый public demo entry без регистрации и Telegram auth, используя настоящий app shell.
Не запускать onboarding постоянного аккаунта.

Добавить persistent, но ненавязчивый demo indicator:
- это demo;
- изменения временные;
- есть continue/sign-in action.

Добавить capability abstraction в стиле проекта, например по смыслу:
`canPersistUserData`, `canUseAiCoach`, `canInviteClient`, `canSendNotifications`, `canLinkAccounts`.

С этого этапа AI Coach в demo должен быть недоступен:
- navigation/UI;
- direct route;
- frontend API invocation;
- backend endpoint/auth validation, если anonymous call иначе возможен.

Допустим только locked/teaser state. Никаких provider calls и demo AI quota.

## Out of scope

Не добавлять fixtures/core interactions, contextual conversion UX, новую auth систему или новые RBAC semantics.

## Проверки

Tests: enter demo, mode detection, authenticated behavior unchanged, indicator, AI locked, direct AI route/API blocked, typecheck/lint/build.

## Done when

Demo является first-class state, использует реальный app shell, явно обозначен и не может вызвать AI Coach.

## Рекомендуемый commit

`feat(demo): add first-class demo application mode`

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
