# Safe import checklist

## 1. Threat model

Threats to consider:

- oversized upload/storage exhaustion;
- decompression/ZIP bomb;
- archive path traversal;
- malformed XML/parser exploit;
- macros/active content;
- formulas/external links/OLE/embedded files;
- external relationships/SSRF;
- excessive rows/cells/shared strings/styles;
- encoding/delimiter ambiguity;
- formula injection in later exports;
- filename/path manipulation;
- unauthorized source-file access;
- cross-user entity matching;
- partial writes;
- duplicate/replay/concurrent confirm;
- private content in logs/LLM/telemetry;
- temporary-file retention leak;
- LLM/OCR hallucinated structure.

## 2. Limit specification

Define and test explicit values in project config for:

```text
request body/file size
number of files
archive entries
expanded bytes
compression ratio
sheets
rows per sheet and total rows
columns
cells
cell/string length
CSV line/field length
DOCX paragraphs/tables/runs if supported
parse wall-clock timeout
memory/concurrency
preview retention
source-file retention
```

Do not put arbitrary numbers in the public API unless clients need them. User-facing validation should explain the relevant limit.

## 3. Upload boundary

- authenticated/authorized endpoint;
- CSRF policy where applicable;
- allowlisted extensions;
- content signature/container validation;
- generated internal filename/id;
- private non-executable storage;
- no public URL;
- no overwrite by source filename;
- request and per-user rate limit;
- duplicate content hash policy;
- safe error without path/stack trace.

## 4. XLSX checks

- valid ZIP/container;
- no path traversal entries;
- entry count/expanded size/compression ratio;
- workbook/sheet count;
- shared strings/styles bounds;
- macros/active content rejected;
- external links/relationships rejected or explicitly ignored with warning;
- embedded objects/files rejected;
- formula policy enforced;
- hidden sheets/rows policy;
- merged cells policy;
- date/number representation;
- no office application execution.

## 5. CSV/TXT checks

- encoding allowlist/BOM;
- delimiter allowlist/detection confidence;
- quote/newline handling;
- field/line/row limits;
- NUL/control characters policy;
- duplicate headers;
- unknown headers;
- decimal/unit locale;
- formula markers preserved as data and escaped on future export;
- no template/code evaluation.

## 6. DOCX checks, if supported

- valid ZIP/container;
- external relationships blocked;
- embedded/OLE/macros blocked;
- XML/entity/entry limits;
- deterministic supported patterns only;
- tables/paragraphs provenance;
- images ignored unless separately approved;
- no OCR;
- no LLM-only structure;
- visible ambiguous sections.

## 7. Draft model

Verify:

- versioned schema;
- owner;
- source format/template/parser version;
- source row/sheet/paragraph provenance;
- parsed raw-safe value and normalized value as needed;
- warnings/errors severity;
- matching candidates/resolution;
- expiry/status;
- no canonical side effect;
- revalidation policy after code/schema update.

## 8. Matching matrix

Cases:

- stable id exact and authorized;
- exact current title;
- normalized case/whitespace/punctuation;
- `ё/е` policy;
- approved user alias;
- approved global alias;
- bilingual alias;
- one strong fuzzy candidate;
- several close candidates;
- equipment/muscle hint conflict;
- private/custom entity from another user;
- no match;
- explicit personal custom creation;
- alias confirmation scoped to user;
- global alias mutation blocked.

Auto-match only according to documented unique high-confidence rule.

## 9. Domain validation

For program import, for example:

- day/order/name;
- exercise required;
- sets positive and bounded;
- reps/range grammar;
- rest seconds;
- RIR optional values;
- superset group references;
- notes length;
- duplicate rows;
- unsupported/mixed units;
- empty day;
- program size;
- current domain version compatibility.

Use canonical domain validators where possible.

## 10. Preview and resolution

- all parsed rows visible in bounded/paginated form;
- blocking vs non-blocking issues distinct;
- source location shown;
- normalized value understandable;
- candidate details sufficient to choose;
- confirm disabled with blocking errors;
- cancel/re-upload;
- no source file leakage in client URL;
- responsive/keyboard/screen-reader;
- large valid import remains usable.

## 11. Confirm transaction

- draft owner and expiry rechecked;
- permissions rechecked;
- critical validation rerun;
- catalogue/version conflicts handled;
- idempotency/replay guard;
- one transaction;
- no partial writes;
- result is editable draft unless task says otherwise;
- no automatic assignment/start;
- provenance/audit stored without raw private content;
- source/draft cleanup lifecycle started.

## 12. Adversarial tests

- fake extension/MIME;
- double extension/long/special filename;
- empty/truncated file;
- corrupted ZIP/XML;
- ZIP bomb/high compression;
- path traversal entry;
- nested archive;
- macro-enabled/embedded/external relationship;
- formula cell;
- huge shared strings/styles;
- malformed CSV quotes;
- ambiguous encoding/delimiter;
- timeout/memory pressure;
- duplicate concurrent uploads;
- confirm replay;
- access revoked between upload and confirm;
- another user fetches draft/file;
- cleanup failure;
- log scan for source content.

## 13. Reference

Review current secure upload guidance, including:

- OWASP File Upload Cheat Sheet/project guidance;
- current parser/library security documentation;
- format specifications relevant to the chosen library.

Do not enable an antivirus/cloud scanner by default if it requires sending confidential files to a third party.
