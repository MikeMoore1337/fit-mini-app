# TASK 55. Приоритеты развития и антропометрия — UX

- Фаза: **Progress UX**
- Приоритет: **55/93**
- Зависит от: `31`, `32`, `43`, `48`
- Рекомендуемая модель: **GPT-5.6 Terra High**

## Цель

Показать собственную динамику замеров и выбранные приоритеты без фото/идеальных пропорций.

## In scope

- balanced/priority muscle groups; measurement trends; consistency hints; no strong single-point inference; separate circumference facts from muscle analytics; trainer permissions; knowledge links.

## Design V2 contract

Measurements, priorities и charts используют Design V2 semantic tokens, typography, data regions и accessible chart conventions; цвет не должен быть единственным носителем смысла. Прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md` и релевантные `docs/design/*v2*`, не вводить локальную analytics palette/card system и проверить light/dark, empty/insufficient и desktop/mobile states в реальном браузере.

## Out of scope

Никаких progress photos, AI/photo analysis, body-fat/ideal-proportion scores.

## Проверки

One/many measurements, priorities, empty/insufficient, trainer, charts/a11y.

## Done when

Замеры и приоритеты понятны и не вводят в заблуждение.

## Рекомендуемый commit

`feat(ui): add physique priorities and measurement trends`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
