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

`manifest.json` содержит проверяемый инвентарь: размеры, вес, порядок фаз и
provenance каждого файла. Он пересобирается командой
`python scripts/build_exercise_guide_media_manifest.py` и проверяется той же
командой с флагом `--check`.
