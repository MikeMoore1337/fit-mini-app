# TASK 86. AI Coach: тренировки, прогресс и антропометрия

- Фаза: **AI Coach**
- Приоритет: **86/93**
- Зависит от: `23`, `24`, `27`, `30`, `31`, `32`, `34`, `35`, `54`, `55`, `58`, `61`, `84`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Отвечать персонально о сегодняшней тренировке, прогрессии, объёме и замерах.

## In scope

- `Что мне сегодня покачать?`: current program/today/schedule/recent; no invented workout if none.
- Exercise progression: weight/reps/working sets/RIR/targets/history.
- Muscle exposure without arbitrary coefficients.
- Weekly check-ins/adherence.
- Anthropometry + user priorities + sufficiency.
- Never say `бицепс отстаёт` from arm circumference alone; require combined anthropometry + progression + exposure + priority + sufficient period.
- Compare user primarily with self. Suggest only, no program writes.

## Out of scope

Никакого анализа фото, ideal-body score, medical injury recommendations, trainer client data or autonomous writes.

## Проверки

No program/rest day, progression, sparse measurements, arm-vs-biceps false inference, priorities, trainer self context, isolation.

## Done when

Coach персонально отвечает по тренировкам/замерам без псевдоточности.

## Рекомендуемый commit

`feat(ai): add training and anthropometry context`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и актуальный `docs/` — source of truth.
Не проводить повторный полный аудит репозитория, не перечитывать все task-файлы и весь `masters/`.
Если текущий task относится к одному master — читать только его. Использовать результаты предыдущих audit вместо повторного исследования.
Исследовать только релевантные файлы и подсистемы. Если функция уже существует — переиспользовать, не дублировать.
Крупное изменение вне scope не начинать автоматически: зафиксировать follow-up.

Работать только в текущей feature-ветке. Не create/switch branch, merge/rebase, deploy и не переходить к следующему task.
После реализации: только профильные checks, `git diff`, один логический commit при tracked changes, краткий отчёт с reused/changed/files/migrations-config/checks/follow-ups/hash.

## Final release integration: progression and cardio

AI не рассчитывает progression самостоятельно.
Для вопросов о следующей нагрузке Coach читает task `58` deterministic result/evidence.

Cardio context:
- только текущий authenticated user;
- duration/frequency/manual HR facts;
- no generic calorie-burn invention;
- no wearables.

## Coach language adaptation

Coach defaults to ordinary Russian:
- `повторы в запасе`, not unexplained `RIR`;
- `соблюдение плана`, not `adherence`;
- `облегчённая неделя`, not unexplained `deload`.

If the user explicitly uses professional terminology, Coach may mirror it.
Do not infer expertise merely because backend data contains advanced fields.
