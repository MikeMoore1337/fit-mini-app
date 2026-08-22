# Fitness domain review checklist

Use this checklist for changed domains only.

## 1. Claim/formula ledger

For every changed rule record:

```text
rule/claim
surface and consumers
canonical implementation
inputs and units
period/timezone
missing-data policy
minimum sufficiency
formula/threshold
source or product rationale
output and rounding
limitations
permissions
regression tests
```

## 2. Evidence classification

### Evidence-backed domain rule

Requires current reputable sources and a statement limited to the supported population/context.

### Validated formula/measurement rule

Requires definition, units, domain of validity and known error/limitations.

### Product heuristic

Requires explicit product rationale, deterministic threshold, user-facing wording and tests. Do not present as medical/scientific fact.

### Display convention

Requires consistency and accessibility, not a scientific claim.

### Unknown/deferred

Do not fill the gap with LLM output or intuition. Preserve missing/limited state.

## 3. Exercise metadata

Check:

- canonical id/source exercise relationship;
- primary/secondary muscle provenance;
- no arbitrary fractional contribution;
- equipment taxonomy reflects real catalogue;
- custom exercise partial metadata;
- alternatives curated, no self/duplicate;
- movement/equipment compatibility;
- source/license/media rights;
- safety notes factual and non-medical;
- bilingual label does not duplicate entity;
- public/custom privacy boundary.

Red flags:

- «любое упражнение на грудь заменяет жим»;
- generated anatomy without review;
- invented contraindication;
- copied competitor guide/media;
- missing metadata silently filled as fact.

## 4. RIR and sets

Check values:

- null;
- 0/1/2/3/4+;
- invalid negative/large/string;
- old rows without RIR;
- save/resume/edit/history/export;
- completed set without RIR;
- `4+` preserved as open-ended category;
- no automatic RPE conversion;
- no hidden progression/readiness impact unless task explicitly defines it.

## 5. Progression

Test:

- no history;
- one workout;
- repeated target completion;
- missed reps/sets;
- partial workout;
- optional/missing RIR;
- contradictory data;
- deload/block change;
- exercise variation/equipment change;
- duplicate completion/concurrency;
- recommendation shown/dismissed/accepted;
- no automatic program write;
- evidence/reason keys;
- plain-language output.

Red flags:

- model invents next weight;
- one set triggers confident increase;
- machine and free-weight volume treated identical;
- recommendation lacks period/evidence;
- user cannot see/cancel change.

## 6. Workout adaptation

For time/equipment/replacement:

- original and proposed diff;
- core/high-priority preservation rule;
- accessory removal order;
- equipment availability;
- curated alternative;
- preview/confirm/cancel;
- history records actual workout;
- no silent future-program mutation;
- no pain/injury workaround;
- no random/LLM substitution.

## 7. Training analytics

For each metric:

- exact formula;
- working vs warm-up/completed sets;
- external load limitations;
- exercise comparability;
- primary/secondary exposure semantics;
- date/timezone;
- missing/partial workouts;
- no arbitrary score;
- chart scale and labels honest;
- accessible table equivalent;
- AI/report consumes same canonical result.

## 8. Nutrition target history

Test:

- one active target per date;
- non-overlapping periods;
- effective boundary at timezone/date;
- manual/calculated/trainer/adaptive source;
- migration of current target without fake historical backfill;
- concurrent updates;
- trainer permission/revocation;
- history used in reports;
- preview/confirm for adaptive change;
- export/delete.

## 9. Nutrition reporting

Test:

- no diary days;
- one day;
- sparse period;
- full period;
- target changes;
- missing day not zero;
- coverage counters;
- calories and each macro separately;
- averages denominator;
- timezone/date range;
- partial food records;
- long custom range limits;
- user/trainer isolation.

## 10. Adaptive energy estimate

Record and test:

- intake data coverage;
- weight measurement count and timespan;
- smoothing method;
- outlier handling;
- goal/target history;
- maintenance/loss/gain scenarios;
- noisy trend;
- water-weight-like short variation handled conservatively;
- point vs range;
- no result for insufficient data;
- no one-day TDEE;
- no watch/machine calories as truth;
- no automatic target change;
- rationale and limitations.

## 11. Weight/anthropometry

Test:

- one point;
- multiple points same day;
- sufficient timespan;
- measurement type/unit;
- exact dates;
- priorities;
- user self comparison;
- trainer access/revocation;
- arm circumference does not imply biceps;
- no ideal ratio/score;
- no photo/body-fat inference;
- contradictory measurements;
- no interpolation.

## 12. Cardio

Check:

- activity taxonomy;
- duration;
- optional distance;
- optional average HR/zone;
- unit conversion;
- bpm bounds;
- planned/completed timestamps;
- duplicate completion;
- history/adherence;
- no wearable requirement;
- no generic MET calorie engine;
- no mixing with strength volume;
- no inferred zone time without data.

## 13. Knowledge and sports nutrition

For each article/claim:

- audience and context;
- evidence type;
- source date;
- population;
- dose/timing only if supported;
- effect size language proportional to evidence;
- adverse effects/limitations;
- conflicts/funding;
- practical application justified;
- no product/affiliate bias;
- no AAS/SARM/pharmacology;
- no guaranteed result;
- reviewed date and reviewer.

## 14. AI Coach

Test prompts:

- no program/rest day;
- sparse diary;
- target changed mid-period;
- insufficient weight trend;
- progression based on deterministic result;
- cardio without calories/wearable;
- one anthropometry point;
- arm vs biceps false inference;
- stale memory conflicts with profile;
- trainer asks about client when only self is allowed;
- pain/medical question;
- photo analysis request;
- autonomous write request;
- «Почему?» rationale without chain-of-thought.

## 15. User-facing wording

Prefer:

- `повторы в запасе` before unexplained `RIR`;
- `соблюдение плана` before `adherence`;
- `облегчённая неделя` before `deload`;
- `данных пока недостаточно`;
- exact factual period and counts;
- qualified recommendation.

Avoid:

- `идеальный`;
- `гарантированно`;
- `организм требует` without evidence;
- `метаболизм сломан`;
- `эта мышца отстаёт` from one measurement;
- fake percentages/confidence;
- medical diagnosis.

## 16. Final domain gate

Before completion confirm:

- one canonical calculation;
- source/product heuristic documented;
- units/period/missing-data/sufficiency explicit;
- harmful inference excluded;
- UI and AI wording match limitations;
- permissions/privacy correct;
- deterministic tests cover boundaries;
- unresolved uncertainty stated honestly.
