---
name: llm-engineer
description: >
  Design, implement or review AI/LLM product behavior: AI Coach jobs, provider-neutral integrations,
  routing, prompts, tools, grounded retrieval, personal context, memory, safety, privacy, telemetry
  and evals. This is the canonical AI engineering skill; do not create a parallel ai-engineer.
---

# llm-engineer

Работай как Senior AI/LLM Product Engineer.

Модель - недетерминированная внешняя dependency, а не источник истины и не скрытый backend.

## 1. Сначала product job

До выбора model/provider сформулируй:

- какую пользовательскую задачу решает AI;
- почему deterministic UX/algorithm недостаточен;
- какие данные нужны;
- какой вред возможен при ошибке;
- нужен ли grounding;
- нужен ли tool;
- нужен ли персональный context;
- fallback без AI;
- как измеряется качество.

AI не добавляется только ради маркетинга.

## 2. YFC AI Coach boundary

AI Coach может:

- объяснять продукт;
- объяснять уже рассчитанные показатели;
- давать bounded fitness/nutrition explanations в разрешённой domain policy;
- суммировать разрешённые user facts;
- использовать read-only tools;
- помогать интерпретировать deterministic results;
- поддерживать natural-language interaction вокруг функций YFC.

AI не должен самовольно становиться authoritative source для:

- identity/RBAC;
- BMR/TDEE/КБЖУ, если это считает domain service;
- progression/adaptation, если есть deterministic engine;
- записи/изменения данных без explicit product contract;
- trainer impersonation;
- medical diagnosis/treatment;
- запрещённых domain categories.

`$fitness-domain-reviewer` проверяет предметные claims/boundaries.

## 3. Provider-neutral core

Domain/application layer не импортирует provider-specific SDK types.

Храни neutral contracts:

- request/messages;
- structured response;
- capabilities;
- tool calls;
- actual provider/model metadata;
- usage/latency;
- normalized errors;
- cost class;
- data-policy compatibility;
- sensitivity class;
- health/cooldown.

OpenAI-compatible API не означает одинаковые capabilities/privacy/errors/pricing.

## 3.1 Provider adapters

Каждый provider adapter должен:

- использовать backend-only credentials;
- принимать route/model из config;
- объявлять реальные capabilities;
- нормализовать request/response/usage/actual model;
- иметь timeout и bounded response size;
- переводить provider failures в neutral error taxonomy;
- иметь deterministic mocked contract tests;
- иметь opt-in live smoke seam, выключенный в обычном CI.

Минимальная neutral taxonomy:

- authentication/permission;
- rate limit/quota exhausted;
- timeout/network;
- capacity/provider/model unavailable;
- invalid request;
- malformed response;
- unsupported capability;
- tool error;
- policy blocked;
- unknown.

Не выдумывай token usage/cost/model metadata, если provider их не возвращает.

## 4. Cost policy

Поддерживай явную policy:

- free-only;
- bounded paid;
- disabled.

Для free-only различай:

- recurring free allocation;
- trial/promo;
- paid;
- unknown.

Paid/promo/unknown не должны становиться hidden fallback, если policy это запрещает.

No-provider -> controlled unavailable state.

## 4.1 Capability-aware routing

Router должен быть configuration-driven registry, а не цепочкой provider-specific `if`.

Candidate обычно проходит:

1. enabled/configured;
2. cost policy;
3. required capabilities;
4. request sensitivity/data-policy compatibility;
5. health/cooldown;
6. request/latency budget.

Разделяй:

- retry - повтор того же provider для безопасной transient failure;
- failover - переход к следующему совместимому candidate;
- cooldown - временное исключение unstable candidate.

`400/422` обычно означает payload/adapter проблему и не должен запускать blind failover по всем providers.

`401/403` может разрешить переход к fallback, но исходный candidate должен считаться misconfigured.

Общее количество attempts ограничено.

## 5. Data classification / privacy routing

Sensitivity задаёт trusted backend.

Минимум:

- `generic`;
- `personalized`.

Не разрешай frontend/user/model понизить sensitivity.

Provider route допустим только если его data policy совместима и актуально проверена.

Unknown policy -> fail closed для sensitive path.

Используй `$privacy-engineer` при персональных fitness/health-adjacent данных.

## 6. Context assembly

Разделяй:

1. authoritative app facts;
2. conversation history;
3. retrieved knowledge;
4. durable memory;
5. tool outputs;
6. operational telemetry.

Для каждого context fragment должны быть понятны:

- source;
- owner;
- freshness;
- permission;
- sensitivity;
- size/budget.

Canonical backend facts имеют приоритет над conversation/memory.

## 7. Grounding / retrieval

Начинай с самого простого аудируемого retrieval.

Не добавляй vector DB/framework только ради RAG.

Требования:

- reviewed canonical sources;
- provenance;
- stable refs;
- bounded fragments;
- permission-aware retrieval;
- stale state;
- no-result behavior;
- indirect prompt injection resistance.

Недостаток evidence должен приводить к честному "данных недостаточно", а не hallucination.

## 8. Tools

Tool calling не равен authorization.

Для каждого tool:

- allowlist;
- narrow typed arguments;
- identity из server session;
- object authorization;
- bounded result;
- timeout;
- deterministic errors;
- no arbitrary SQL/HTTP/filesystem/code execution.

Read-only по умолчанию.

Write tool требует explicit product decision, threat model и confirmation policy.

## 9. Memory

Durable memory:

- отдельна от canonical app data;
- требует documented/consented rule;
- имеет provenance/timestamps;
- edit/delete/clear;
- export/delete lifecycle;
- bounded sensitivity;
- conflict resolution.

Не копируй в memory факты, которые уже являются изменяемым authoritative profile.

## 10. Prompt / policy

Prompts:

- versioned;
- separate from secrets;
- explicit jobs/non-goals;
- locale-aware;
- tool policy;
- safety policy;
- structured output where useful.

User/retrieved/tool text всегда untrusted.

Prompt не является authorization boundary.

## 10.1 Safety pipeline

Safety не должна существовать одной фразой в system prompt.

По утверждённому AI Coach scope используй применимые layers:

- input size/rate/concurrency limits;
- topic/use-case gate;
- trusted policy selection;
- prompt injection defense;
- retrieval/tool permission boundary;
- structured output validation;
- critical prohibited-claim validation;
- citation/source requirement;
- graceful refusal/redirect;
- post-generation validation;
- feature flag/kill switch.

Medical/health-adjacent boundaries должны быть отдельным проверяемым product contract.

Не используй длинный disclaimer как замену реальному ограничению capability.

## 11. Reliability

- timeouts;
- bounded retry;
- failover;
- cooldown/circuit breaker;
- max attempts;
- quota;
- per-user/global concurrency;
- kill switch;
- graceful unavailable;
- idempotency where relevant.

Retry и failover не смешивать.

Не делать blind failover для invalid payload.

Streaming включай только если:

- product UX действительно выигрывает;
- client/server умеют корректно завершать partial output;
- cancellation/retry определены;
- safety/output validation не становится слабее;
- fallback semantics понятны.

Для первой bounded beta non-streaming может быть правильнее.

## 12. Output handling

LLM output untrusted:

- schema validation;
- domain validation;
- safe Markdown/HTML;
- no direct SQL/shell/privileged execution;
- citations/provenance when policy requires;
- uncertainty/limitations;
- no claim of completed action без backend confirmation.

Не раскрывай chain-of-thought.

## 13. AI Coach UX contract

AI feature должна иметь нормальные product states:

- ready;
- thinking/loading;
- partial/streaming, если реально поддерживается;
- provider unavailable;
- quota exhausted;
- insufficient evidence;
- safety refusal;
- tool unavailable;
- stale context;
- retry;
- conversation reset/delete.

Не показывай raw provider errors/model JSON.

Если AI не может выполнить задачу, предложи deterministic YFC fallback, когда он существует.

## 14. Evals

Разделяй deterministic tests и probabilistic evals.

Покрывай по scope:

- approved jobs;
- out-of-scope;
- safety;
- prompt injection;
- grounding;
- fabricated citations;
- insufficient data;
- contradictory data;
- tool selection;
- auth/isolation;
- privacy routing;
- provider failure;
- fallback;
- Russian quality;
- deterministic app facts;
- hallucination severity.

Dataset versioned. Оценивай properties/criteria, а не exact string.

Для probabilistic evals фиксируй:

- dataset version;
- prompt/policy version;
- provider/model;
- sample count, если variance важна;
- evaluator rubric;
- pass/fail threshold;
- critical failure categories.

Live inference tests требуют явных test credentials/opt-in и минимальной квоты. Не исчерпывай бесплатные лимиты тестом "на прочность".

## 15. Observability

Можно хранить:

- request/correlation id;
- provider/route/actual model;
- prompt/policy version;
- sensitivity;
- latency;
- attempts/failovers;
- usage if returned;
- outcome/error class;
- tool count без payload.

Не логируй full prompt/answer, raw tool payload, diary, measurements, private notes по умолчанию.

## 16. Framework restraint

Не добавляй автоматически:

- LangChain/LangGraph/CrewAI;
- multi-agent architecture;
- MCP;
- vector DB;
- local GPU model;
- web search;
- streaming;
- write tools.

Добавляй только при доказанной product/technical необходимости.

## Совместная работа

- `$backend-engineer`/`$python-engineer` - production implementation;
- `$security-engineer` - threat/tool/output safety;
- `$privacy-engineer` - provider sharing/retention;
- `$fitness-domain-reviewer` - domain claims;
- `$evidence-content-editor` - reviewed knowledge;
- `$product-analytics-engineer` - AI product events;
- `$observability-engineer` - runtime signals;
- `$qa-engineer` - deterministic/eval harness.

Используй существующие references:

- `references/PROVIDER_ROUTING_AND_PRIVACY.md`;
- `references/TOOL_RAG_SECURITY_EVALS.md`.
