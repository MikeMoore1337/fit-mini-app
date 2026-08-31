# Duplicates, naming и aliases

## Confirmed duplicate/merge decisions

| IDs | Severity | Решение | Проверка |
|---|---|---|---|
| `goblet-squat`, `kettlebell-goblet-squat` | must | Один canonical item `Гоблет-присед с гирей`; второй slug/ID не удалять destructively: определить canonical target, сохранить history compatibility и search redirect/alias | search даёт одну карточку; старые программы/история открываются |

## Naming corrections без смены stable slug

| Slug | Сейчас | Canonical display | Aliases |
|---|---|---|---|
| `assault-bike` | `Assault bike` | `Воздушный велотренажёр` | `air bike`, `аэробайк`, `assault bike` |
| `hip-thrust` | `Ягодичный мост со штангой` | `Ягодичный мост со штангой с опорой на скамью` | `hip thrust`, `хип траст`, `ягодичный мост на скамье` |
| `rowing-machine` | `Гребной тренажер` | `Гребля на кардиотренажёре` | `rowing machine`, `гребной эргометр` |
| `machine-row` | `Гребная тяга в тренажере` | `Горизонтальная тяга в тренажёре` | `machine row`, `гребная тяга`, `горизонтальная тяга` |

Изменение display name не меняет metric type, history или slug.

## Similar, но не duplicates

- `hip-thrust` (опора на скамью) и `barbell-glute-bridge` (с пола).
- `lat-pulldown` selectorized/cable и новый independent lever pulldown.
- `machine-chest-press` generic/selectorized и новый plate-loaded independent lever press.
- `leg-press` generic current item и новый explicitly plate-loaded/unilateral item — только если media/setup подтверждают distinct execution.
- `rowing-machine` cardio и `machine-row` strength.
- `pec-deck` chest fly и `reverse-pec-deck` rear delt.

## Required alias families

### Generic machine language

`тренажёр/тренажер`, `рычажный`, `lever`, `plate loaded`, `на блинах`, `селекторный`, `грузоблочный`, `независимые рычаги`, `конвергентный`, `дивергентный`.

`Hammer Strength`/`хаммер` может помогать найти generic lever/plate-loaded entries, но не становится canonical category, title или обязательной маркировкой UI.

### Script/transliteration

Reviewed English names и распространённая русская транслитерация: `lat pulldown`, `high row`, `low row`, `chest press`, `shoulder press`, `leg press`, `hack squat`, `pendulum squat`, `hip thrust`, `glute drive`, `air bike`, `smith`.

### Russian spelling/slang

Нормализовать `ё/е`; хранить только устойчивые варианты вроде `гакк`, `смит`, `аэробайк`, `бабочка`, `кроссовер`, `скамья Скотта`. Не добавлять бесконечные inflections: token normalization и проверяемый corpus важнее количества aliases.

## Collision risks

- `хаммер` описывает бренд/целое семейство, не одну exercise: match должен учитывать движение.
- `бабочка` может означать pec-deck или reverse pec-deck: без muscle/direction term выдавать обе компактные rows.
- `гребля` может означать cardio rower; `гребная тяга` — strength row. Exact alias/ranking обязаны различать.
- `ягодичный тренажёр` может означать hip thrust, kickback или abduction: это broad token, не unique alias.
- `пуловер` разделяет dumbbell/cable/machine variants; equipment term обязателен для exact alias.

## Validator rules

Normalize every title/alias, reject empty values and duplicate aliases inside one record, flag cross-record exact collisions, require explicit `ambiguous=true` decision for allowed broad terms, and verify redirect target exists. Validator must not auto-merge based on string similarity.
