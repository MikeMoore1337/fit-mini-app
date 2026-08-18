# TASK 40. Активная тренировка - эталонный interaction flow

- Фаза: **Core UX**
- Приоритет: **40/93**
- Зависит от: `05`, `24`, `28`, `29`, `35`, `36`, `38`
- Рекомендуемый reasoning: **Medium**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, при необходимости `$qa-engineer`

## Цель

Сделать активную тренировку самым быстрым и понятным interaction flow продукта без изменения тренировочной бизнес-логики.

## In scope

Переработать workout hero/progress, exercise/current set, weight/reps controls, previous result hint если есть, complete set, rest timer, next set/exercise, saving/saved/error, finish workout, Telegram haptic через существующий adapter.

Текущий подход визуально доминирует. Controls имеют крупные hit areas, mobile keyboard удобен, double tap не ломает state, scroll/focus предсказуем. Completion feedback быстрый: state/check/progress/timer. Haptic умеренно. Save status не закрывает controls. Reduced motion обязателен.

## Optional RIR UX
Использовать task `24`: optional `0/1/2/3/4+`, компактно, новичок может игнорировать. Рядом короткое `Что это?`; после task `50` ссылка ведёт на canonical RIR material.

## Exercise technique during workout
Использовать shared guide task `46` после его появления. Тяжёлое media не загружать до открытия.

## Out of scope

Не менять workout formulas/completion rules без необходимости, не добавлять auto progression/AI/voice, не менять историю данных.



## Проверки

Complete several sets, edit weight/reps, timer, save success/failure/retry, finish, reload/resume если существует, 390/360 mobile, desktop smoke, reduced motion, haptic adapter test.

## Done when

Очевидно текущее действие, controls удобны пальцем, timer/save feedback не мешают flow, бизнес-логика сохранена.

## Рекомендуемый commit

`feat(ui): refine active workout experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 integration: advanced workout state
Использовать task `29` set kinds/supersets, task `35` workout adaptation и task `36` offline-safe sync. Advanced controls — progressive disclosure; beginner can ignore them. Offline state: локально / синхронизация / синхронизировано / требует действия.

## Plain-language workout logging

Default beginner path stays simple: вес, повторы, завершение подхода.
Advanced concepts use `Дополнительно` or equivalent progressive disclosure.

Do not show raw `RIR`, `working set`, `warm-up`, `failure` or technical superset identifiers.

Ignoring advanced controls must not prevent completing a workout correctly.
