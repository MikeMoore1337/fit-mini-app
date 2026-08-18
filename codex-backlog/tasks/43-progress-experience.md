# TASK 43. Прогресс, история и соблюдение плана - UI

- Фаза: **Core UX**
- Приоритет: **43/93**
- Зависит от: `21`, `27`, `31`, `32`, `34`, `38`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`

## Цель

Превратить Progress в понятный ответ «что изменилось и становлюсь ли я лучше?» на основе реальных aggregates task 21.

## In scope

Собрать смысловые группы: Body, Training, Nutrition, `Соблюдение плана`. Периоды минимум 7/30/90. Верхняя часть 2-4 high-signal summary, а не grid одинаковых cards.

Training: history, PR, frequency/volume только из backend. Body: weight/measurements trend. Nutrition: averages/target compliance. Adherence: формула не пересчитывается во frontend.

Графики использовать существующим stack или лёгким SVG/CSS, с текстовым представлением, доступными units/scales и корректным no-data/one-point/gaps/long-history behavior. Mobile без обязательного horizontal scroll.

## Extended Training analytics
Frontend только отображает backend task `27`: completed set count, weight/reps progression, exercise history, optional RIR, primary/secondary muscle exposure, frequency/volume. Никаких frontend formulas/effective-set coefficients. Для derived metrics предусмотреть explanation links task `50`.

## Out of scope

Не придумывать metrics, не менять PR/adherence formulas, не подключать тяжёлую chart library без доказанной необходимости, не выдавать medical conclusions.



## Проверки

No history/short/long, PR/no PR, body none/many, nutrition none/present, adherence partial, period change, workout detail, loading/error/partial. Playwright 1440/768/390/360 + component tests.

## Done when

Общая динамика понятна за секунды; графики не вводят в заблуждение; frontend не дублирует формулы.

## Рекомендуемый commit

`feat(ui): redesign progress and adherence experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 integration: anthropometry and confidence
Progress использует priorities/anthropometry `30`, sufficiency `31`, weekly check-in `33`. Никаких ideal-body scores и attribution окружности одной мышце.

## Final release integration: progression/reminders

После tasks `58-59` Today может показывать:
- одну high-signal progression подсказку для relevant exercise;
- upcoming workout/reminder state;
без превращения страницы в notification feed.
