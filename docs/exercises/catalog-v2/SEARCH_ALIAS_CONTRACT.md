# Search alias contract v1

## Проблема

Текущий `ExerciseCatalog` фильтрует загруженный список простым substring по `title`, legacy muscle/equipment и alternative titles. `ProgramBuilder` использует только `title`, legacy muscle/equipment и поэтому не находит запись по названию alternative. Alias fields, transliteration, `ё/е` normalization, token matching и ranking отсутствуют на обеих surfaces.

## Минимальный contract 120B–D

Для global canonical exercise хранить versioned `aliases[]` рядом с canonical seed metadata и возвращать их обоим search consumers. Frontend-only hardcode запрещён: catalog и ProgramBuilder должны использовать один payload/normalizer.

### Нормализация

1. Unicode NFKC.
2. Locale-independent case folding/lowercase.
3. `ё -> е` для поиска, без изменения display string.
4. Hyphen, slash и punctuation -> space; whitespace collapse.
5. Latin/Cyrillic transliteration не генерировать автоматически: хранить reviewed variants.
6. Query разбивается на tokens; все meaningful tokens должны присутствовать в одном canonical record.

Полноценный fuzzy/stemming engine не нужен. Common typo добавляется явным alias только после query evidence. Отсутствие generic typo tolerance должно быть честно покрыто no-result state, а не случайным broad match.

### Ranking

Детерминированный порядок:

1. exact canonical title;
2. exact alias;
3. canonical-title prefix;
4. alias prefix;
5. all-token substring;
6. текущий difficulty/order tie-breaker.

Один canonical entity выводится один раз, даже если совпали несколько aliases. Generic tokens `machine/тренажёр/рычажный` не должны вытеснять exact movement result.

### Collision policy

- Normalized alias уникален, если он обозначает конкретное упражнение.
- Ambiguous gym term разрешён только как broad search token и обязан возвращать несколько явно различимых rows, а не скрыто выбирать одну.
- После merge duplicate старый title/slug становится redirect/search alias canonical target; history ID не переписывается destructively.
- Brand-like term допустим только как non-display alias при реальной findability ценности.

## Обязательный query corpus

| Query | Ожидание |
|---|---|
| `жим в хаммере` | generic independent/lever chest press; `хаммер` не display category |
| `рычажный жим грудь` | lever chest press records |
| `на блинах грудь` / `plate loaded chest press` | plate-loaded chest press |
| `конвергентный жим` | converging/independent machine press |
| `верхняя рычажная тяга` / `high row` | lever high row |
| `нижняя рычажная тяга` / `low row` | lever low row |
| `вертикальная рычажная тяга` | independent lever pulldown |
| `смит присед` / `smith squat` | existing Smith squat |
| `гакк` / `hack squat` | existing hack squat |
| `маятниковый присед` / `pendulum squat` | new pendulum squat |
| `жим ногами на блинах` | plate-loaded leg press |
| `ягодичный тренажер` / `glute drive` | machine hip thrust |
| `сгибание ног сидя/лежа/стоя` | ровно соответствующий current item |
| `аэробайк` / `air bike` / `assault bike` | generic air bike canonical item |
| `гребля тренажер` | cardio rower выше strength machine row |
| `гребная тяга` | strength machine row выше cardio rower |
| `подъем` и `подъём` | одинаковый result set |
| `goblet squat` / `гоблет` | один canonical result после merge |

120B/C добавляют aliases для своих новых/затронутых items и проверяют representative queries. 120D завершает общий corpus, collision validator и обе search surfaces.

## API/UI boundary

API payload получает `aliases: string[]`, `movement_pattern` и controlled variant tags, если они реализованы. Display row остаётся compact-first: title, muscle/equipment context, difficulty/metric badge. Alias/trademark не показывается как второе длинное название; при необходимости match reason можно показывать коротко и только для неочевидного результата.

## Не входит

- отдельный search engine;
- AI/LLM query expansion;
- runtime перевод названий;
- SEO pages для каждого alias;
- автосоздание canonical exercises из no-result query.
