# TASK 58. Детерминированные рекомендации прогрессии нагрузки

- Фаза: **Training Intelligence**
- Приоритет: **58/93**
- Зависит от: `29`, `39`, `43`, `45`, `51`, `52`, `55`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Добавить понятный deterministic механизм ответа на вопрос
«что делать с нагрузкой в следующий раз?» без LLM и без автоматического изменения программы.

## In scope

1. Сначала проверить current program prescription, rep ranges, RIR, set semantics, exercise history,
units и доступные шаги веса.

2. Recommendation engine должен использовать только объективно доступные факты:
   - program target reps/range;
   - completed WORKING sets;
   - actual reps;
   - actual weight;
   - RIR, если пользователь его ведёт;
   - последовательность последних сопоставимых sessions;
   - program/block context;
   - exercise/equipment increment constraints, если они есть.

3. Не требовать RIR.
При отсутствии RIR движок должен работать более консервативно и явно понимать меньшую информативность.

4. Результат не должен быть бинарным «увеличить/уменьшить любой ценой».
Минимальные безопасные outcomes:
   - `consider_progressing`;
   - `hold`;
   - `review`.
Допустимо `consider_reducing` только при хорошо определённых deterministic rules,
но не как диагноз fatigue/overtraining.

5. Величина suggested increment:
   - использовать configured/available equipment step, если он известен;
   - иначе предложить qualitative action без выдуманного точного веса;
   - units kg/lb корректны.

6. Пример double-progression rule допустим только если соответствует program prescription.
Не подменять программный метод прогрессии generic формулой.

7. Recommendation НЕ меняет:
   - программу;
   - target weight;
   - future workout;
   - set prescription.
Пользователь/тренер принимает решение сам.

8. UX:
   - небольшая подсказка рядом с relevant exercise / next occurrence;
   - «Почему?» показывает факты: последние sessions, target range, RIR coverage;
   - можно проигнорировать;
   - не перегружать active workout.

9. Optional post-workout feedback:
   - `легче ожидаемого / нормально / тяжелее ожидаемого`;
   - optional note;
   - не превращать в recovery score;
   - не использовать как единственный reason для progression.

10. Будущий AI Coach читает deterministic suggestion и evidence,
но не рассчитывает progression самостоятельно.

## Out of scope

Не использовать LLM.
Не вычислять псевдоточный hypertrophy/fatigue/readiness score.
Не делать e1RM центральным источником решения.
Не менять программу автоматически.
Не диагностировать перетренированность.
Не использовать one-session anomaly как сильный вывод без правил.

## Проверки

No history; partial history; rep range achieved/not achieved; with/without RIR;
warmup excluded; drop/failure semantics; kg/lb; unavailable increment;
program revision/block change; user ignores suggestion; trainer-assigned program;
post-workout feedback optional; deterministic repeatability.

## Done when

Следующая нагрузка получает объяснимую deterministic рекомендацию,
которая уважает конкретную программу, данные пользователя и не меняет ничего без его решения.

## Рекомендуемый commit

`feat(training): add deterministic progression guidance`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными.
Текущий код, Git history и актуальный `docs/` — source of truth по их результатам.

Не проводить повторный полный аудит репозитория.
Не перечитывать все предыдущие task-файлы.
Не читать весь `codex-backlog/masters/` без необходимости.

Если текущий task явно относится к одному master-документу,
прочитать только этот master.

Если предыдущий audit уже исследовал нужную область и результат доступен,
переиспользовать его; точечно перепроверять только факты, которые могли измениться.

Сначала прочитать текущий task, затем исследовать только релевантный набор файлов
и подсистем, необходимый для корректного выполнения задачи.

Если требуемая функциональность уже существует:
- не реализовывать её заново;
- переиспользовать текущую архитектуру;
- закрыть только реальные gaps.

Не расширять scope самостоятельно.

Если для выполнения нужен крупный architectural change вне scope:
- не начинать его автоматически;
- зафиксировать follow-up;
- выполнить безопасную часть текущего task, если возможно.

Работать только в текущей feature-ветке.

Не:
- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- переходить к следующему task.

После реализации:
1. только профильные проверки согласно `AGENTS.md`;
2. не запускать полный test suite без необходимости;
3. проверить `git diff`;
4. создать один логический commit при tracked changes;
5. краткий финальный отчёт: reused / changed / files / migrations-config / checks / follow-ups / commit hash.

## Plain-language progression UX

Use ordinary wording:
- `Можно рассмотреть небольшое увеличение веса`;
- `Пока оставьте текущую нагрузку`;
- `Данных недостаточно — сначала закрепите текущий диапазон повторений`.

Do not require understanding double progression, RIR or overload algorithms.

If RIR matters, say:
`в последних подходах оставалось примерно 1–2 повтора`
unless the user already uses RIR terminology.
