---
name: document-import-engineer
description: >
  Design, implement or review safe deterministic import of structured XLSX, CSV, DOCX or TXT data
  through validation, parsing, normalization, preview, matching and confirmed canonical writes.
  Use for document/spreadsheet import workflows. Do not use for generic uploads or exports that do
  not parse user files into domain entities.
---

# document-import-engineer

Импорт - это недоверенный data ingestion pipeline. Файл не становится каноническими данными сразу
после upload.

## Обязательный pipeline

```text
upload
-> file validation
-> bounded parsing
-> neutral draft
-> preview
-> resolve warnings/ambiguity
-> validate domain rules
-> explicit confirm
-> transactional canonical write
```

Parse и matching не должны создавать program, exercise, alias или другую canonical entity.
При любой ошибке до confirm canonical data остаётся неизменной.

## Сначала

Перед реализацией:

- изучи текущие domain schemas, versioning, ownership и permissions;
- найди существующие upload/storage/parsing dependencies;
- проверь locale/unit conventions и design system;
- проверь ограничения runtime/deployment и temporary storage;
- определи canonical template и поддерживаемые variants;
- не добавляй format/parser, если он не нужен текущему task;
- не обещай произвольный импорт файлов «из любого приложения».

## Format allowlist

Поддерживай только явно разрешённые extensions и content structures.

Проверяй сочетание:

- extension;
- MIME/content type как недоверенный signal;
- file signature/container structure;
- parser result;
- expected schema.

Filename не используется как storage path или identity. Генерируй internal random id/name.

Для каждого формата зафиксируй:

- maximum file size;
- archive expanded size и compression ratio;
- sheet/row/column/cell/string counts;
- paragraph/table limits;
- parse timeout и memory budget;
- supported encodings/delimiters;
- allowed formulas/relationships/objects policy;
- retention и cleanup.

## XLSX и DOCX

XLSX/DOCX являются ZIP containers. До распаковки и во время чтения защищайся от:

- ZIP bomb/decompression bomb;
- excessive entry count;
- oversized uncompressed content;
- path traversal в archive entries;
- nested archives;
- external relationships;
- embedded files/objects;
- macros/active content;
- malformed XML/entity expansion;
- unexpectedly large shared strings/styles.

Не исполняй macros, formulas, links, OLE objects или embedded code.

Formula cells:

- либо явно unsupported;
- либо разрешены только bounded cached values по документированной policy;
- никогда не вычисляются сервером через office application;
- warning видим пользователю.

DOCX text import, если появится, поддерживает только заранее определённые patterns. Не используй
LLM-only silent structure creation.

## CSV и TXT

- Encoding/delimiter detection ограничено известным набором и размером sample.
- Поддержи BOM и документированную fallback policy.
- Ограничь field/line count и длину.
- Не считай CSV безопасным только потому, что это text.
- Значения, начинающиеся с formula markers, не должны незаметно попасть в будущий spreadsheet export
  как active formulas.
- Не исполняй template expressions, shell-like content или URLs.
- Ambiguous delimiter/encoding приводит к понятному выбору/ошибке, а не к повреждённым данным.

## Temporary storage

- Храни upload вне public web root.
- Используй private permissions и unguessable identifiers.
- Не сохраняй исходный filename как путь.
- Удаляй temporary file после parse/cancel/expiry/error по контролируемому lifecycle.
- Не передавай confidential file во внешний scanner/LLM без отдельного privacy decision.
- Не логируй raw content, full rows, notes или documents.
- Background cleanup идемпотентен и наблюдаем.

## Neutral draft model

Draft должен быть versioned и отделён от canonical domain model.

Храни минимум:

- import id/owner/status/schema version;
- source format;
- parsed entities/rows;
- source sheet/row/cell/paragraph provenance;
- normalized values;
- warnings/errors;
- unresolved candidates;
- parser/template version;
- created/expiry timestamps.

Не используй raw parser objects в API или persistence contract.

Draft можно безопасно revalidate после deploy/version change. Если version несовместима, потребуй re-upload,
а не угадывай migration.

## Template и schema

Canonical template:

- имеет version;
- содержит обязательные/optional columns;
- даёт пример без production/user data;
- использует stable machine semantics;
- описывает aliases;
- корректно открывается в целевых spreadsheet apps;
- проходит round-trip test.

Column aliases локализованы, но canonical field ids стабильны. Duplicate/unknown columns имеют явную policy.
Не определяй смысл колонки только fuzzy-сходством без preview.

## Normalize и validation

Разделяй:

1. syntactic parsing;
2. normalization;
3. field validation;
4. cross-row/domain validation;
5. matching;
6. canonical transaction.

Для numeric/range/unit fields:

- locale decimal separators;
- whitespace/non-breaking spaces;
- bounded values;
- integer/decimal semantics;
- range/list grammar;
- units;
- empty vs zero;
- duplicate rows;
- supersets/group references;
- cross-row consistency.

Ошибки должны ссылаться на source row/cell и объяснять исправление.

## Entity matching

Используй предсказуемую последовательность:

1. stable id, если template позволяет и ownership valid;
2. normalized exact visible title;
3. approved global/user alias;
4. token/fuzzy candidate search;
5. domain hints, например equipment/muscle;
6. confidence + candidates;
7. manual resolution.

Правила:

- auto-match только для одного unique high-confidence candidate;
- ambiguity никогда не скрывается;
- fuzzy score сам по себе не создаёт entity;
- пользователь явно выбирает existing или создаёт разрешённую personal custom entity;
- confirmed personal alias имеет user scope;
- один пользователь не меняет global catalogue;
- global aliases требуют отдельной moderation policy;
- bilingual labels/aliases ведут к одной canonical id;
- cross-user/private entities не участвуют в candidates.

Не выдавай percentage confidence пользователю, если threshold не калиброван и число создаёт ложную
точность. Достаточно категорий и причины.

## Preview UX

Preview обязателен и показывает:

- parse status;
- структуру будущего результата;
- warnings/errors;
- matched/unmatched/ambiguous rows;
- source location;
- normalized values;
- domain validation;
- что будет создано и что не будет создано.

Пользователь может cancel, исправить resolution и re-upload. Confirm недоступен при blocking errors.

Проверяй mobile/TMA, keyboard, screen reader, длинные названия и большие, но допустимые imports.
Не превращай preview в редактирование raw spreadsheet внутри браузера без необходимости.

## Confirm и canonical write

- Повторно проверь auth/ownership и draft expiry.
- Revalidate critical domain rules server-side.
- Используй одну явную transaction boundary.
- Не допускай partial canonical writes.
- Защити confirm от duplicate submit/replay.
- Сохрани import provenance/audit без raw confidential content.
- Создавай editable draft domain entity, а не автоматически assign/activate/start, если task не требует.
- При conflict/concurrent catalogue change верни resolution flow, а не молча выбери другой match.

## Permissions и privacy

- Self import создаёт данные владельца.
- Coach/trainer import проверяет current relationship/capability на confirm, не только upload.
- Revoked access блокирует confirm/download.
- Admin capability не означает автоматический доступ к private source files.
- Source file и preview не доступны другому пользователю по predictable id.
- Retention/export/delete policy зафиксирована отдельно для source file, draft и canonical result.

## LLM/OCR boundary

По умолчанию не используй:

- LLM-only parsing;
- OCR;
- image/PDF extraction;
- arbitrary competitor migrations.

LLM может когда-либо предложить candidates только как недоверенный advisory layer, но deterministic parser,
visible uncertainty и mandatory review остаются. Для PDF/images/OCR нужен отдельный owner decision, threat
model, quality policy и task.

## Tests

Минимальная матрица:

- template round-trip;
- valid minimal/full file;
- aliases/locales/units;
- ambiguity и no match;
- personal custom entity;
- malformed container/XML/CSV;
- ZIP bomb/path traversal/external relation/macro/formula/object;
- file/archive/row/cell/string/time limits;
- encoding/delimiter;
- duplicate/replay/concurrent confirm;
- no partial writes;
- self/coach allow/deny/revoked;
- temp cleanup/expiry;
- logs without raw content;
- mobile/TMA/a11y preview.

Используй `references/SAFE_IMPORT_CHECKLIST.md` для полного threat/test review.

## Совместная работа с другими skills

- `$security-engineer` - upload/parser threat model;
- `$privacy-engineer` - source retention и third-party sharing;
- `$backend-engineer`/`$data-engineer` - draft/transaction/persistence;
- `$frontend-engineer`/`$product-designer` - preview/resolution UX;
- `$localization-engineer` - aliases, units и template localization;
- `$fitness-domain-reviewer` - program/exercise/set semantics;
- `$qa-engineer` - adversarial and regression suite.

## Финальный отчёт

Укажи:

- поддерживаемые formats/template version;
- limits и active-content policy;
- neutral draft/matching/confirm contracts;
- permissions и retention;
- security/adversarial tests, реально выполненные;
- unsupported formats и known ambiguities.
