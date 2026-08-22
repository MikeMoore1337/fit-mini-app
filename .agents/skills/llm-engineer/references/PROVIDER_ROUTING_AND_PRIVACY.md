# Provider routing and privacy checklist

## 1. Provider verification record

Before enabling a provider/model in production, record:

```text
provider
route/model/alias
transport/API version
verified official sources
verified_at
configured model vs actual model behavior
capabilities
recurring-free / promo / paid / unknown
paid fallback possible?
quota/rate semantics
content retention/training/processing policy
upstream provider implications
allowed request data classes
known limitations
owner/reviewer
```

Do not treat this record as permanent. Add a review trigger for provider/model/pricing/policy changes.

## 2. Neutral contracts

The provider core should express without provider-specific types:

- request/messages/roles/content parts;
- tool schema and tool-call result;
- response candidates/final output;
- configured route and actual model;
- nullable usage dimensions;
- capabilities;
- health/cooldown;
- normalized error;
- free-tier classification;
- data-policy classification and source marker;
- request data class;
- attempt/skip reason.

Avoid a universal `dict[str, Any]` contract that silently leaks provider differences into domain code.

## 3. Capability matching

Candidate must explicitly satisfy requested capabilities.

Examples:

- `requires_tools` needs confirmed tool calling;
- `requires_structured_output` needs a tested structured-output contract;
- a model that sometimes prints JSON is not automatically structured-output capable;
- OpenAI-compatible endpoint does not prove tool/streaming/reasoning parity;
- ignored required tool call is an invalid result, not success;
- text parsing must not emulate privileged tool calling.

Capabilities may be model/route-specific, not only provider-wide.

## 4. Cost classification

Recommended enum/contract:

```text
recurring_free
promotional_or_trial
paid
unknown
```

At free-only gate:

- allow only `recurring_free`;
- reject `promotional_or_trial`, `paid`, `unknown`;
- reject automatic route that may choose paid model;
- reject missing/expired verification metadata according to project policy;
- do not infer free status from model name alone;
- do not automatically purchase/top up/upgrade.

Controlled unavailable is a valid product state.

## 5. Request data class

Minimum:

```text
generic
personalized
```

`personalized` includes context containing or derived from:

- conversation history tied to a user;
- profile/goals/preferences;
- food diary/targets;
- workouts/program/history;
- progress/anthropometry/cardio;
- durable memory;
- trainer/client data;
- user-specific tool results.

Classification is set by trusted backend code. The UI cannot downgrade it. Prompt-text heuristics are not a
privacy control.

Default authenticated request to `personalized` unless a narrow trusted path proves no user-specific context is
sent externally.

## 6. Provider data-policy compatibility

A provider/model candidate is eligible for a request class only when current verified metadata explicitly permits it.

Fail closed when:

- policy is unknown;
- terms conflict;
- upstream model provider is unknown where relevant;
- retention/training status cannot satisfy project policy;
- verification is stale under project rules;
- route may silently change to a model with incompatible policy.

Router must not:

- downgrade `personalized` to `generic`;
- strip context opportunistically without a defined alternate product flow;
- send the same sensitive request to incompatible fallback;
- expose the reason in a way that reveals internal provider configuration to the user.

Internal skip reason should remain observable.

## 7. Candidate selection algorithm

Reference order:

```text
for candidate in configured_order:
    if disabled/unconfigured: skip
    if cost policy incompatible: skip
    if capability mismatch: skip
    if data policy incompatible: skip
    if cooldown/unhealthy: skip
    attempt with timeout
    if success and response valid: return
    if retryable and retry budget available: retry same candidate
    if failover-eligible: continue
    stop on deterministic invalid request/adapter bug
return controlled unavailable
```

The exact order can differ, but cost/privacy/capability gates must occur before sending data.

## 8. Retry and failover taxonomy

Usually failover-eligible:

- rate limited;
- recurring free quota exhausted;
- capacity exceeded;
- model/provider unavailable;
- timeout;
- network/DNS/connection;
- temporary 5xx.

Special handling:

- `401/403`: mark misconfigured; optional failover;
- `400/422`: likely payload/adapter bug; avoid blind fan-out;
- malformed response: bounded retry/failover based on known provider behavior;
- safety refusal: not automatically a provider outage;
- policy block: do not retry another provider unless the request itself remains allowed and next candidate is compatible.

Keep retry and failover budgets separate and bounded.

## 9. Cooldown and concurrency

- Cooldown per provider/route, not global unless justified.
- Quota/rate/capacity errors can set different cooldown categories.
- Recovery should not use frequent inference healthchecks.
- If no shared cache exists, a process-local implementation may be sufficient for MVP, but document multi-process limitations.
- Add synchronization to prevent stampede after cooldown expiry.
- Bound total attempts per user request.
- Bound global concurrency and per-user concurrency.

## 10. Adapter test matrix

For each adapter:

- disabled/missing config;
- auth success/failure;
- valid recurring-free route;
- paid/promo/unknown blocked;
- model/route config;
- actual model mapping;
- capabilities;
- chat success;
- structured output success/failure;
- tools success/ignored required tool;
- usage present/absent/provider-specific unit;
- 429/quota;
- timeout/network/5xx;
- invalid request;
- malformed response;
- data-policy metadata;
- personalized allowed/blocked;
- no secret/full prompt leakage.

## 11. Router test matrix

- default/custom order;
- unknown/disabled provider;
- capability mismatch;
- cost mismatch;
- generic routing;
- personalized routing;
- unknown policy blocked;
- no compatible provider;
- no sensitivity downgrade;
- retry vs failover;
- auth misconfiguration;
- invalid request stops blind fan-out;
- cooldown and recovery;
- max attempts;
- tool-required without tool-capable provider;
- attempt/skip telemetry and reason codes;
- deterministic controlled unavailable response.

## 12. User-facing status

Do not expose:

- API key/account id;
- raw provider error;
- internal provider order;
- policy details that could aid abuse;
- promised availability of a particular free provider.

Useful states:

- AI disabled;
- temporarily unavailable;
- general chat available but personalized/tool analysis unavailable;
- request too large/rate limited;
- safe policy boundary response.

## 13. Sources to re-check

- Each provider's official API, pricing/free-tier and privacy/data-processing documentation.
- OWASP GenAI Security Project: https://genai.owasp.org/
- Current OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/

Never rely on a third-party comparison article as the only source for pricing, capability or data policy.
