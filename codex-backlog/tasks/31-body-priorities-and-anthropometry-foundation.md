# TASK 31. Приоритеты развития и антропометрический контекст

- Фаза: **Progress domain**
- Приоритет: **31/93**
- Зависит от: `23`, `27`, `30`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Заложить честный foundation для трендов замеров и индивидуальных приоритетов развития.

## In scope

- Проверить текущую BodyMeasurement model.
- User preference: `balanced` или 1+ priority muscle groups из canonical taxonomy; optional.
- Chronological measurement trends; сильные выводы только при достаточном числе точек/периоде.
- Measurement consistency guidance.
- Окружность плеча != размер бицепса; бедро != квадрицепс. Muscle-specific вывод позже допускается только из совокупности anthropometry + exercise progression + muscle exposure + priority.
- Сравнивать пользователя прежде всего с собой.
- Privacy/ownership сохранить.

## Out of scope

Никаких progress photos, image/body analysis, body-fat-from-photo, ideal body ratios/scores и diagnosis.

## Проверки

One/many measurements, priorities, trainer access, cross-user isolation, date ranges, single-point guards.

## Done when

Есть structured priorities и честный anthropometry context без псевдоточности.

## Рекомендуемый commit

`feat(progress): add body priorities and anthropometry context`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
