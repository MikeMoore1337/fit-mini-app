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

Файлы `*.svg` для batch Task 120B созданы специально для Your Fitness Coach
детерминированным скриптом `scripts/build_upper_body_machine_guide_assets.py`.
Это оригинальные схематические key-position illustrations без сторонних логотипов,
изображений людей и внешних media. Сопоставление exercise/setup/key positions и alt-текст
проверены в domain-review Task 120B; сведения о проверке и SHA-256 каждого файла находятся
в `manifest.json`.

`manifest.json` содержит проверяемый инвентарь: размеры, вес, порядок фаз и
provenance каждого файла; для новых SVG Task 120B также хранится SHA-256. Он пересобирается командой
`python scripts/build_exercise_guide_media_manifest.py` и проверяется той же
командой с флагом `--check`.
