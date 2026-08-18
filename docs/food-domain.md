# Food domain

The food catalog is an independent backend domain. It is the source of truth for future food
diary entries and integrations; nutrition targets in `nutrition_targets` remain a separate
calculation of a user's daily target.

## Data and visibility

Every food stores a name, optional brand and GTIN barcode, nutrition per 100 grams, an optional
standard serving with a known mass, provenance, trust/status, and timestamps.

Food types have explicit visibility rules:

- `system` and `branded` foods are catalog records with no user owner;
- `user` foods always have an owner and `user` provenance;
- user foods are private to their owner. A trainer relationship or admin UI visibility does not
  implicitly grant access;
- only active catalog records and the current user's own active records belong in ordinary food
  lookup results.

The database enforces owner/provenance alignment. Active system and branded records must have
verified trust and complete energy, protein, fat, and carbohydrate values. Fiber may be unknown.
Draft/disabled records may remain incomplete while a source is reviewed, but must not be used as
active diary data.

Catalog barcodes are unique across system/branded foods. A user barcode is unique only within its
owner's private scope, so a private correction cannot collide with another account or with the
shared catalog. Application validation verifies GTIN length, digits, and check digit before a
record reaches persistence.

## Nutrition calculations

Nutrients are stored as decimal values per 100 grams. The deterministic calculation scales each
known value by `weight_g / 100` using decimal arithmetic and round-half-up:

- energy: 0.01 kcal;
- protein, fat, carbohydrates, and fiber: 0.001 g;
- effective mass: 0.001 g.

Unknown nutrients stay unknown; they are never silently replaced with zero. A standard serving
can be calculated only when its gram weight is known. For a serving expressed in grams, the
declared amount must equal its weight. Other units (`ml`, `piece`, `serving`) retain the display
amount/unit but still require an explicit gram weight; the domain does not invent density or
piece-weight conversions.

## Reproducible catalog import

`scripts/import_food_catalog.py` accepts a local JSON catalog. The manifest is versioned and must
identify the source dataset and version, source URL, license and license URL, reviewer, review
date, and an explicit verified-license attestation. Each source record needs a stable external ID.
The importer upserts by `(source_name, external_id)` and never deletes records absent from a later
file, which makes reruns deterministic and prevents accidental catalog loss.

Validate a candidate file without database writes:

```console
py scripts/import_food_catalog.py path/to/catalog.json --dry-run
```

Run the same command without `--dry-run` only after source accuracy, provenance, and license have
been reviewed. No base food seed is committed until such a source is selected; the pipeline alone
does not imply that a dataset is suitable for production.

External HTTP fetching, diary entries, recipes, favorites/recent foods, barcode scanning, and UI
are intentionally outside this foundation.
