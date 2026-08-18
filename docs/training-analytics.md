# Deterministic training analytics

The extended training analytics API exposes factual completed-set history without recovery,
fatigue, readiness, effective-set, estimated one-repetition maximum, or calorie-burn scores.

- `GET /api/v1/workouts/progress/training-analytics?period_days=30&exercise_history_limit=20`
  returns the authenticated account's analytics.
- `GET /api/v1/coach/clients/{client_id}/training-analytics` returns the same detail only while
  the authenticated trainer has an active relationship with that client.

`period_days` accepts only `7`, `30`, or `90`. `exercise_history_limit` is applied separately to
each exercise at the database query boundary and accepts `1..100`. The trainer client-list
endpoints remain summaries and do not load this history.

## Formulas and missing data

All period boundaries use the account's IANA timezone and include both boundary dates. Only
working and drop sets with `is_completed = true` inside workouts whose status is `completed` are
included. Warm-up sets, planned/in-progress/skipped/cancelled workouts, and incomplete sets are
excluded from working-volume, progression, RIR, and muscle-exposure metrics. Legacy rows whose
`set_kind` is `null` remain included so the migration does not rewrite historical meaning.

| Metric | Formula and unit | Missing data and limitations |
| --- | --- | --- |
| Completed sets | Count of included working, drop, or legacy-null set rows, sets | Warm-up sets are excluded. Drop sets remain a distinct `set_kind` in bounded history; they are not converted into an effective-set score. |
| Repetitions | Sum of recorded `actual_reps`, repetitions | `reps_recorded_sets` reports coverage. The sum is `null` when no included set has repetitions and can be partial when coverage is incomplete. Repetitions at different loads are not converted into a score. |
| Maximum external load | Maximum recorded `actual_weight`, kg | `null` when load is absent. It is an observed load, not an estimated 1RM and not proof of strength change by itself. |
| Set external-load volume | `actual_reps × actual_weight`, kg | `null` unless both inputs exist. |
| Session/period external-load volume | Sum of computable set volumes, kg | `volume_recorded_sets` reports coverage. The value is `null` when no set is computable and can be partial when coverage is incomplete. |
| Best set volume | Maximum computable set volume, kg | Compares only the recorded external-load product; it is not an effective-repetitions or effort metric. |
| Performed session | A workout-exercise occurrence with at least one included set | Dates use `scheduled_date`; bounded history is newest first. `performed_session_count` remains the full period count and `history_truncated` tells clients when sessions were omitted from the response. |
| RIR distribution | Count of recorded categorical values `0`, `1`, `2`, `3`, `4+`, sets | Missing RIR remains missing and is reported separately. `4+` is a category, not the exact number four. RIR never produces fatigue, readiness, recovery, or predicted-failure metrics. |
| Primary muscle exposure | For each structured primary link, add the exercise's included completed-set count, sets | No fractional coefficient is applied. One set can appear under each explicitly linked muscle. Exercises without structured metadata are reported separately. |
| Secondary muscle exposure | The same count for structured secondary links, kept separate from primary exposure, sets | Primary and secondary exposure must not be added into an "effective sets" score. The metric describes catalog linkage, not measured muscular stimulus. |

`uses_bodyweight_equipment` comes from the structured equipment relation. The stored load field is
treated only as external load. Body mass is not added automatically, and assisted resistance is
not normalized or subtracted, so unweighted bodyweight sets normally have `null` volume and
bodyweight/assisted movements must not be compared by this volume as if it were total mechanical
work.

## Query and privacy behavior

The service uses one grouped period query, one window-ranked bounded-history query, and one
metadata query for the exercises actually present. Query count does not grow with exercise or
session count. Existing indexes on user programs, `(user_program_id, scheduled_date, status)`,
workout exercises, workout sets, and structured exercise links cover the access path; this change
requires no migration.

The user ID always comes from the authenticated server-side context. Trainer access reuses the
existing active relationship check and returns `404` for unrelated or ended relationships. The
response contains only training aggregates and bounded completed-set history; it does not expose
nutrition data, trainer comments, or another account's records.
