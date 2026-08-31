# Canonical exercise data contract v2

## Цель

Контракт задаёт минимальные данные для global canonical exercise в 120B–120D. Он не меняет schema в 120A и не требует заполнения неизвестных фактов для custom exercise.

## Поля и текущая реализуемость

| Поле | Статус | Источник/правило |
|---|---|---|
| stable `slug`/ID | existing | `Exercise.slug`, DB ID; существующие slug не переименовывать |
| Russian display name | existing | `Exercise.title`; generic descriptive name |
| aliases/search synonyms/transliteration | missing-needs-decision | versioned code-owned alias registry для global catalog; API/search consumer должны его использовать |
| broad equipment | existing | legacy `equipment` + normalized `equipment_ids[]` |
| machine/load/path tags | missing-needs-decision | controlled catalog metadata: `smith`, `selectorized`, `plate_loaded`, `lever`, `independent`, `converging`, `diverging`; не свободный текст |
| primary muscles | existing | `exercise_muscles role=primary`; без fractional contribution |
| secondary muscles | existing | `exercise_muscles role=secondary`; только reviewed guide data |
| movement pattern | derivable | текущий `SLUG_TO_PROFILE`; вынести в canonical record/API, не выводить по title runtime |
| execution variant | missing-needs-decision | controlled tags `bilateral`, `unilateral`, `alternating`, `isometric`, `cyclic`, `multi_stage` |
| difficulty | existing | `beginner/intermediate/advanced`; product/editorial classification, не медицинская сложность |
| metric type | existing | только `strength/cardio` по Task 119; snapshot в program/workout |
| technique steps/breathing/mistakes | existing | reviewed guide profile; для нового item — item-specific проверка |
| safety cues | existing | non-medical factual cues; acute pain means stop, без diagnosis/treatment claims |
| visual example | partial existing | typed local media + manifest есть для 158 items, но 7 mappings подтверждённо неверны; semantic review обязателен |
| alternatives | existing | curated symmetric pairs; no self/duplicate; muscle match недостаточен |
| source/provenance/license | partial existing / missing-needs-decision | guide metadata + manifest/NOTICE есть; нет immutable upstream revision, asset SHA-256, reviewer/date и verification flags |

## Canonical seed record для 120B–D

Рекомендуемый deterministic baseline — один versioned code-owned record для global catalog:

```text
slug
display_name_ru
aliases[]
primary_muscle_ids[]
secondary_muscle_ids[]
equipment_ids[]
machine_variant_tags[]
movement_pattern
execution_variant_tags[]
difficulty_level
metric_type
guide_profile/item_content
media_reference
alternative_slugs[]
provenance
```

Его можно реализовать расширением текущего seed/catalog module и derived API payload без migration. Нельзя создавать второй расходящийся alias/media registry во frontend. Если 120B докажет необходимость редактировать эти поля для global catalog через DB/admin flow, это отдельное migration decision с backfill и validation, а не скрытое условие 120A.

## Media manifest v2 для human-visual assets

Task 120E сохраняет stable `media_reference` и code-owned architecture без новой
DB-модели. Для 18 machine/free-weight items manifest schema v2 связывает каждую
фазу с exact `asset_id`, `asset_version`, `variant_key`, explicit `phase_id`,
source-master SHA-256, responsive local sources `480/768/1280` и versioned
human-review record. API отдаёт клиенту только identity, phase, dimensions,
responsive URLs и безопасные source/license fields; generation lineage, rights и
review evidence остаются server-side manifest/documentation contract.

Display `phase` не используется как logic key. Frontend выбирает responsive source
через `srcset/sizes`, а отсутствие изображения сохраняет текстовую технику без
fallback на устаревший schematic asset. Legacy JPEG entries остаются совместимы:
API формирует для них один source и nullable asset/version/variant identity до их
отдельной remediation.

## Инварианты

1. `slug` уникален и стабилен; rename display не ломает history/API.
2. `metric_type` — `strength` или `cardio`; неизвестный legacy row безопасно остаётся `strength` по Task 119.
3. `cardio` не получает strength prescription; `strength` не получает cardio result fields.
4. Alias не создаёт новую exercise identity.
5. Brand/trademark alias не становится canonical display name.
6. Primary/secondary muscles не содержат придуманных коэффициентов.
7. Movement/equipment/execution tags выбираются явно редактором, не строковой эвристикой runtime.
8. Alternative требует movement/equipment/setup review и никогда не ссылается на себя.
9. Новый canonical item без semantically reviewed media или проверяемой file-level provenance не включается в releasable batch. Наличие manifest row недостаточно.
10. Missing metadata остаётся missing для custom rows; LLM/autofill не превращает предположение в факт.

## Metric type и Task 119

Все новые machine/free-weight/bodyweight items 120B–D имеют `strength`, кроме явно циклических cardio activities. `strength` здесь описывает форму workout logging, а не физиологическую категорию. Cardio items используют доступные Task 119 поля: duration, optional distance, average HR и zone; никакие calories/pace/power/cadence не добавляются этим audit.

## Variant decisions

- Grip, foot stance, seat micro-adjustment и обычная смена хвата — guide/alias metadata, не отдельный canonical item.
- Unilateral item создаётся отдельно, только если setup, execution или logging/selection materially отличаются (например unilateral leg press).
- Independent-arm machine может быть один canonical item с `bilateral` и `unilateral` execution tags, если то же оборудование поддерживает оба режима.
- Converging/diverging — machine path tag; это не обещание превосходства и не отдельный item без иного materially distinct setup.
- Selectorized/plate-loaded/lever — controlled equipment metadata. Не использовать `Hammer Strength` как required UI category.

## Content quality

Technique: setup, рабочая фаза, контролируемое возвращение/завершение. Common mistakes описывают наблюдаемое выполнение. Safety cues не обещают «безопасно для коленей/спины», не назначают ROM при боли и не заменяют консультацию специалиста.

## Validation, требуемая в 120B–D

- unique slug и normalized alias;
- allowed muscle/equipment/variant/metric values;
- no alias collision without explicit ranking decision;
- guide steps/mistakes/safety present;
- media reference exists, files decode, exact-duplicate scan выполнен, semantic reviewer подтвердил identity/setup/key positions, immutable provenance complete;
- alternative endpoints exist, differ from source and pass curated compatibility;
- every global item searchable by canonical name and required aliases;
- current 158 IDs/history remain intact.
