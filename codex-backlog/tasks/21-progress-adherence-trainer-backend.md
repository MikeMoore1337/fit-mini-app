# TASK 21. Progress/adherence aggregates и trainer-safe access

- Фаза: **Core analytics**
- Приоритет: **21/93**
- Зависит от: `16`
- Рекомендуемый reasoning: **High**

## Цель

Создать достоверный слой прогресса и соблюдения плана поверх существующих workout/body/nutrition данных без псевдонаучных метрик.

Слой должен быть полезен не только пользователю, но и тренеру: тренер должен быстро понимать фактическое состояние закреплённых клиентов без ручного просмотра каждой тренировки и нескольких экранов.

## In scope

Сначала переиспользовать существующие progress/workout services. Поддержать API/service aggregates для периодов минимум 7/30/90 дней:
- body weight/measurements trends;
- nutrition averages/targets compliance;
- training frequency, completed planned workouts, PR/volume только если исходные данные позволяют;
- adherence: workouts, cardio, calories, protein и общий показатель только после явного определения формулы.

Для adherence определить: набор компонентов, weights, missing targets, no-plan days, incomplete current day, calorie tolerance. Формулу оформить отдельной domain/service функцией с unit tests и документацией.

Trainer получает только разрешённый overview закреплённого клиента. Проверить current relationship и отзыв доступа. Пользователь не видит чужие nutrition/body/user-food данные.

Не выдавать медицинские диагнозы/интерпретации.


## Trainer productivity summaries

Для закреплённых клиентов добавить безопасные high-signal summaries, пригодные для будущего Coach workspace. Если исходные данные реально существуют, summary может включать:

- дату последней завершённой тренировки;
- ближайшую/сегодняшнюю тренировку;
- количество planned/completed workouts за период;
- training adherence;
- nutrition adherence только при разрешённом trainer access;
- краткий body-weight/measurement trend;
- последнее измерение и дату его обновления;
- новые PR/значимые результаты только если они детерминированно считаются backend.

Summary должен быть пригоден для client list, trainer dashboard, sorting/filtering и client detail без загрузки полной истории.

Не создавать readiness/recovery/motivation/dropout-risk scores и ярлыки вроде «клиент ленится» или «плохо восстанавливается». Сигнал «давно не тренировался» строить только на объективной дате последней активности и явном UI-правиле.

Проверить отсутствие N+1 и overfetch при загрузке summaries нескольких клиентов.

## Out of scope

Не делать Progress UI/Coach UI, не придумывать readiness/recovery/streak или другую метрику без backend source/formula, не менять trainer relationship model, не добавлять AI Trainer Copilot/LLM summaries клиентов.



## Проверки

Formula/unit tests, empty/partial periods, missing goals, current day, long history aggregates, user isolation, trainer assigned/unassigned/former relation negative tests, several-clients summaries, no cross-user leakage, query/index/N+1 behavior.

## Done when

Frontend может получить единые, объяснимые и безопасные progress/adherence summaries без дублирования расчётов, а Coach workspace - high-signal summaries закреплённых клиентов без расширения прав доступа.

## Рекомендуемый commit

`feat(progress): add adherence and trainer client summaries`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Existing analytics preservation
Перед изменениями проверить current `services/analytics.py`. При подготовке backlog там уже есть adherence/streak/weight change/weekly volume/PR/timeline. Не переписывать их. Fitness Online-inspired exercise progression/RIR/muscle distribution выполняется task `27`.
