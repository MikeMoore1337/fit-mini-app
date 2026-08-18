# Workout set semantics and supersets

Workout sets store three independent observations:

- `set_kind`: `warmup`, `working`, or `drop`;
- `rir`: optional repetitions-in-reserve category `0`, `1`, `2`, `3`, or `4+`;
- `reached_failure`: optional boolean stating whether the person reports reaching failure.

The backend does not derive failure from RIR, detect failure automatically, or calculate
effective repetitions/sets. Existing rows keep `set_kind = null` and
`reached_failure = null`; analytics treats the legacy null kind like the previously counted
working volume. Newly materialized workout sets are explicitly `working`.

Warm-up sets remain visible in workout responses, trainer history, and account export, but do not
contribute to working-volume, progression, personal-record, RIR-distribution, or muscle-exposure
analytics. Working and drop sets do contribute. Drop sets are returned explicitly as `drop` and
are never multiplied or weighted into a synthetic score.

## Superset snapshots

`ProgramTemplateExercise` and `UserWorkoutExercise` both store nullable `superset_group` and
`superset_order`. The fields are either both null or both present. A template superset contains
exactly two exercises ordered `1` and `2`; duplicate order slots in one day/workout are rejected.
Assignment copies the values into each materialized workout so later template edits cannot alter
workout history.

The technical API fields are intentionally compact. User interfaces must present beginner-facing
Russian wording:

- `warmup` — `Разминочный подход`;
- `working` — `Рабочий подход`;
- `drop` — `Дроп-сет`, with a short first-use explanation;
- `reached_failure` — `Подход до отказа`;
- grouped exercises — `Суперсет — два упражнения подряд`.

These controls remain optional advanced fields; the default logging flow stays
`Вес -> Повторы -> Готово`.
