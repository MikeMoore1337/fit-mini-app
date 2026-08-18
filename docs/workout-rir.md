# Repetitions in reserve

`UserWorkoutSet.rir` is an optional category describing how many more repetitions a person
believes they could have completed with good technique after a performed set. It is intended
for completed working or drop sets, but it is never required for completing a set or workout.
It remains independent from `reached_failure`: the API records both observations as supplied
and does not infer one from the other.

The API and database use the categorical string values `"0"`, `"1"`, `"2"`, `"3"`, and
`"4+"`. `"4+"` means that many repetitions remained; it is not an exact estimate of four.
`null` means that repetitions in reserve were not recorded. Existing workout sets therefore
remain valid without a backfill.

The primary user-facing label is `Повторы в запасе`. The explanation is:

> Сколько повторов вы ещё могли бы сделать с хорошей техникой после завершения подхода?

User-facing choices are:

- `0 — больше не смог бы`;
- `1 — ещё примерно 1 повтор`;
- `2 — ещё примерно 2 повтора`;
- `3 — ещё примерно 3 повтора`;
- `4+ — осталось много сил`.

RIR is stored and returned by workout set save/resume, completed workout details, trainer
workout history, and account export. It does not change completion, volume, calories,
progression, or readiness calculations. Automatic estimation, RPE conversion, and UI are
outside this foundation.
