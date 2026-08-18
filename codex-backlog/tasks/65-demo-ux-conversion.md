# TASK 65. Demo Mode - UX, contextual conversion и public CTA

- Фаза: **Demo conversion UX**
- Приоритет: **65/93**
- Зависит от: `64`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Сделать Demo Mode инструментом конверсии для самостоятельных пользователей и персональных тренеров: сначала дать попробовать полезный workflow, затем предлагать auth в момент сохранения/продолжения реальной работы.

## In scope

Добавить/уточнить public secondary CTA `Попробовать демо` без поломки основного CTA.

Реализовать contextual persistence prompts для поддержанных flows:
- Save program;
- Save profile;
- Save КБЖУ result;
- Finish/save workout;
- Keep progress.

Принцип: `try -> receive value -> attempt to keep result -> authenticate`.

Предлагать существующие canonical continuation paths:
- authenticated Web;
- Telegram Mini App/deep-link, где уместно.

Не дублировать auth/navigation helpers и не спамить modals.
Persistent demo banner action остаётся доступным.

AI Coach остаётся disabled. Допустим non-interactive teaser:
- no chat input;
- no fake responses;
- no provider calls;
- no demo AI quota.

Проверить desktop/mobile Web и Telegram continuation/auth layouts.


## User / Trainer demo entry

Если task `64` реализовал оба сценария, единый Demo Mode entry должен дать понятный выбор по смыслу: `Я занимаюсь самостоятельно` / `Я тренер`. Не создавать несколько конкурирующих hero CTA - финальный landing hierarchy будет в task `73`.

## Trainer demo conversion

Тренер должен сначала иметь возможность исследовать synthetic client list, client detail, program, workout history, progress/measurements и разрешённый nutrition/adherence.

При попытке persistent/identity-bound trainer action предложить существующую auth/registration path. Conversion copy должен объяснять trainer benefit, например по смыслу: «Ведите клиентов, назначайте программы и отслеживайте прогресс в одном месте», а не только generic «Войдите, чтобы продолжить».

Не создавать отдельную trainer auth систему. Не выполнять реальные invitations/notifications/relationships из demo.

В trainer demo не обещать Trainer Copilot. AI Coach остаётся locked и не выполняет provider requests.

## Out of scope

Не делать финальный landing redesign - task 73. Не делать auth-data import - task 66. Не активировать AI/Trainer Copilot и не создавать trainer marketplace/new auth flow.

## Проверки

UI/integration tests: demo CTA, user/trainer scenario choice, user save interception, trainer persistent-action interception, trainer-specific value copy, Web/Telegram targets, no real side effects, no modal spam, AI locked in both scenarios, 390/360 + desktop.

## Done when

Рабочий Demo entry есть; user и trainer получают ценность до auth; trainer может попробовать Coach workspace на synthetic clients; conversion контекстный и объясняет trainer benefit; AI неактивен во всех demo scenarios.

## Рекомендуемый commit

`feat(demo): add user and trainer conversion ux`

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

## Training product discovery
Demo может ненавязчиво показать program wizard, expanded exercise guide, progress analytics и contextual trainer feedback, но не превращается в длинный feature tour.

## Final release integration: deterministic intelligence fixtures

Synthetic demo fixtures могут показать:
- progression suggestion с объяснением;
- одну manual cardio session;
но не должны запускать реальные reminders или создавать persistent notification jobs.
