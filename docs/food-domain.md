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

External HTTP fetching, recipes, barcode scanning, and UI remain outside this foundation.

## Personal library and local search

Authenticated users can create, read, update, and delete their own active foods through
`/api/v1/nutrition/foods`. Personal foods use the same nutrient, serving, and GTIN validation as
the catalog, but remain private to their owner. A foreign personal-food ID returns the same 404 as
a missing ID. Deleting a personal food does not remove diary snapshots already created from it.

Favorites are account-scoped and may reference either a visible catalog food or the user's own
food. `PUT /foods/{food_id}/favorite` is idempotent; the matching `DELETE` removes the favorite.
Recent foods are derived from the user's current diary history by the latest entry update, so no
second mutable usage source is maintained. Deleted diary entries and deleted foods no longer
contribute to recent results. Frequently-used foods are not exposed yet: current requirements do
not need another ranking signal, and a durable counter would require explicit semantics for entry
edits and deletion.

`GET /api/v1/nutrition/foods/search` is a local-only, deterministic search. It case-folds and
collapses whitespace in the query, requires at least two non-whitespace characters, and searches
the normalized name plus brand. Results are ranked by mutually exclusive priority:

1. recently used;
2. favorites;
3. the user's own foods;
4. system foods;
5. local branded foods.

Ties use recent/favorite timestamps, match position, name, and ID for stable pagination. Search,
recent, and favorites use `limit`/`offset`; `limit` defaults to 20 and is capped at 50, while
`offset` is capped at 10,000. The frontend autocomplete contract is a 250 ms debounce after the
normalized query reaches two characters. A later UI task must cancel obsolete requests and ignore
stale responses; the API itself does not add an artificial delay. PostgreSQL trigram/full-text or
a separate search service are intentionally not used before catalog size and latency demonstrate
a need. Visibility/ranking queries are backed by food scope, favorite-order, and diary-recency
indexes.

## Private food diary

The diary stores one entry per selected food, user-local calendar date, and meal type
(`breakfast`, `lunch`, `dinner`, or `snacks`). An entry accepts either a mass in grams or a number
of the food's standard servings. Dates in the user's past and their current date are writable;
future dates are rejected using the timezone stored in the shared account profile. With no date,
the day endpoint resolves today through that same timezone, so Web and Telegram use identical
calendar semantics.

Diary entries snapshot the food name, serving information, and nutrients per 100 grams when the
entry is created or explicitly changed to another food. Later catalog edits or deletion therefore
do not rewrite nutrition history. Calculated entry, meal, and day totals continue to use the food
domain's decimal scaling rules. Unknown fiber remains unknown when a non-empty aggregate includes
an entry without fiber data; energy, protein, fat, and carbohydrate are complete for every active
food.

The authenticated API is deliberately organized around the diary rather than its table:

- `GET /api/v1/nutrition/diary?diary_date=YYYY-MM-DD` returns all four meals, day totals, the
  current target from the existing nutrition service, and the remaining target;
- `POST /api/v1/nutrition/diary/entries` creates an entry;
- `PATCH /api/v1/nutrition/diary/entries/{entry_id}` changes its food, date, meal, or amount;
- `DELETE /api/v1/nutrition/diary/entries/{entry_id}` removes it.

All entry reads and mutations are scoped to the authenticated account. A missing or foreign food
or diary entry uses the same not-found response, so the API does not disclose another account's
private catalog or diary data. A day is a bounded aggregate and is intentionally returned as one
response rather than paginated entry fragments.
