# Аудит текущего каталога упражнений

Дата среза: 31.08.2026. База: `origin/dev` `0d46b6e4b9669006244ad4a73bd4eeee4a4c617e`, включающая Task 119 (`1c18e30`).

## Методика и source of truth

Инвентаризация построена по фактическим данным и consumers:

- `backend/fitminiapp_api/services/program_seed_data.py` — 158 canonical seed-записей;
- `backend/fitminiapp_api/services/exercise_domain.py` — мышцы, оборудование, alternatives и provenance;
- `backend/fitminiapp_api/services/exercise_guides.py` — movement-profile proxy, техника и ошибки;
- `backend/assets/exercise-guides/manifest.json` — локальные media-файлы и фазы;
- `backend/fitminiapp_api/models/exercise.py` и `schemas/program.py` — фактический DB/API contract;
- `frontend/src/features/exercises/ExerciseCatalog.tsx` и `features/programs/ProgramBuilder.tsx` — реальный поиск и выбор;
- migrations `0064`–`0066` и `services/workout_metrics.py` — type-aware contract Task 119.

`COVERAGE_MATRIX.csv` содержит строку для каждого текущего canonical slug и отдельные gap/decision строки для 120B–120D. Movement pattern и execution variant в этом CSV — audit-классификация по текущему guide profile/названию, а не уже существующие DB-поля.

## Фактический состав

| Срез | Результат |
|---|---:|
| Canonical exercises | 158 |
| `strength` / `cardio` | 145 / 13 |
| Beginner / intermediate / advanced | 67 / 53 / 38 |
| Guide profiles | 158 из 158 |
| Manifest coverage | 307 JPEG entries для 158 exercises; это presence, не semantic validation |
| Exact cross-exercise duplicate sets | 8 пар slugs; 7 confirmed mismatches + 1 duplicate identity pair |
| Curated alternative pairs | 37 |
| Muscle identifiers | 26 |
| Equipment identifiers | 9 |

По broad equipment: 35 `machine`, 30 `dumbbell`, 26 `barbell`, 25 `bodyweight`, 17 `cable`, 8 `cardio`, 8 `other`, 7 `kettlebell`, 2 `bench`. Число `machine=35` завышает полезную machine coverage: в одну категорию попали selectorized, Smith, разные lever/plate-loaded движения и даже три cardio items.

По основным muscle/category labels: back 19, chest 17, cardio 13, triceps 11, quadriceps 10, legs 10, biceps 10, core 9, full body 8, hamstrings 8; остальные группы имеют 1–7 записей. Количество не равно полноте: один generic machine item не доказывает coverage разных траекторий или независимых рычагов.

## Что покрыто хорошо

- Базовые horizontal/vertical press и pull, free weights, cable и bodyweight представлены.
- Для ног есть squat/lunge/hinge, leg extension и три положения leg curl.
- Calves, core, carries и 13 cardio types имеют рабочую базу.
- Task 119 даёт только два валидных metric type: `strength` и `cardio`; legacy/null детерминированно считается `strength`.
- Для всех 158 seed items есть guide profile и manifest media entry. Полная semantic visual coverage не подтверждена: exact-hash audit ниже нашёл неверные mappings.
- Alternatives curated; совпадение основной мышцы само по себе не создаёт замену.

## Подтверждённые gaps

### Machine taxonomy

Текущий `equipment=machine` не отвечает, является ли тренажёр selectorized, plate-loaded, lever, Smith, converging/diverging или independent-arm. `Машина Смита` также нормализуется в broad `machine`. Поэтому фильтр и search не могут доказать отдельно требуемую coverage.

Must-gaps сосредоточены в реально отличающихся движениях: incline/independent lever chest press, high/low lever rows, independent lever pulldown/shoulder press, pendulum squat, plate-loaded/unilateral leg press, machine hip thrust и Smith split squat. Косметические grip/stance изменения не становятся отдельными canonical entities.

### Search

Alias model отсутствует. `ExerciseCatalog` делает case-insensitive substring по title, legacy muscle/equipment и названиям alternatives; `ProgramBuilder` — только по title, legacy muscle/equipment. Нет `ё -> е`, transliteration, token normalization, словоформ, slang, alias ranking или collision checks. Поэтому запросы `хаммер`, `рычажный`, `на блинах`, `plate loaded`, `lever` и `селекторный` не находят нужные generic canonical exercises, а alternative-title query ведёт себя неодинаково на двух surfaces.

### Naming и duplicates

- `goblet-squat` и `kettlebell-goblet-squat` описывают одну canonical связку «гоблет-присед + гиря» и требуют merge/redirect decision.
- `assault-bike`/`Assault bike` использует brand-like name как canonical display. Стабильный slug нельзя ломать, но display должен стать generic `Воздушный велотренажёр`; `assault bike`/`аэробайк` остаются только search aliases.
- `rowing-machine` (cardio) и `machine-row` (strength) по-русски слишком близки; выдача должна показывать metric/equipment context и не смешивать их по ambiguous alias.
- `hip-thrust` и `barbell-glute-bridge` не дубликаты, но первое название должно явно указывать опору на скамью, чтобы отличие от моста с пола было найдено без открытия guide.

### Cardio/equipment mismatch

`rowing-machine`, `treadmill-run` и `assault-bike` имеют `metric_type=cardio`, но legacy `Тренажер` нормализует их в equipment `machine`, а не `cardio`. Metric type остаётся правильным; equipment classification требует исправления в 120D без изменения исторических workout results.

### Semantic media audit

Manifest builder подтверждает decode/размер/path, но не соответствие изображения exercise identity. SHA-256 scan 307 файлов нашёл восемь пар разных canonical slugs, где совпадают обе фазы. Ручная проверка setup/key positions дала следующий verdict:

| Shared asset pair | Verdict | Must action |
|---|---|---|
| `barbell-row` / `pendlay-row` | Изображение показывает обычную тягу из виса; не Pendlay start с пола | заменить media `pendlay-row` |
| `goblet-squat` / `kettlebell-goblet-squat` | Один и тот же goblet squat; подтверждает canonical duplicate | history-safe merge, один visual set |
| `chest-dip` / `weighted-dip` | Внешнее отягощение не показано | заменить media `weighted-dip` либо merge только при product decision, не сейчас |
| `single-leg-calf-raise` / `standing-calf-raise` | Показан bilateral machine calf raise | заменить media `single-leg-calf-raise` |
| `hollow-hold` / `plank` | Показана plank sequence, не hollow hold | заменить media `hollow-hold` |
| `meadows-row` / `t-bar-row` | Показана обычная T-bar row | заменить media `meadows-row` |
| `captain-chair-leg-raise` / `hanging-leg-raise` | Показан свободный вис на перекладине, не captain chair | заменить media `captain-chair-leg-raise` |
| `belt-squat` / `hack-squat` | Показан hack squat machine | заменить media `belt-squat` |

Итого: 158/158 manifest presence, но минимум семь item-level visual mappings неверны; оставшиеся assets не объявляются полностью semantically reviewed только из-за отсутствия exact duplicate. Исправления входят must scope 120D и отражены отдельными decision rows matrix. Новый validator должен сочетать hash duplicate detection с human semantic review; один hash scan не доказывает корректность уникального файла.

### Content granularity

Текущие 158 entries переиспользуют 28 generic guide profiles. Это достаточная база для текущего каталога, но новые machine entries нельзя добавлять с автоматически скопированным generic текстом: setup, положение сиденья/опоры, траектория рычагов и key positions должны быть item-reviewed. Default safety cue не является медицинским обещанием и не заменяет specific common mistakes.

## Data-contract verdict

Existing fields достаточно для identity, display name, broad muscle/equipment, difficulty, metric type, базовой guide attribution и alternatives. Media provenance существующая только частично: manifest не хранит immutable upstream revision, file hash, reviewer/date и verification flags. Derivable без schema change: movement pattern, aliases и variant tags для global seed catalog, если они хранятся в одном versioned canonical record и возвращаются API. Missing-needs-decision: способ представления orthogonal machine/variant tags, file-level immutable provenance и lifecycle alias redirect после merge duplicate. Решение для 120B–D зафиксировано в `EXERCISE_DATA_CONTRACT.md`: сначала versioned code-owned catalog metadata без migration; DB expansion допускается только если implementer докажет, что custom/admin persistence или query plan реально её требует.

## Compact-first UX boundary

Новая taxonomy/media не меняет выбранный Task 115A `Command Stack`: catalog/program picker row остаётся компактной (name + key context + optional badges), guide и visual открываются по intent. Нельзя резервировать высоту под always-expanded technique/media или создавать вложенный accordion.

## Ограничения аудита

- Visual checkpoint: `N/A` — изменены только audit docs/CSV; production UI, layout, media assets и runtime не менялись.
- Production DB не читалась: audited canonical seed/current code, а не пользовательские custom rows.
- Реальный Telegram, физические устройства и viewports не проверялись: task не меняет UI/runtime.
- Audit не утверждает биомеханическую эквивалентность по совпадению muscle/pattern; alternatives остаются curated.
- External source verified для upstream repository/license, но текущий manifest не доказывает file-level immutable provenance или semantic correctness; новый asset проходит полный gate.
