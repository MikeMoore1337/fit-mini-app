# Exercise domain

The exercise catalog keeps the existing `exercises.primary_muscle` and
`exercises.equipment` text fields for backward compatibility and display. New code that
filters, recommends, or aggregates exercises must use the structured relations described
below instead of comparing those legacy strings.

## Canonical metadata

- `muscles` stores stable identifiers and Russian display names.
- `exercise_muscles` assigns one or more muscles with an explicit `primary` or `secondary`
  role and deterministic order. It deliberately has no fractional contribution or volume
  coefficient.
- `equipment` contains the controlled identifiers `bodyweight`, `dumbbell`, `barbell`,
  `bench`, `cable`, `machine`, `kettlebell`, `cardio`, and `other`.
- `exercise_equipment` permits more than one equipment category when a future reviewed
  catalog entry genuinely needs it. The current backfill maps the existing single text value
  to one controlled identifier.
- `exercise_alternatives` stores reviewed, symmetric substitutions as one ordered pair.
  The database rejects self-links and duplicate/reversed pairs. A shared muscle alone never
  creates an alternative.
- `exercise_guide_metadata` stores safety notes, source and license attribution, and a stable
  local media reference. Technique steps, breathing, and common mistakes remain in the
  existing guide profiles and are not duplicated in a second persistence model.

The lookup indexes are shaped for muscle/equipment filtering and both sides of an
alternative lookup. Catalog loading uses batched relationship loading, so query count does
not grow with the number of exercises.

## Backfill and lifecycle

Migration `0039_exercise_domain` snapshots the current guide profile assignments and
backfills existing rows deterministically:

- explicit recognized `primary_muscle` and `equipment` values become canonical relations;
- secondary muscles come only from the existing reviewed guide profile for that exercise;
- guide provenance preserves `free-exercise-db` / Unlicense attribution, while the existing
  locally created cardio illustrations retain `Your Fitness Coach` attribution;
- personalized copies inherit the source exercise guide profile and provenance while keeping
  their explicitly edited primary muscle and equipment;
- custom exercises with absent or unknown metadata stay partial and receive no inferred
  muscles, equipment, guide, or alternatives.

The catalog seed performs the same synchronization after migrations and is idempotent. Its
curated alternative list is the source of truth until an explicit management workflow is
introduced.

## API contract

Catalog and detail responses retain `primary_muscle` and `equipment`, and additionally expose:

- `primary_muscle_ids[]` and `secondary_muscle_ids[]` with stable identifiers;
- `equipment_ids[]` with controlled identifiers;
- `alternatives[]` with stable exercise ID, slug, and visible title.

`GET /api/v1/programs/exercises/{exercise_id}` returns the full item including the guide.
The guide endpoint additionally returns stable muscle role identifiers together with display
names, controlled equipment with display names,
safety notes, alternatives, media reference, and source-license metadata. A custom exercise
may legitimately return empty structured arrays and no guide.
