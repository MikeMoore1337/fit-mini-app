# Task 115A — спецификация core flows

## 1. First run без обязательного onboarding

1. После auth пользователь попадает на `Сегодня`.
2. Empty hero объясняет: `С чего начнём?`.
3. Если программы нет, доступны два program intent: `Создать свою программу` (primary) и
   `Выбрать готовую` (secondary). Питание, активность и другие core-разделы остаются доступны через
   обычную навигацию и собственные contextual actions.
4. Profile completion не блокирует действие. Нужный параметр запрашивается контекстно и объясняет
   пользу; `Не сейчас` сохраняет доступ к core.
5. Success: создана первая программа, запись питания или фактическая активность; Today показывает
   сохранённый результат и следующий шаг.
6. Failure: введённые данные остаются, retry видим, возвращение не сбрасывает выбранный intent.

## 2. Создать свою программу

Базовый путь — 3 смысловых шага:

1. `Программа` -> `Создать свою программу`; название `Моя программа` и первая
   `Тренировка 1` уже заполнены.
2. Сразу выбрать первое упражнение через быстрый поиск; технику можно открыть до выбора и после
   добавления, не теряя черновик.
3. Проверить compact summary, `Создать программу` и перейти в `Сегодня`, где тренировку запускает
   только явное действие пользователя.

Обязательные API-поля получают явную beginner policy: `maintenance`, `beginner`, одна неделя,
первый день — сегодня, отдых — 90 секунд. Пользователь может изменить их в одном disclosure
`Настройки программы`. Расписание, rest presets, оборудование, reorder, supersets и detailed
progression не удаляются. Primary save никогда не находится внутри disclosure. Validation остаётся
рядом с причиной блока.

## 3. Начать и выполнить strength workout

1. Today/current program показывает один CTA `Начать тренировку` или `Продолжить`.
2. Active screen всегда показывает current exercise, set number, weight, reps и `Готово`.
3. Previous set и rest timer находятся рядом с current operation.
4. `Техника`, `История`, `Повторы в запасе`, тип подхода и note — contextual; не образуют nested
   accordion.
5. Offline save показывает `Сохранено на устройстве`; reconnect синхронизирует один раз.
6. Finish требует ясного summary; pending/error не схлопывает unsaved controls.

## 4. Active cardio

1. Today показывает planned/completed/empty factual state выбранного дня.
2. `Начать кардио` открывает отдельный active-cardio screen: activity, timer/duration, применимые
   distance/pace/heart-rate fields, pause/finish.
3. Strength-specific concepts (sets, reps, RIR) отсутствуют.
4. Future selected day не позволяет factual save; planning остаётся Program.
5. Completed result становится compact summary; `Добавить ещё` — secondary.

## 5. Добавить food / barcode

1. Nutrition meal `Добавить` открывает единый picker.
2. Первый явный entry — `Сканировать штрихкод`; ниже search по названию/бренду, recent/favorites.
3. Search empty честно предлагает external continuation/manual product без fake results.
4. External result `Выбрать` сохраняет normalized user food и переводит к количеству.
5. Amount/serving получает focus и остаётся видимым над keyboard; `Добавить в дневник` — primary.
6. Success возвращает в тот же meal без remount существующих drafts.

## 6. Проверить Progress

1. Top summary отвечает `что изменилось за выбранный период?`.
2. Data confidence видна рядом: достаточно / мало / нет данных.
3. One next action: добавить measurement, открыть тренировки либо дополнить diary — по state.
4. Training, nutrition, measurements и wellbeing открываются отдельными details.
5. Missing/unlogged не показывается как zero; strength/cardio не смешиваются.

## 7. Profile и settings

1. Profile index показывает identity/avatar, account role и compact completion summary.
2. Rows: `Личные данные`, `Цели и параметры`, `Тренер`, `Уведомления`, `Доступ и безопасность`.
3. Каждая row открывает отдельный detail screen; большие формы не раскрываются внутри index.
4. Save disabled в persisted state; dirty valid change включает Save; failure сохраняет values/retry.
5. Task 84 reminders default-off/quiet hours живут в Notifications. Task 110 avatar — в identity.

## Recovery и runtime acceptance

- `360/390/430`, touch, no hover dependency, target 44 px;
- bottom nav/sheet/CTA не перекрывают друг друга и safe area;
- keyboard оставляет field/error/primary/recovery достижимыми;
- TMA BackButton закрывает sheet/detail раньше app exit;
- reload/background/offline сохраняют recoverable draft по account/resource;
- light/dark и reduced motion имеют равную hierarchy;
- desktop reflow, не mobile stretch.
