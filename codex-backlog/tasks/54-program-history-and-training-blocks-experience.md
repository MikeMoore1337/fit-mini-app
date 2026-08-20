# TASK 54. История программы и тренировочные блоки — UX

- Фаза: **Programs UX**
- Приоритет: **54/93**
- Зависит от: `30`, `44`, `48`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Показать эволюцию программы и текущий тренировочный блок.

## In scope

- Current block/status/dates/purpose; block history; who/when/what changed; readable diff; trainer edits; historical workouts tied to correct revision.

## Design V2 contract

History, blocks и readable diff собираются из shared Design V2 timeline/data-region/status primitives и остаются визуально связаны с Programs и Coach workspace. Прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`; не создавать локальную card/timeline system. Проверить light/dark, long history и desktop/mobile composition в реальном браузере.

## Out of scope

Без complex periodization UI, auto-deload и AI.

## Проверки

Self/trainer edits, block transitions, long history, revoked trainer, mobile.

## Done when

Пользователь понимает, как и почему менялась программа.

## Рекомендуемый commit

`feat(ui): add program history and blocks`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
