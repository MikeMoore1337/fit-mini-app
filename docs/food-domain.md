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

External HTTP fetching, barcode scanning, and UI remain outside this foundation.

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

`GET /api/v1/nutrition/foods/search` always starts with deterministic local search. It case-folds
and collapses whitespace in the query, requires at least two non-whitespace characters, and
searches the normalized name plus brand. Results are ranked by mutually exclusive priority:

1. recently used;
2. favorites;
3. the user's own foods;
4. system foods;
5. local branded foods.

Ties use recent/favorite timestamps, match position, name, and ID for stable pagination. Search,
recent, and favorites use `limit`/`offset`; `limit` defaults to 20 and is capped at 50, while
`offset` is capped at 10,000. The frontend autocomplete contract is a 250 ms debounce after the
normalized query reaches two characters. A later UI task must cancel obsolete requests and ignore
stale responses; the API itself does not add an artificial delay. A separate full-text/search
service is not introduced. PostgreSQL uses a `pg_trgm` GIN index for the real
substring query over `search_text`; SQLite test/local schemas use an ordinary compatibility index.
Visibility/ranking queries are additionally backed by food scope, favorite-order, and
diary-recency indexes. Stable source imports use the unique `(source_name, external_id)` index,
and barcode lookup uses separate catalog and per-owner partial unique indexes.

## Optional external catalog

The neutral `FoodProvider` contract exposes `search` and `get_by_barcode`; domain
orchestration does not depend on Open Food Facts response shapes. `FOOD_PROVIDER=disabled` is the
default and requires no external configuration. To enable the current adapter, set
`FOOD_PROVIDER=open_food_facts` and a real identifying
`OPEN_FOOD_FACTS_USER_AGENT=AppName/Version (contact)` value. No API secret is required.
`FOOD_PROVIDER_TIMEOUT_SECONDS` configures the per-attempt network timeout from 1 to 15 seconds
and defaults to 4 seconds; eligible reads retry at most once, so callers retain a bounded fallback.

Search remains local-first. The provider is called only when local results are empty and the
caller explicitly sets `include_external=true`; callers must present that as a separate external
search action, not invoke it from the 250 ms local typeahead. Barcode lookup through
`GET /api/v1/nutrition/foods/barcode/{barcode}` also returns a visible personal/catalog record
before consulting the provider. Its response echoes the validated barcode and explicitly reports
`status=found|not_found` plus `source=local|external|null`, so camera and manual-entry clients can
use the same contract and offer personal-food creation after an empty result. `provider_status`
separately records whether the external lookup was unnecessary, disabled, available, unavailable,
or rate-limited. A disabled provider, timeout, network failure, rate limit, upstream 5xx, malformed
response, or mismatched provider barcode produces a successful structured fallback without raw
upstream details; it never makes the diary unavailable. Timeout/network/5xx reads get at most one
short retry. A 429 is not retried.

Open Food Facts integration follows the official current guidance reviewed on 2026-08-18:

- barcode reads use the current v3.6 product endpoint and request only required fields;
- full-text search uses the dedicated Search-a-licious API because Product Opener v2/v3 do not
  provide current full-text search;
- the adapter sends the required identifying User-Agent;
- upstream limits are currently 15 product reads/minute/IP and 10 searches/minute/IP, so external
  search is never automatic typeahead; the adapter also enforces matching process-local sliding
  request budgets, including retries, for the current single-process API deployment;
- database contents are ODbL 1.0; attribution and share-alike apply, including to local caches.

References: [API introduction and limits](https://openfoodfacts.github.io/openfoodfacts-server/api/),
[v3 barcode endpoint](https://openfoodfacts.github.io/documentation/docs/Product-Opener/v3/products/get-api-v3-product-code/),
[Search-a-licious API](https://openfoodfacts.github.io/search-a-licious/users/ref-openapi/), and
[licensing guidance](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/license-be-on-the-legal-side/).

Provider results are read-only response objects, not rows in `foods`. Every result carries the
provider name, product source URL, `Open Food Facts contributors` attribution, `ODbL-1.0`, and the
license URL. Images are intentionally not requested because they have a separate CC BY-SA license.
This boundary prevents an external ODbL cache from being silently combined with private user
foods or diary data. A future decision to persist or transform provider data requires a separate
license/share-alike review and a provenance-preserving storage design.

The backend does not persist or process-cache provider responses. Authenticated API responses are
marked `Cache-Control: no-store, private`; adding a shared or durable Open Food Facts cache would
require an explicit ODbL attribution/share-alike design. Provider failure logs contain only the
stable provider name and a bounded failure class (`timeout`, `network_error`, `rate_limited`,
`upstream_error`, or `malformed_response`), never the search phrase, barcode, returned product, or
diary content.

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

Food/recipe/diary domain failures use the existing API error envelope `{"detail": "..."}`:
missing or foreign private resources return `404`, idempotency-key conflicts return `409`, and
domain-invalid operations return `422`. Request-schema validation also returns `422` using
FastAPI's structured validation details. External-provider unavailability is not a diary failure:
search/barcode reads return `200` with an explicit `provider_status` fallback and no raw upstream
error.

Migrations `0034`-`0038` are forward, deterministic steps. `0036` initially populated
`search_text` from food name/brand; `0038` safely recomputes it in ID-ordered batches with the same
Unicode `casefold()` algorithm used at runtime before adding the search index. Neither step
invents nutrients, ownership, provenance, or source IDs. `0038` also replaces the trainer relation
lookup index without changing user-authored domain content.

## Private recipes

Recipes under `/api/v1/nutrition/recipes` are private to their owning account. Each ingredient is
a visible food with an amount in grams or in the food's explicitly defined standard serving. The
recipe snapshots ingredient names, serving data, and nutrients, so later catalog edits or deletion
do not silently rewrite the saved recipe.

Recipe totals use the same decimal scaling and round-half-up rules as foods and diary entries. The
ingredient weights are summed as the default effective recipe weight. An optional
`final_weight_g` replaces that denominator only when the user explicitly supplies it; the backend
does not infer cooking loss, water gain, density, or yield. Responses expose ingredient weight,
the optional final weight, effective weight, total nutrients, and nutrients per 100 grams. Diary
entries can reference either one food or one owned recipe. Recipe diary entries accept an
arbitrary positive gram weight and snapshot the recipe calculation at that point in time.

## Explicit diary copying

Authenticated copy operations are separated by scope:

- `POST /api/v1/nutrition/diary/copy/product` repeats one source diary entry;
- `POST /api/v1/nutrition/diary/copy/meal` copies all entries in one meal;
- `POST /api/v1/nutrition/diary/copy/day` copies all entries in a day while preserving meal types.

Product and meal requests name both the source date/meal and target date/meal. A day request names
both dates. This makes "repeat yesterday's breakfast" the ordinary meal-copy contract rather than
a hidden server shortcut. Source ownership and both calendar dates are validated on the backend;
the same user-timezone future-date rule as manual diary writes applies to copy targets.

Every copy request requires an `Idempotency-Key` header. The database scopes keys per account and
stores a fingerprint of the explicit source/target request in the same transaction as the copied
entries. Retrying the same key and payload returns the original entry IDs with `replayed=true` and
does not append duplicates. Reusing the key for a different source or target returns `409`.
