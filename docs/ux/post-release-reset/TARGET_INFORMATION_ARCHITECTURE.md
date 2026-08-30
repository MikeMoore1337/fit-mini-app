# Task 115A — целевая информационная архитектура

## Fixed navigation

```text
Сегодня | Программа | Питание | Прогресс
```

Навигация стабильна при любом состоянии. `Сегодня` не исчезает без данных. Profile/avatar открывает
secondary account layer из app shell и не становится пятым competing product destination.

## Иерархия экранов

```text
App shell
├── Сегодня
│   ├── current action / empty guidance
│   ├── compact day summaries
│   └── contextual sheets: date legend, quick cardio, quick water, check-in
├── Программа тренировок
│   ├── current program summary
│   ├── workout/day detail
│   ├── create simple program
│   └── templates / recommendation / history / advanced settings
├── Питание
│   ├── day summary + meals
│   ├── food picker: barcode -> name/brand -> quick/manual
│   ├── target/history/report detail
│   └── hydration detail/history (Task 81 placement)
├── Прогресс
│   ├── what changed summary
│   ├── measurements
│   ├── training
│   ├── nutrition reports
│   └── wellbeing history/insights (Task 82 placement)
└── Account/Profile
    ├── identity/avatar (Task 110 placement)
    ├── personal data and fitness profile
    ├── trainer and invitations
    ├── notifications/reminders (Task 84 placement)
    ├── auth methods / privacy / export / delete
    └── capability workspaces
```

## Feature layering matrix

| Функция                         | Layer              | Placement               | Presentation                           |
| ------------------------------- | ------------------ | ----------------------- | -------------------------------------- |
| Workout дня                     | Core now           | Сегодня                 | Always visible hero/action             |
| Empty day actions               | Core now           | Сегодня                 | 1–3 quick actions                      |
| Выбранная дата                  | Core now           | Today/Nutrition         | Compact WeekStrip                      |
| Cardio factual state            | Contextual         | Сегодня                 | Compact summary -> sheet               |
| Hydration Task 81               | Contextual         | Today + Nutrition       | Quick `+ Вода`; detail/history         |
| Sleep/Mood Task 82              | Contextual         | Today + Progress        | Optional check-in; history detail      |
| Reminders Task 84               | Secondary          | Profile/Notifications   | Compact settings summary               |
| Program current state           | Core now           | Программа               | Compact summary + primary action       |
| Create own program              | Core intent        | Программа               | Dedicated 3-step flow                  |
| Templates/recommendation        | Contextual         | Программа               | Choice sheet/detail                    |
| Program history                 | Advanced           | Программа               | Detail route                           |
| Exercise picker                 | Contextual         | Program/workout         | Full-height sheet                      |
| Exercise catalog                | Secondary          | Profile/More            | Detail route                           |
| Technique                       | Contextual         | Workout/catalog         | Detail sheet                           |
| Strength logging                | Core now           | Active workout          | Always visible controls                |
| Cardio logging                  | Core now           | Active cardio           | Always visible state-specific controls |
| RIR/set type/notes              | Advanced           | Active workout          | One disclosure or exercise detail      |
| Day nutrition summary           | Core now           | Питание                 | Compact summary                        |
| Meals                           | Core now           | Питание                 | Compact expandable rows                |
| Barcode/search/recent           | Contextual         | Food picker             | Single picker flow                     |
| Nutrition target/history/report | Secondary          | Питание/Прогресс        | Detail route                           |
| Progress conclusion             | Core now           | Прогресс                | Summary/bento                          |
| Charts/history                  | Contextual         | Progress                | Detail route/sheet                     |
| Missing data guidance           | Core state         | Прогресс                | One honest actionable state            |
| Profile completion              | Contextual         | Profile + relevant flow | Compact prompt, not gate               |
| Profile settings                | Secondary          | Profile                 | Compact index -> details               |
| Knowledge Task 85               | Public Web         | Public site             | Contextual handoff only                |
| Avatar Task 110                 | Secondary identity | AppShell/Profile        | No nav item                            |
| Progress bento Task 111         | Core summary       | Прогресс                | Semantic summaries -> details          |

## Semantic visual families

- `training`: directional lime field, cadence/trajectory geometry;
- `nutrition`: warm citrus/lime spectrum, portion/ring motifs;
- `progress`: precise graph/ruler grid, cooler graphite depth;
- `wellbeing`: softer wave/halo, lower urgency;
- `neutral/system`: calm paper/graphite surfaces without decorative competition.

Wow концентрируется на compact hero/summary/action surfaces. Forms, settings, tables, exercise/set
rows и expanded content используют спокойную neutral/system основу.

## Desktop rule

Desktop не растягивает mobile column. Today и Progress получают 2–3 смысловые колонки; Program
может показывать current program рядом с upcoming days; Nutrition — summary рядом с meal list.
Detail flows сохраняют ограниченную readable width. Навигация остаётся семантически равной mobile.

## Что нельзя потерять при реализации

- selectable Today date и различение today/selected;
- state-first cardio и future factual restriction;
- capability-gated trainer feedback;
- real local-first/external food search и barcode-first hierarchy;
- compact meals и draft/remount safety;
- overlay/keyboard/safe-area/BackButton contract;
- dirty-save/retry semantics;
- data confidence: missing != zero;
- private PDF/account/auth lifecycle и server authorization.
