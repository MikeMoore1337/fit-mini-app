# Task 115A — аудит текущего UX

## Статус и границы доказательств

Аудит выполнен на `dev` до изменения production-кода. Источники: фактический render текущего
frontend через существующие Playwright API-fixtures, mocked Telegram adapter, локальный `/login`,
текущий React-код и принятые UX-контракты. Проверены viewport `360x800`, `390x844`, `430x932`,
`768x900`, `1280x900` и `1440x900`, light/dark там, где это предусмотрено сценариями.

Это **не** real Telegram, physical-device, production-data или real-user evidence. Mocked API
подтверждает фактическую композицию и interaction contract, но не полевую скорость и не поведение
реальной клавиатуры Telegram iOS/Android.

Current-state screenshots лежат в ignored-пакете `.artifacts/task-115A/current-state/`.

| Screenshot map                                                                            | Runtime / viewport                   | Поверхность                   |
| ----------------------------------------------------------------------------------------- | ------------------------------------ | ----------------------------- |
| `01-today-mobile-web-360-light.png`, `05-today-desktop-1280-light.png`                    | mocked Mobile Web / Desktop          | Today                         |
| `02-today-mock-tma-360-light.png`, `03-progress-mock-tma-390-dark.png`                    | mocked TMA                           | Today / Progress              |
| `04-nutrition-barcode-mock-tma-430-dark.png`, `12-food-search-mock-tma-390-dark.png`      | mocked TMA                           | Barcode / food search         |
| `06-program-stepper-mobile-360-light.png`, `07-program-result-mobile-390-light.png`       | mocked Mobile Web                    | Program builder / result      |
| `08-profile-mobile-390-light.png`, `09-profile-desktop-1440-light.png`                    | mocked Mobile Web / Desktop          | Profile / settings entry      |
| `10-active-workout-mock-tma-390-dark.png`, `11-cardio-state-first-mock-tma-390-light.png` | mocked TMA                           | Strength / cardio             |
| `13-food-selected-mobile-web-360.png`, `14-nutrition-meal-mobile-360.png`                 | mocked Mobile Web                    | Food selection / compact meal |
| `knowledge-mobile-390-dark.png`, `knowledge-desktop-1440-dark.png`                        | local public Web                     | Knowledge Base                |
| `login-mobile-390-light.png`                                                              | local Web, backend unavailable state | Login / recovery              |

Notification center отдельно проверен существующим mocked Mobile Web/TMA parity test: populated
state, unread geometry, destructive action affordance и TMA BackButton return path. Скриншот этого
state не используется как real Telegram evidence.

## Карта текущего пути

```text
Landing
  -> /login
     -> OAuth / Telegram initData
        -> обязательный onboarding gate для нового Web-пользователя
           -> выбор цели
           -> выбор следующего действия
        -> /app
           -> Сегодня
           -> План
           -> Прогресс
           -> Питание
           -> Ещё
              -> Упражнения
              -> Профиль и настройки
              -> База знаний (только Web)
              -> Кабинет тренера / Admin по capability
```

Кодовые опоры: `frontend/src/app/OnboardingGate.tsx`,
`frontend/src/pages/onboarding/OnboardingPage.tsx`, `frontend/src/app/AppShell.tsx`,
`frontend/src/pages/miniapp/MiniAppPage.tsx`.

## Наблюдения по основным поверхностям

### Login и callback

- Canonical browser entry `/login`, TMA с валидным `initData` проходит без второго login.
- Provider list capability-driven; callback не показывает raw code/error payload.
- При недоступном backend локальный render честно показывает recovery action `Повторить`.
- Desktop login строит отдельную continuation-композицию, mobile сохраняет фирменный lockup.
- Целевой reset не меняет auth contract; только упрощает переход к первой ценности после входа.

### First run / onboarding

- Новый Web-пользователь обязан пройти отдельный экран выбора цели до `/app`.
- Текущий минимальный путь: выбрать цель -> `Продолжить` -> выбрать, с чего начать. Это 2
  смысловых действия, но gate всё равно обязателен и отделяет пользователя от продукта.
- Пол, возраст, рост и вес уже не запрашиваются на первом шаге — это хорошая существующая
  progressive-disclosure опора.
- Target: убрать обязательный wizard. Новый пользователь сразу видит `Сегодня` с 1–3 действиями;
  цель предлагается контекстно, когда она улучшает программу или КБЖУ.

### Сегодня

- Сильная сторона: выбранная дата действительно меняет planned/factual state; workout hero даёт
  понятное primary action.
- На mobile initial viewport тренировка доминирует, но питание уже начинается ниже сгиба, а
  дополнительные Today-секции продолжают длинную ленту.
- На desktop текущая композиция лучше: workout, nutrition и progress summaries образуют
  scan-friendly сетку, cardio остаётся отдельным нижним блоком.
- Empty day показывает полезные переходы, но конкуренция Today quick actions зависит от state.
- Cardio уже state-first: пустая форма не занимает экран, planned/completed различены.

Кодовые опоры: `TodayDashboard`, `WeekStrip`, `CardioQuickLog` в
`frontend/src/features/dashboard/TodayDashboard.tsx`.

### Программа / подбор / builder / templates

- Текущий mobile nav label — `План`; target locked label — `Программа`.
- Recommendation wizard имеет 5 шагов (`Цель`, `Опыт`, `Частота`, `Место`, `Оборудование`) и
  отдельный result/preview. Для осознанного подбора это объяснимо, но не является коротким входом
  в собственную программу.
- На одном разделе соседствуют templates, recommendation, active/history state и большой
  `ProgramBuilder`; пользователь выбирает между несколькими моделями до того, как понятен основной
  intent.
- Builder уже содержит отдельные advanced disclosures, но основной экран остаётся длинным из-за
  расписания, дней и упражнений в одном layer.
- Target разделяет: current program summary -> `Начать/Продолжить`; `Создать программу` как простой
  базовый flow; templates/recommendation/import/history — contextual/detail.

Кодовые опоры: `TemplatesList`, `ProgramRecommendation`, `ProgramBuilder`,
`AssignedProgramDetails`, `HistoricalProgramWorkout`.

### Exercise picker и техника

- Каталог является отдельным secondary разделом и открывается через `Ещё`/desktop sidebar.
- Compact rows и отдельная `Техника и детали` уже сохраняют полезную metadata и 44 px touch target.
- В target каталог остаётся secondary capability, но picker открывается в контексте Program и
  active workout; техника — detail sheet, не новый top-level раздел.

### Active workout: strength и cardio

- Strength logger хорошо обозначает текущий подход, позволяет ввести вес/повторы и завершить set;
  offline draft/reconnect уже проверяется.
- Secondary guidance, injury action, technique, progression explanation и advanced set options
  могут оказаться между workout status и logging rows, создавая высокий scroll cost.
- Primary/current logging controls нельзя сворачивать. `Почему?`, техника, RIR, тип подхода,
  история и заметки должны жить на одном contextual level либо на detail sheet.
- Cardio должен быть отдельным active state: вид активности, длительность, дистанция/пульс по
  применимости, timer/current status и `Завершить`; не имитировать strength set table.

### Питание / search / barcode

- Locked search hierarchy уже реализована: barcode -> поиск по названию/бренду -> quick/manual.
- External result выбирается, сохраняется в `Мои продукты`, затем фокусируется количество.
- Meal sections компактны, сворачиваемы и сохраняют `Добавить` без раскрытия.
- Day summary, week strip, completeness state, meals, targets/history/reports всё ещё могут
  формировать длинный экран при одновременном раскрытии.
- Target сохраняет текущие contracts, но initial layer ограничивает экран day summary + meals;
  targets/history/reports уходят в detail routes/sheets.

Кодовые опоры: `NutritionDiary`, `FoodPickerDialog`, `BarcodeLookup`,
`NutritionTargetHistory`, `NutritionReport`.

### Прогресс

- Data confidence честно отличает missing/insufficient/limited data от нуля.
- Текущий раздел последовательно рендерит schedule, measurements, confidence cards, analytics,
  history и reports. На `390x844` representative screenshot находится глубоко внутри ленты и
  показывает несколько однотипно акцентных missing-data cards.
- Target верхний layer отвечает только на `что изменилось?`; один summary/bento + next action.
  Измерения, тренировки и питание открываются в detail layer. Missing data получает один общий
  actionable state вместо серии повторяющихся пустых карточек.

Кодовые опоры: `ProgressSchedule`, `ProgressExperience`, `Diary`, `WorkoutHistory`,
`NutritionReport`.

### Profile / settings / auth methods / notifications

- Profile completion prompt уже capability-aware и исчезает при `3/3`.
- Семантические disclosure-card и dirty-save semantics являются хорошими anchors.
- При incomplete profile mobile initial viewport занят hero, completion card, section nav и
  началом первой expanded section; основной список настроек читается как длинная страница.
- Target оставляет identity + completion summary наверху. Личные данные, цели, тренер,
  уведомления и безопасность — компактные rows, каждая ведёт на отдельный detail screen.
- Notifications default-off/quiet hours остаются в Profile; Today показывает reminder только если
  он actionable.

### Knowledge Base

- В Web доступна через secondary navigation; в TMA отдельного index/reader нет.
- Target сохраняет Public Web-first. В app остаются только техника, короткое `Что это?` и
  contextual handoff на public article.

## Дубли и неоднозначности

| Концепт                   | Текущее проявление                                      | Target решение                         |
| ------------------------- | ------------------------------------------------------- | -------------------------------------- |
| План/программа            | nav `План`, recommendation, templates, builder, history | единый nav `Программа`, intents внутри |
| Прогресс/измерения/отчёты | несколько длинных блоков одного уровня                  | summary -> тематический detail         |
| Каталог упражнений        | отдельный раздел и picker-context                       | каталог secondary, picker contextual   |
| Профиль/настройки         | hero + anchor nav + disclosures на одной странице       | compact index -> detail screen         |
| Knowledge                 | Web nav и contextual help                               | Public Web-first, context-only в TMA   |

## Action-count baseline

Счёт — смысловые решения, не каждое техническое касание.

| Сценарий                          | Текущий путь                                                                      |                              Оценка |                                         Target |
| --------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------: | ---------------------------------------------: |
| Новый пользователь до core        | login -> goal -> next action -> app                                               | 2 после входа, но обязательный gate |                   1: выбрать действие на Today |
| Начать запланированную тренировку | Today -> `Начать тренировку`                                                      |                                   1 |                                              1 |
| Создать свою программу            | План -> открыть builder -> заполнить основу -> добавить дни/упражнения -> создать |  5+ решений на одном длинном экране | 3: название/default -> день -> упражнение/save |
| Добавить еду поиском              | Питание -> meal `Добавить` -> search -> выбрать -> количество -> add              |                                   5 |                         4; recent может дать 3 |
| Добавить по barcode               | Питание -> meal -> barcode -> scan/find -> amount -> add                          |                                   5 |                        4 с явным barcode entry |
| Понять Progress                   | Progress -> найти релевантный блок -> интерпретировать confidence                 |                   зависит от scroll |                1 summary + 1 detail при intent |
| Изменить notifications            | Ещё -> Профиль -> Уведомления -> раскрыть/изменить                                |                                 3–4 |                           3, без anchor-scroll |

## Вывод

Production уже содержит сильные локальные contracts — state-first cardio, real food search,
compact meals, data confidence, dirty-save, TMA adapter. Главная проблема не отсутствие функций,
а их presentation как соседних равноправных sections. UX reset должен менять hierarchy и
layering, а не заново изобретать backend/domain behavior.
