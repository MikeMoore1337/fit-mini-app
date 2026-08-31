# Источник иллюстраций

Файлы `*-start.jpg` и `*-active.jpg` получены из проекта
[yuhonas/free-exercise-db](https://github.com/yuhonas/free-exercise-db).

Набор опубликован на условиях [Unlicense](https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md)
и относится авторами к общественному достоянию. Имена файлов адаптированы к
внутренним идентификаторам Your Fitness Coach; изображения не изменялись.

Сопоставление и воспроизводимый скрипт загрузки находятся в
`scripts/sync_exercise_guide_assets.py`.

Файлы `*-technique.jpg` для девяти cardio-упражнений созданы специально для
Your Fitness Coach и не используют материалы Fitness Online или удалённый media API.
Они учитываются как собственные материалы приложения.

Файлы `*-technique.jpg` для `bodyweight-glute-bridge`, `dead-hang`, `pendlay-row`,
`weighted-dip`, `single-leg-calf-raise`, `hollow-hold`, `belt-squat` и `wall-sit`
созданы специально для Your Fitness Coach через OpenAI built-in `image_gen`. Для каждого
упражнения выполнен отдельный generation call без стороннего reference image; логотипы,
trademarks и узнаваемые реальные лица не использовались. Exact hashes и результаты agent
visual inspection identity/setup/key positions находятся в
`docs/exercises/catalog-v2/120D_MEDIA_REVIEW.json`.
Production derivatives уменьшены до ширины 1280 px и сохранены как JPEG quality 88;
неизменённые source masters остаются вне production bundle.

Файлы `human-v1/**/*.webp` для 18 упражнений Tasks 120B–120C созданы в
YFC-controlled workflow Task 120E через OpenAI built-in `image_gen`. Входами были
текстовые production briefs и созданные в том же наборе YFC assets для pair-lock;
сторонние изображения, узнаваемые реальные лица, логотипы и trademarks не
использовались. Source masters являются review artifacts и не входят в production
bundle.

Каждая из 36 фаз вручную проверена на exercise identity, оборудование, анатомию,
опоры, направление движения, единый стиль и читаемость на мобильном экране.
Production содержит только оптимизированные responsive WebP `480/768/1280` с
versioned local URL. Exact hashes, variant binding, generation record, ограничения
правового review и статусы owner gates находятся в `manifest.json` и
`docs/exercises/catalog-v2/120E_ASSET_REVIEW.json`. Воспроизводимая derivative
pipeline: `scripts/build_exercise_human_visual_assets.py`.

`manifest.json` schema v2 содержит проверяемый инвентарь: размеры, вес, responsive
sources, explicit `phase_id`, asset/version/variant identity, hashes и provenance.
Он пересобирается командой
`python scripts/build_exercise_guide_media_manifest.py` и проверяется той же
командой с флагом `--check`.

Быстрый catalog-wide gate `python scripts/validate_exercise_catalog.py` дополнительно
проверяет required fields, taxonomy, aliases/redirect, media references, SHA-256 и exact
cross-canonical duplicates.
