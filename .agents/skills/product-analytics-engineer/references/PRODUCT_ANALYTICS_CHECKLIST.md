# Product analytics checklist

## 1. Product question template

```text
Question:
Decision this metric informs:
Target population:
Journey:
Success definition:
Failure/abandonment definition:
Time window/timezone:
Required events:
Privacy/consent class:
Owner:
Validation plan:
```

Do not instrument until the question and decision are explicit.

## 2. Event specification template

```text
name
version
definition
trigger boundary
producer: client/server
subject identity class
required properties
optional properties
prohibited properties
idempotency/dedupe key
environment/surface
consent behavior
retention
expected volume
funnel/metric consumers
tests
owner/deprecation plan
```

## 3. Suggested YFC-level events

Names must follow repository convention. Examples of useful semantics:

- landing viewed / CTA selected;
- demo started / valuable demo action reached;
- login started/completed/failed by high-level provider type if allowed;
- onboarding started/completed;
- program selected/started;
- workout started/completed/abandoned;
- food logged;
- measurement logged;
- weekly check-in completed/skipped;
- adaptation previewed/applied/cancelled;
- progression suggestion shown/accepted/dismissed;
- trainer application/workspace high-level states;
- notification preferences changed;
- data export requested/completed;
- account deletion started/completed;
- cardio logged;
- AI request started/completed/failed/unavailable;
- AI rationale/memory controls used.

Do not include exact food, weight, macro, HR, distance, note or conversation values.

## 4. Property review

For every property ask:

- Is it required to answer the product question?
- Could it identify a person?
- Is it health/fitness-sensitive?
- Is it free text?
- Could it contain a token/URL/query parameter?
- Can it be a coarse category instead?
- Does an existing canonical field already answer the question elsewhere?
- Is the value stable across versions?
- Is it allowed by consent/privacy policy?

Prefer allowlist + schema rejection over best-effort redaction.

## 5. Producer ownership

Examples:

| Occurrence | Preferred producer |
| --- | --- |
| Screen actually rendered | Client |
| CTA intent | Client |
| Auth session established | Server |
| Program saved/started | Server |
| Workout completed | Server |
| Food/measurement persisted | Server |
| Export/delete job completed | Server |
| Error banner seen | Client only if needed |
| Provider/API technical failure | Observability, not product analytics by default |

If both client and server events exist, specify distinct semantics or dedupe.

## 6. Identity matrix

Test:

- anonymous landing;
- anonymous demo;
- auth start and complete;
- same user Web/TMA;
- multiple devices;
- multiple tabs;
- logout/login as another user;
- failed auth;
- account linking;
- trainer/admin capability;
- Demo fixtures;
- account deletion;
- opt-out.

No client-side merge by email/Telegram id.

## 7. Funnel definition

For each funnel record:

```text
population/denominator
entry step
ordered steps
completion
time limit
repeat handling
cross-device/account handling
exclusions
version/date range
```

Validate with synthetic journeys:

- complete;
- abandon at each step;
- repeat step;
- refresh/back;
- cross-device;
- delayed server outcome;
- duplicate client events;
- Demo vs real account.

## 8. Activation/retention

Activation should represent first useful outcome. Evaluate candidate definitions against:

- user value;
- measurability;
- resistance to accidental/empty events;
- time-to-value;
- Demo/auth context;
- product role differences.

Retention action should be meaningful and stable. Record day/week/month boundary and timezone.

## 9. Dedupe/idempotency tests

- React Strict Mode/dev rerender;
- route remount;
- double click;
- network retry;
- offline queue replay;
- server retry;
- duplicate job;
- multiple tabs;
- same action twice intentionally;
- late event;
- clock skew.

Dedupe key must not erase legitimate repeated workouts/meals/check-ins.

## 10. Environment/provider behavior

- production/test/staging separated;
- local development can be disabled or sent to isolated sink;
- provider unavailable does not block product;
- retry/queue bounded;
- payload schema validated before provider adapter;
- vendor-specific ids stay out of domain event;
- sampling policy documented;
- consent/opt-out enforced before external send;
- no sensitive session replay.

## 11. Data-quality monitors

Track where practical:

- total event volume by version/environment;
- invalid/unknown event rate;
- missing required property;
- duplicate rate;
- delivery failure;
- late/out-of-order;
- anonymous/auth transition anomaly;
- client/server reconciliation;
- funnel impossible order;
- sudden drop/spike;
- prohibited property detection;
- production contaminated by test/demo data.

## 12. Privacy regression payloads

Tests should reject or prevent accidental fields containing:

- exact weight/measurements/macros/calories;
- food/recipe name or notes;
- HR/distance;
- trainer comment;
- support message;
- AI prompt/answer/tool payload;
- email/phone/token/initData;
- uploaded filename/content;
- arbitrary URL query;
- raw database/Telegram id where not approved.

## 13. Dashboard/metric definition

Every dashboard metric should display or link to:

- definition;
- event versions;
- population;
- date/timezone;
- exclusions;
- known data-quality limitations;
- owner;
- last reviewed date.

Do not create a chart before definitions and validation queries agree.

## 14. Final rollout gate

- product question approved;
- event catalog updated;
- privacy/property review complete;
- consent behavior verified;
- event producers implemented once;
- schema/dedupe tests pass;
- representative journey checked;
- test/staging isolated;
- dashboard/query validated against known fixtures;
- operational failure non-blocking;
- limitations documented.
