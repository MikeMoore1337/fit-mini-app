# Task 115A — compactness и progressive disclosure

## Decision rule

Секция always-visible только если без неё нельзя понять или завершить текущее действие. Один
expandable level допустим для короткого контекста. Длинная форма, история, график или несколько
действий получают отдельный screen/sheet.

## Карта presentation modes

| Раздел         | Always visible                 | Compact summary                       | Expandable              | Detail screen/sheet                         |
| -------------- | ------------------------------ | ------------------------------------- | ----------------------- | ------------------------------------------- |
| Сегодня        | date context, current action   | nutrition, progress, cardio/wellbeing | legend/short reason     | quick log/history                           |
| Программа      | current program + CTA          | days/workouts                         | short day preview       | builder, templates, history, advanced       |
| Active workout | current set/timer/finish       | exercise queue                        | one `Дополнительно`     | technique/history/replace exercise          |
| Active cardio  | current timer/status/finish    | planned target/result                 | optional sensors/notes  | history/settings                            |
| Питание        | day total + meal add           | meals                                 | meal entries            | picker, targets, reports, hydration history |
| Прогресс       | period conclusion + confidence | semantic category summaries           | short methodology       | charts/history/report                       |
| Профиль        | identity + account state       | settings rows                         | short completion reason | all large forms/settings                    |

## Representative collapsed/expanded states

### Today

Collapsed card: `Питание · 1460 из 2100 ккал` + `Добавить`. Expanded state не нужен: tap title
открывает Nutrition, quick action открывает picker. Workout current operation никогда не collapsed.

### Program

Collapsed day: `День 1 · 5 упражнений · ~55 мин`. Один tap раскрывает короткий exercise preview;
`Изменить день` ведёт на detail builder. Внутри preview нет второго accordion.

### Nutrition

Collapsed meal: `Завтрак · 2 записи · 510 ккал`, `Добавить` доступно сразу. Expanded показывает
food rows и одну строку secondary actions. Targets/history/report — отдельные details.

### Progress

Collapsed summary: `Тренировки · 3 из 3 · по плану`. Tap открывает training detail. Methodology
допускает один disclosure внутри detail, не на summary screen.

### Profile

Collapsed row: icon, label, status (`Заполнено` / `Требуются данные`), chevron. Tap открывает
detail route. Profile index не раскрывает формы inline.

## Vertical density budget как hierarchy, не pixel quota

- На initial `360x800` должны быть видны location, primary action/current status и начало 2–3
  meaningful summaries; нижняя nav не перекрывает контент.
- Высота создаётся полезными data rows, а не permanently expanded helper/settings/history.
- Один viewport не обязан вместить весь день. Он обязан дать ясный следующий шаг без поиска.
- Desktop группирует summaries колонками; не показывает все detail blocks одновременно.

## Где disclosure запрещён

- `Начать/Продолжить тренировку`, current set inputs, timer, `Готово`/`Завершить`;
- food amount и `Добавить в дневник` после выбора продукта;
- primary Program save и validation reason;
- error/retry и dirty unsaved state;
- active cardio state/finish;
- permission/capability explanation, если без неё action исчезает.

## Nested-disclosure audit

| Риск                                                  | Решение                                                        |
| ----------------------------------------------------- | -------------------------------------------------------------- |
| Program builder -> day -> exercise -> advanced        | day/exercise становятся detail screens; один advanced level    |
| Progress summary -> section -> chart -> methodology   | summary -> detail; methodology один disclosure в detail        |
| Profile group -> subsection -> advanced               | index -> detail; advanced один disclosure внутри form          |
| Meal -> entry -> repeat/edit dialog                   | meal один expand; edit/repeat separate modal/sheet             |
| Workout exercise -> guidance -> `Почему?` -> settings | guidance reason один expand; settings/technique separate sheet |

## Accessibility/runtime contract

- expandable header — semantic button с `aria-expanded`/`aria-controls`;
- весь header tap-target не меньше 44 px, label остаётся текстовым;
- focus сохраняется; reveal не вызывает неожиданный scroll jump;
- sheet получает focus trap/restore и TMA BackButton lifecycle;
- transition interruptible, reduced-motion без spatial animation;
- keyboard/visualViewport не закрывает field, error, CTA и close;
- pending/error/dirty section не схлопывается автоматически.
