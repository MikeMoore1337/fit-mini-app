# Expansion batches 120B–120D

Приоритет означает coverage usefulness, а не quota. `Must` item входит в Definition of Done своего batch либо возвращается как конкретный media/data blocker. `Should` выполняется после must в пределах task. `Optional` не блокирует family.

## Task 120B — upper-body machine

### Must: новые canonical items

| ID | Display name | Pattern / metadata | Почему gap |
|---|---|---|---|
| `machine-incline-chest-press` | Жим от груди вверх в тренажёре | chest press; machine; selectorized/lever | incline machine press отсутствует |
| `independent-lever-chest-press` | Жим от груди в независимом рычажном тренажёре | horizontal press; plate-loaded lever; independent | generic `machine-chest-press` не описывает independent lever setup |
| `lever-high-row` | Верхняя рычажная тяга с упором грудью | row; plate-loaded lever; independent/bilateral | high-row trajectory отсутствует |
| `lever-low-row` | Нижняя рычажная тяга с упором грудью | row; plate-loaded lever; independent/bilateral | low-row trajectory отсутствует |
| `independent-lever-lat-pulldown` | Вертикальная рычажная тяга независимыми руками | vertical pull; plate-loaded lever | current pulldown не различает cable/selectorized и lever |
| `machine-pullover` | Пуловер в тренажёре | shoulder extension/pullover; machine | есть dumbbell/cable, machine gap подтверждён |
| `independent-lever-shoulder-press` | Жим над головой в независимом рычажном тренажёре | vertical press; plate-loaded lever | current generic machine press не покрывает independent arms |

### Should

- `machine-decline-chest-press` — decline machine press, если media/setup действительно distinct.
- `machine-triceps-extension` — selectorized elbow extension; не дублировать machine dip.
- `chest-supported-dumbbell-row` — free-weight supported row; можно перенести в 120D, если media budget 120B исчерпан.

### Alias/merge decisions в этом batch

- `жим в хаммере`, `hammer press`, `рычажный жим`, `на блинах` ведут к generic lever items, но brand не показывается как category.
- `high row`, `верхняя тяга хаммер`, `low row`, `нижняя тяга хаммер`, `iso-lateral` — reviewed aliases.
- Existing `machine-biceps-curl` принимает `сгибание на скамье Скотта в тренажёре` как alias, если setup совпадает; отдельный canonical item без distinct media не создавать.

### Representative gate

Exact/alias search, one selectorized and one plate-loaded item, independent-arm execution, program add, strength logging, guide/media/alt, compact catalog row.

## Task 120C — lower-body machine

### Must: новые canonical items

| ID | Display name | Pattern / metadata | Почему gap |
|---|---|---|---|
| `pendulum-squat` | Маятниковый присед в тренажёре | squat; plate-loaded lever; bilateral | distinct machine path отсутствует |
| `plate-loaded-leg-press` | Жим ногами в тренажёре с дисками | squat/press; plate-loaded | current generic `leg-press` не подтверждает load type/setup |
| `unilateral-leg-press` | Жим одной ногой в тренажёре | squat/press; machine; unilateral | materially distinct execution отсутствует |
| `machine-hip-thrust` | Ягодичный мост в рычажном тренажёре | hip extension; lever; bilateral | current barbell/floor variants не покрывают glute-drive setup |
| `smith-split-squat` | Сплит-присед в машине Смита | lunge; Smith; unilateral | Smith lower-body gap кроме bilateral squat |
| `machine-glute-kickback` | Разгибание бедра назад в тренажёре | hip extension; machine; unilateral | есть cable variant, machine setup отсутствует |

### Should

- `v-squat-machine` — generic V-squat/lever squat, только с distinct media от hack/pendulum.
- `reverse-hyperextension` — posterior-chain machine, не путать с current hyperextension.
- Unilateral execution для current leg extension/curl хранить как variant/guide option, не создавать дубликат без distinct setup.

### Alias/merge decisions в этом batch

`жим ногами на блинах`, `pendulum squat`, `маятник`, `glute drive`, `ягодичный тренажёр`, `смит сплит`, `smith lunge`; foot stance aliases не создают отдельные entities.

### Representative gate

Plate-loaded vs selectorized context, Smith, unilateral, quads/hamstrings/glutes/calves coverage, program add, strength logging, guide/media/alt, compact row.

## Task 120D — remaining coverage + search hardening

**Финальный статус 31.08.2026:** выполнено. Добавлены шесть canonical items,
`high-to-low-cable-fly` намеренно объединён с `cable-fly` как направление/alias,
`chest-supported-dumbbell-row` уже закрыт Task 120B. Legacy
`kettlebell-goblet-squat` сохранён для истории и направляет search consumers на
`goblet-squat`. Все обязательные media mismatches исправлены; дополнительно validator
обнаружил и закрыл неверный shared visual `wall-sit`/`bodyweight-squat`.

Search использует общий NFKC/`ё -> е`/punctuation/token contract, явный relevance
ranking и canonical grouping в каталоге и ProgramBuilder. Быстрый deterministic
validator проверяет 182 stored / 181 surfaced canonical records, таксономии, aliases,
redirect, guide content, provenance, 347 media items, 419 файлов/derivatives, hashes и
отсутствие cross-canonical exact media duplicates.

### Must: content/data corrections

1. Merge decision `goblet-squat` + `kettlebell-goblet-squat` с history-safe compatibility.
2. Rename display `assault-bike` -> `Воздушный велотренажёр`; сохранить slug и aliases.
3. Развести search/ranking `rowing-machine` cardio и `machine-row` strength.
4. Reclassify `rowing-machine`, `treadmill-run`, `assault-bike` under cardio equipment while preserving `metric_type=cardio` and historical snapshots.
5. Implement shared aliases/normalization/ranking and complete query corpus from `SEARCH_ALIAS_CONTRACT.md` in catalog и ProgramBuilder.
6. Add deterministic catalog validator for required fields, allowed taxonomy, unique normalized aliases, existing media/provenance and valid metric type.
7. Replace semantically wrong visual mappings for `pendlay-row`, `weighted-dip`, `single-leg-calf-raise`, `hollow-hold`, `meadows-row`, `captain-chair-leg-raise` and `belt-squat`; do not modify production assets in 120A.
8. Extend media validation with exact cross-exercise hash detection plus recorded human identity/setup/key-position review. Unique hash alone is not a semantic pass.

### Must: remaining canonical items

| ID | Display name | Coverage |
|---|---|---|
| `bodyweight-squat` | Приседания с собственным весом | quads/glutes; squat; bodyweight; bilateral; strength |
| `bodyweight-glute-bridge` | Ягодичный мост с собственным весом | glutes; hip extension; bodyweight; bilateral; strength |
| `barbell-wrist-curl` | Сгибание кистей со штангой | forearms; wrist flexion; barbell; bilateral; strength |
| `barbell-wrist-extension` | Разгибание кистей со штангой | forearms; wrist extension; barbell; bilateral; strength |

### Should

- `dead-hang` — grip/bodyweight/isometric.
- `high-to-low-cable-fly` — distinct cable direction, если current guide/media не может быть variant текущего fly.
- `recumbent-bike` — distinct cardio setup; Task 119 metric remains cardio.
- `chest-supported-dumbbell-row`, если не вошёл в 120B.

### Optional/deferred

Arm ergometer, rare specialty machines, cosmetic grip/stance variations, manufacturer-specific machines and separate canonical items for every independent-arm mode. Они не блокируют matrix после must/should decisions.

Финальный статус этих optional-пунктов: `deferred optional`; конкретного пользовательского
coverage blocker для отдельного canonical item не обнаружено.

## Общие запреты

- Не менять существующие stable slugs/IDs destructively.
- Не добавлять item без reviewed technique, media и provenance.
- Не добавлять `calories burned`, power/cadence/pace или новый metric type.
- Не выводить alternative только из muscle match.
- Не начинать 120B/120C/120D из этой task.
