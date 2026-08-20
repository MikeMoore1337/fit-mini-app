# TASK 64. Demo Mode - fixtures и временные интерактивные сценарии

- Фаза: **Demo product flows**
- Приоритет: **64/93**
- Зависит от: `29`, `31`, `34`, `35`, `48`, `63`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$frontend-engineer`, при необходимости `$backend-engineer`, `$qa-engineer`

## Цель

Сделать Demo Mode содержательным для двух аудиторий: самостоятельного пользователя и персонального тренера, на реалистичных полностью synthetic данных без ordinary persistent records.

## In scope

Создать maintainable fixtures на актуальных domain types/contracts только для реально существующих функций.
Покрыть по факту: profile/goal/anthropometry, КБЖУ, pulse zones, programs/exercises, workout history,
progress/measurements/statistics и nutrition data, если уже реализована.

Разрешить temporary interactions там, где это соответствует продукту:
- demo profile/goal edits;
- КБЖУ и pulse recalculation через существующие deterministic services;
- create/edit training program;
- sets/reps/rest;
- start workout, results, timers, finish;
- prepared progress/history;
- актуальные nutrition interactions.

Demo writes не становятся обычными backend records.
Предпочитать demo repository/adapter или ephemeral state, а не shared mutable DB demo-user.

Добавить `Reset demo`.
Выбрать и задокументировать reload policy:
- reset; или
- безопасная demo-scoped browser/session persistence.

Unsupported persistent action должен давать продуктовый fallback.

## Design V2 contract

Fixtures обязаны упражнять реальные Design V2 components и representative states, а не mock-макеты или demo-only variants. Прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`; synthetic content должен проверять shared navigation, forms, exercise/data regions, empty/filled/status states и light/dark parity на desktop/mobile.


## Demo personas

Demo Mode должен поддерживать два сценария в рамках одного продукта:

### A. Самостоятельный пользователь

Использовать representative synthetic profile/goal/КБЖУ/program/workout/progress/measurements/nutrition data по реально существующим функциям.

### B. Trainer demo

Поверх фактического Coach workspace из task `48` подготовить несколько полностью synthetic clients, например: recent workout, no recent activity, active program, progress trend, measurements update, разрешённый nutrition/adherence state, pending invitation.

Никаких real production users, Telegram accounts, email/phone, production exports или PII. Не использовать ярлыки «ленивый», «проблемный», «в зоне риска».

Trainer demo должен позволять безопасно попробовать: client list/search/filter, client detail, program, workout history, progress, measurements, разрешённый nutrition/adherence, `client -> program -> client`, temporary program action если workflow существует.

Temporary trainer changes не создают real records, invitations, notifications, relationships или side effects.

Если architecture позволяет, дать понятный выбор/переключение `попробовать как пользователь` / `попробовать как тренер` без создания второго приложения.

## Out of scope

Не создавать shared mutable demo account.
Не сохранять fixture history как real user history.
Не включать AI/Trainer Copilot, invitations, notifications, linking и другие external side effects; не использовать real client/user data.
Не выдумывать отсутствующие функции.

## Проверки

Tests: user+trainer fixture loading, scenario selection, trainer client list/detail/program/progress/measurements, temporary edits, deterministic calculations, reset, no normal persistence write, no PII/production IDs, no cross-demo-session leakage, demo/auth isolation, reload policy, no AI/invitations/notifications.

## Done when

Demo позволяет реально оценить продукт и самостоятельному пользователю, и тренеру; Trainer demo показывает Coach workspace на synthetic clients; edits временные, reset предсказуем, real records/PII не используются и не загрязняются.

## Рекомендуемый commit

`feat(demo): add user and trainer demo scenarios`

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

## Fitness Online-inspired demo fixtures
Если features реализованы: ephemeral program recommendation, optional RIR, one synthetic trainer comment, legal exercise guide/media. Никаких ordinary persistent records.

## Backlog v3 demo fixtures
Synthetic fixtures могут показать set kinds/RIR, один superset, measurements+priorities, weekly check-in, workout adaptation и program revision/block. Никаких progress photos.

## Final release integration: demo conversion

Demo не должен заставлять проходить реальный onboarding.
После решения сохранить/авторизоваться:
- auth;
- task `14` progressive onboarding только для реально недостающих authoritative данных;
- demo fixtures не импортируются автоматически.
