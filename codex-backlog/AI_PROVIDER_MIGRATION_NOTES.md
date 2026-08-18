# AI provider migration notes

## Historical decision

The earlier GigaChat-first approach was removed. The current AI Coach uses a free-only multi-provider architecture
and does not require GigaChat, Ministry of Digital Development certificates or a paid fallback.

The original `masters/ai-coach-multiprovider-master.md` remains useful for the broader AI Coach product design,
but its provider-selection sections are historical where they conflict with tasks `77-81` and `89`.
Those task files and `GLOBAL_RULES.md` are the current source of truth for provider/free-tier/privacy routing.

## Current AI block

```text
76 integration audit
77 provider core + recurring-free/data-policy guards
78 Cloudflare Workers AI
79 OpenRouter Free
80 OrcaRouter Free
81 privacy-aware router/failover/cooldown
82 topic/domain policy gate
83 app knowledge retrieval
84 read-only tools + agent loop
85 nutrition context tools
86 training/progress/anthropometry context
87 personalized memory/user context
88 evidence/confidence/rationale
89 conversations/API/privacy-aware telemetry
90 shared Web/Telegram AI UI
91 security/evals/docs
```

## Default production provider order

```text
Cloudflare Workers AI -> OrcaRouter -> OpenRouter Free
```

The order is configurable and the router must not be hard-coded to exactly three providers.

## Main free-only invariant

```text
AI_FREE_ONLY=true
```

The system may not automatically use paid inference, paid fallback, buy credits, auto-top-up or enable a paid tier.
Promotional/trial/free credits are not treated as a recurring production free tier.
If suitable recurring-free providers are unavailable, the user receives a controlled temporary-unavailable state.

## Privacy routing invariant

Requests are classified by trusted backend code as at least:

```text
generic
personalized
```

Authenticated AI Coach traffic defaults conservatively to `personalized` unless the backend explicitly proves that
no user-specific context is sent to the external LLM.

A `personalized` request may only use a provider/model whose currently verified data-policy metadata permits that
class. Unknown or incompatible policy is fail-closed. Router/failover may not downgrade sensitivity to get an answer.

## Deferred provider candidates

- NaraRouter - experimental candidate only after re-verifying recurring free tier and content retention/privacy terms.
- Pollinations.ai - experimental candidate only after re-verifying zero-cost availability, capabilities and data policy.
- AgentRouter / one-time credits - useful for development/evals, not a production recurring-free fallback.
- Token Harbor / time-limited free access - not a production recurring-free fallback.
- TeamoRouter / FreeRouter - not part of the current production MVP chain.

Do not create inactive/fake adapters just to list these services. Add them later as separate tasks only if they meet
current free-tier, privacy, reliability and capability requirements.

## Current downstream gates

- `92` production operational readiness;
- `93` final integrated audit.
