# Progress and adherence aggregates

The period summary API is the backend source of truth for factual progress and plan adherence.
It supports only `7`, `30`, and `90` day windows:

- `GET /api/v1/workouts/progress/summary?period_days=30` returns the authenticated user's data;
- `GET /api/v1/coach/clients/{client_id}/summary?period_days=30` returns one currently assigned
  client;
- `GET /api/v1/coach/client-summaries?period_days=30` returns bounded summaries for all of the
  trainer's active clients without loading each client's history separately.

The existing `/workouts/progress` and coach analytics endpoints retain their legacy lifetime
contract.

## Adherence formula (`adherence-v1`)

The formula has four explicit component weights: planned workouts `40%`, cardio `20%`, calories
`20%`, and protein `20%`. A component is included only when the backend has both a target or plan
and factual observations. The overall value is the weighted mean of available components, with
their weights renormalized. The response lists `included_components`; it returns `null` rather
than a score when none are available.

- Workouts: completed workouts divided by evaluable planned workouts. Cancelled workouts and days
  without a planned workout are excluded. A planned or in-progress workout on the current day is
  excluded until it is completed, skipped, or becomes overdue.
- Calories: past logged diary days within `+-10%` of the current calorie target divided by past
  logged diary days on or after the target's last-save date.
- Protein: past logged diary days meeting or exceeding the current protein target divided by past
  logged diary days on or after the target's last-save date.
- Cardio: exposed as `unsupported` when cardio is planned because the current product has a cardio
  target but no factual cardio activity log. It is never inferred from the target itself.

The current day is excluded from nutrition adherence because its diary may be incomplete. A past
day without diary entries is missing data, not a failed day. The current schema has no explicit
"day complete" marker, so a partially logged past day is evaluated from the recorded totals; the
response reports `logged_days` and `adherence_evaluated_days` so clients can explain this
limitation.
Missing targets and periods without evaluable planned workouts produce component-level
`not_applicable` or `insufficient_data` states instead of zeroes.

Nutrition averages use all past logged days in the selected period. Adherence uses only
`adherence_evaluated_days` on or after `target_effective_on`, because the current schema stores the
latest target and save date but not target history. Older diary days are never judged against a
newer target.

## Privacy and interpretation

User summaries are always scoped to the authenticated account. Trainer endpoints require an
active trainer-client relationship for every returned client; ended or unrelated relationships
cannot access the detail endpoint and are absent from the bulk endpoint. Trainer nutrition output
contains only aggregate calorie/protein totals and targets. It never returns food names, meals,
recipes, personal foods, notes, or full diary entries.

Body changes compare the user only with their own measurements in the selected period. Training
volume uses completed sets from completed workouts. A new personal record is counted per exercise
when the period's best recorded weight or single-set volume exceeds all completed results before
the period. These are factual observations, not medical, recovery, readiness, motivation, or risk
assessments.
