# TASK 32. Качество данных и confidence contract

- Фаза: **Analytics foundation**
- Приоритет: **32/93**
- Зависит от: `22`, `27`, `31`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Отличать достаточные данные от sparse data для analytics, adaptive nutrition и AI.

## In scope

- Не один magic score, а per-domain signals: nutrition coverage, weight points/timespan, anthropometry points/timespan, workout logging completeness, working sets, RIR coverage, schedule/adherence availability.
- Machine-readable `sufficient|limited|insufficient` + counters/reason keys.
- Deterministic rules/tests; thresholds документировать как product rules, не medical norms.
- Analytics может возвращать confidence metadata.
- Trainer permissions наследуются.

## Out of scope

Без health score, medical confidence, LLM sufficiency и shame/gamification.

## Проверки

Empty/partial/full data, periods, RIR optional, partial workouts, trainer permissions.

## Done when

Каждый аналитический domain сообщает достаточность данных и причину.

## Рекомендуемый commit

`feat(analytics): add data sufficiency contracts`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.
