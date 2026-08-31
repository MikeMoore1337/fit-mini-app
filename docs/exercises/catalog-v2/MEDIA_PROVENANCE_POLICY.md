# Media provenance policy для каталога v2

## Release gate

Каждый новый global canonical exercise получает mobile-readable visual execution example до включения в releasable batch. Текстовая техника не заменяет visual. Отсутствие безопасного media — конкретный blocker для item, а не повод hotlink/copy.

## Разрешённые источники

1. Существующее repository-owned original media с подтверждаемой историей создания.
2. Новые оригинальные YFC human-visual illustrations/renders с анатомически
   читаемым человеком и конкретным оборудованием. Primitive schematic human,
   stick figure, skeleton-like/line-person и один тренажёр без человека не
   являются demonstration media, даже если файл технически валиден.
3. Third-party media только после file-level проверки лицензии на commercial use, modification (если выполняется), bundling/redistribution и нужный способ attribution.

Текущие third-party assets происходят из [`free-exercise-db`](https://github.com/yuhonas/free-exercise-db). На дату аудита upstream repository называет dataset public-domain, а [`LICENSE.md`](https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md) содержит Unlicense и явно разрешает commercial/non-commercial use и distribution. Это подтверждает текущую policy, но не позволяет автоматически считать любой новый web asset частью того же набора: каждый файл должен быть сопоставлен с upstream path/revision и manifest record.

### Current-state boundary

Manifest schema v2 для human-visual набора Task 120E фиксирует versioned local
paths, responsive sources, dimensions, byte size, explicit `phase_id`, asset и
variant identity, SHA-256, generation lineage и versioned human-review status.
Existing `free-exercise-db` media сохраняет legacy source/license baseline; восемь
найденных ранее cross-exercise duplicate pairs и семь semantic mismatches относятся
к remediation Task 120D и не объявляются исправленными Task 120E.

## Запрещено

- competitor screenshots/animations или их перерисовка один-в-один;
- random web images и hotlink;
- media без source URL/revision/license evidence;
- packaging/logo/public-figure likeness и trademarks как decorative proxy;
- generated anatomy/trajectory, представленная как проверенный факт без human domain review;
- primitive schematic human, stick figure, skeleton-like/line-person и
  абстрактная траектория вместо читаемого положения человека;
- fake charts, ranges, joint angles или «идеальная техника» без источника;
- autoplay со звуком или animation-only explanation.

## Reusable visual format

Baseline для 120B–D — две статические key positions `Начало` -> `Конечное положение` либо domain-reviewed phase labels. Для cyclic/multi-stage/cardio допускается одна human-readable composition или несколько key positions с нейтральными labels. Схематичная концепция человека не допускается.

В guide это одна спокойная responsive composition: на ширине, где каждая позиция сохраняет читаемый размер, фазы стоят рядом; иначе они переходят в вертикальную последовательность без horizontal scroll. Короткий phase index/стрелка может использовать lime как YFC accent, но направление также выражено порядком и текстовой подписью. Visual не конкурирует с названием и шагами техники, а catalog row содержит только одно явное действие открытия guide.

Требования:

- локальные same-origin assets, без runtime CDN;
- `image` baseline; video только отдельным validated pilot;
- исходные width/height, `object-fit: contain`, lazy loading и async decoding;
- readable при 360 px без обязательного zoom;
- одинаковая framing/orientation для пары, если это не искажает движение;
- no decorative crop body/joint landmarks;
- stable `media_reference`, deterministic `sort_order`, poster/fallback;
- machine-readable `phase_id`, `asset_id`, `asset_version`, `variant_key` и
  responsive `sources`; display label не используется как logic key;
- reduced-motion не теряет информацию.

## Alt/accessibility

Alt описывает exercise, позицию и различимый action cue, а не имя файла: например `Рычажный жим от груди: исходное положение, рукояти у груди` и `... конечное положение, руки выпрямлены без жёсткой блокировки`. Подпись и текст техники остаются доступны при image error. Цвет/стрелка не являются единственным носителем направления.

## Provenance record

Для каждого файла/illustration хранить:

```text
exercise_slug
asset_path
asset_sha256
source_kind: yfc_original | commissioned | third_party | ai_generated
asset_type: photo | render_3d | raster_illustration | human_like_vector
asset_version
variant_key
source_name
source_url
source_revision_or_retrieved_at
license_name
license_url_or_local_notice
commercial_use_verified: true
redistribution_verified: true
modification_verified: true|false|not_needed
model_release_status/property_release_status: verified | not_applicable | blocked
author_or_generator_record: provider/model/version/job-or-seed/prompt-or-brief/input lineage
reviews: domain/anatomy/equipment/phase/visual_style/mobile/legal with reviewer/date/status
width/height/byte_size
phase/sort_order/alt
```

`commercial_use_verified` — audit evidence, не юридическая гарантия. Неизвестное значение означает `blocked`, а не `false-but-ship`.

## YFC original illustration workflow

Brief фиксирует exact exercise, `variant_key`, setup, key positions, camera/framing и запрещённые misleading детали. Создатель/генератор и input lineage записываются. Fitness-domain reviewer вручную проверяет exact revision: movement identity, equipment setup, anatomy, grip/feet/contact points, left/right consistency, load path, phase order и отсутствие unsafe/невозможной позиции. Отдельный visual/mobile review подтверждает читаемость без zoom. Затем media builder проверяет только объективные invariants: decode, размеры, hashes, responsive derivatives, manifest и unexpected files.

AI-generated visual допустима только как YFC-controlled draft при достаточных правах выбранного provider/workflow и human review; model output не является источником техники. Automated validator не может выставить semantic/anatomy approval. Approval относится к exact asset hash/version и не переносится на новую генерацию или вариант упражнения.

## Third-party workflow

1. Зафиксировать exact upstream file path и immutable revision/hash.
2. Сохранить license text/URL и применимость к конкретному asset.
3. Проверить commercial use и redistribution, а при crop/annotation — modification.
4. Скопировать локально; hotlink запрещён.
5. Заполнить manifest/NOTICE и attribution payload.
6. Прогнать builder `--check` и representative visual review.

## UI boundary

Media открывается только по intent в guide/detail. Catalog row не резервирует media height и не становится always-expanded. Error state сохраняет text technique и честно сообщает недоступность изображения.
