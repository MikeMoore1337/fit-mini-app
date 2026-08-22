---
name: llm-engineer
description: >
  Design, implement or review provider-neutral LLM integrations, routing, prompts, tool calling,
  grounded retrieval, memory, safety, telemetry and evals. Use when application behavior invokes
  an LLM or depends on model capabilities. Do not use for deterministic recommendation engines or
  ordinary backend work that has no model call.
---

# llm-engineer

Строй LLM-подсистему как недоверенную внешнюю интеграцию, а не как источник истины или скрытый
универсальный backend.

## Главный принцип

Разделяй ответственность:

```text
детерминированный расчёт, authorization, validation и write policy -> приложение
генерация, объяснение, классификация и bounded selection -> LLM
```

Модель не должна пересчитывать то, что уже корректно рассчитывает доменный сервис, определять
identity, обходить RBAC или самостоятельно решать, какие персональные данные можно передавать наружу.

## Сначала

Перед изменением кода:

- прочитай `AGENTS.md`, task, релевантные `docs/`, current config и data lifecycle;
- найди существующие HTTP clients, retry/rate-limit, feature flags, persistence, search и telemetry;
- проверь текущую архитектуру auth/RBAC и источники доменных данных;
- изучи фактические provider adapters и tests, не создавай дублирующий AI layer;
- сверяй pricing/free tier, model IDs, capabilities, limits, errors, retention и data policy только
  с актуальными официальными источниками на момент реализации;
- не выполняй live inference без явного opt-in и доступных test credentials;
- не считай формулировки backlog или старые docs вечными provider guarantees.

## Provider-neutral core

Domain/application layer не импортирует SDK или типы конкретного provider.

Определи нейтральные contracts для:

- messages/request/response;
- tool definitions и tool calls;
- usage, latency и actual model;
- capabilities;
- health/cooldown;
- normalized errors;
- free-tier/cost policy;
- data-policy compatibility;
- request data classification.

Capabilities должны быть явными, например:

- `chat`;
- `tools`;
- `structured_output`;
- `streaming`;
- `reasoning`.

Не считай, что OpenAI-compatible transport означает одинаковые capabilities, errors, limits,
pricing или privacy.

## Стоимость и free-only policy

Если продукт требует free-only режим, enforce его кодом до network call.

Различай минимум:

- recurring free allocation;
- promotional/trial/one-time credits;
- paid;
- unknown.

При free-only:

- paid и unknown-cost routes блокируются;
- trial/promo credits не становятся production fallback без явного решения;
- auto-router с возможностью paid inference блокируется;
- запрещены automatic top-up, purchase credits и hidden paid fallback;
- отсутствие подходящего route заканчивается controlled unavailable state.

Не хардкодь динамические provider limits или model catalogs в public API contract.

## Data classification и privacy routing

Request sensitivity задаёт доверенный backend-код, а не пользователь, frontend или эвристика по
тексту prompt.

Минимально различай:

- `generic` - наружу не уходит user-specific history/profile/tool context;
- `personalized` - request/context может содержать данные конкретного пользователя.

Authenticated AI request по умолчанию трактуй консервативно, если backend не доказал обратное.

Для каждого provider/model храни проверяемую metadata:

- какие данные допускаются;
- retention/training/processing status, если это релевантно contract;
- upstream provider implications;
- source и дата последней проверки;
- unknown state.

Unknown или incompatible policy работает fail-closed. Router не может понизить sensitivity,
удалить данные наугад или выбрать менее приватный route только ради ответа.

Используй также `$privacy-engineer` для персональных, health и fitness данных.

## Provider adapters

Каждый adapter обязан:

- использовать backend-only credentials;
- принимать model/route через config;
- выставлять capabilities по фактически выбранной модели;
- нормализовать request/response/usage/actual model;
- иметь timeout и bounded response size;
- переводить provider errors в neutral taxonomy;
- не логировать secret, full prompt, full response или raw tool payload;
- поддерживать mocked contract tests;
- иметь opt-in live smoke seam, выключенный в обычном CI.

Нормализуй минимум:

- authentication/permission;
- rate limit/quota exhausted;
- timeout/network;
- capacity/provider/model unavailable;
- invalid request;
- invalid/malformed response;
- unsupported capability;
- tool error;
- unknown.

`400/422` обычно указывает на payload/adapter issue и не должен бездумно уходить во все providers.
`401/403` может разрешить failover, но candidate нужно пометить misconfigured.

Не выдумывай token count, usage или policy value, если provider их не возвращает.

## Router, retry, failover и cooldown

Router должен быть generic ordered registry из конфигурации, а не цепочкой специальных `if` для
известных providers.

Candidate проходит проверки в предсказуемом порядке:

1. enabled и configured;
2. cost/free-only policy;
3. required capabilities;
4. request data class и data-policy compatibility;
5. cooldown/health;
6. request timeout/budget.

Разделяй:

- **retry** - ограниченная повторная попытка того же provider при безопасной transient error;
- **failover** - переход к следующему подходящему candidate;
- **cooldown** - временное исключение provider без частых inference healthchecks.

Ограничивай общее число attempts. Не допускай retry storms и quota exhaustion одним request.

Streaming включай только если архитектура умеет безопасно завершать partial response. Если failover должен
происходить до пользовательского вывода, streaming в этой версии не нужен.

## Prompt и domain policy

System/developer prompts:

- хранятся отдельно и versioned;
- описывают scope, safety, privacy, tools и ограничения;
- не содержат secrets;
- не являются единственной authorization boundary;
- не считаются надёжно скрытыми от пользователя.

User text, retrieved documents, knowledge snippets и tool outputs всегда считай недоверенными данными.
Не разрешай им переопределять system policy.

Topic gate, если он нужен:

- классифицирует, а не отвечает;
- не получает лишние персональные данные и tools;
- возвращает строгую валидируемую структуру;
- имеет safe fallback при недоступности model;
- не удваивает LLM calls без измеримой необходимости.

Medical/safety boundary должен быть отдельной проверяемой product policy, а не случайной фразой в prompt.

## Tools и bounded agent loop

Tool calling не равен authorization.

Для каждого tool:

- allowlist;
- узкая функция;
- минимальные permissions;
- typed/validated arguments;
- identity из server auth/session, не из model-supplied `user_id`;
- object-level authorization;
- bounded result size;
- timeout и predictable error;
- отсутствие arbitrary SQL, HTTP, filesystem, code execution или secret access;
- безопасная сериализация результата.

Read-only по умолчанию. Write tools требуют отдельного threat model, explicit product decision,
server-side policy и, где уместно, human confirmation. Не добавляй write capability только потому,
что provider поддерживает functions.

Agent loop ограничивай:

- max tool rounds;
- max total provider attempts;
- context/token/character budget;
- max tool result size;
- repeat-call/cycle detection;
- controlled fallback.

Ignored required tool call или произвольный text вместо обязательной structured action не считай
корректным agentic result.

## Retrieval и knowledge

Начинай с минимального подходящего retrieval:

- существующий search;
- PostgreSQL FTS;
- структурированный Markdown/content index;
- другой локальный bounded index.

Не добавляй embeddings/vector DB/framework только ради модного RAG.

Требования:

- canonical reviewed source of truth;
- provenance и stable document/section ids;
- bounded fragments;
- permission-aware retrieval;
- отсутствие private/custom данных в public corpus;
- injected instructions внутри документа игнорируются;
- no-result приводит к признанию недостатка информации, а не hallucination;
- индекс обновляется вместе с source content и имеет regression tests.

## Conversations, memory и authoritative data

Не смешивай:

1. **authoritative app data** - профиль, программа, дневник, расчёты;
2. **conversation history** - сообщения конкретного диалога;
3. **durable memory** - явно сохранённые устойчивые предпочтения;
4. **operational telemetry** - технические попытки и ошибки.

Durable memory создаётся только явно или по документированному high-confidence rule, имеет provenance,
owner, timestamps, optional expiry и пользовательские edit/delete/clear controls.

Не копируй изменяемые app facts в memory. При конфликте canonical backend data имеет приоритет.
Conversation и memory входят в применимые export/delete/retention contracts.

## Output handling

LLM output недоверенный:

- structured output валидируй schema и business rules;
- ссылки, Markdown/HTML и media рендери безопасно;
- не передавай output напрямую в SQL, shell, template interpreter или privileged API;
- не считай модельное утверждение подтверждённым фактом без grounding;
- не показывай raw tool calls, provider errors или internal JSON пользователю без осознанного UX;
- не утверждай, что write выполнен, если backend его не выполнил.

Не раскрывай chain-of-thought. Для объяснимости отдавай краткий product rationale: факты, источник,
период, достаточность данных и ограничения.

## Telemetry и abuse protection

Operational telemetry может хранить:

- request/correlation id;
- provider/configured route/actual model;
- request type и data class;
- attempts, skips, failovers и reason codes;
- nullable usage;
- latency/status/error class;
- tool call count без payload;
- policy metadata marker.

Не записывай full prompt/answer, raw tool args/results, food diary, weight, measurements или other
private content в обычные logs/metrics.

Добавь per-user и global rate/concurrency limits, input/history/output budgets и bounded conversation
creation. Один пользователь не должен легко исчерпать общую квоту параллельными запросами.

## Tests и evals

Разделяй deterministic tests и model evals.

Deterministic tests:

- provider contracts и error mapping;
- free-only/data-policy guards;
- routing order, retry/failover/cooldown;
- auth/RBAC/tool validation;
- persistence/lifecycle;
- telemetry redaction;
- output sanitization;
- rate/concurrency.

Evals:

- versioned dataset;
- категории и критерии, а не full-string equality;
- allowed/out-of-scope/medical boundary;
- direct и indirect prompt injection;
- tool selection и no-tool-capable state;
- hallucination/grounding;
- sparse/contradictory data;
- cross-user isolation;
- provider fallback и privacy routing;
- no chain-of-thought leakage.

Live tests выключены по умолчанию, требуют явный marker/credentials, используют минимальную квоту и не
пытаются искусственно исчерпать бесплатный лимит.

Для подробной реализации используй:

- `references/PROVIDER_ROUTING_AND_PRIVACY.md`;
- `references/TOOL_RAG_SECURITY_EVALS.md`.

## Не добавляй без доказанной необходимости

- LangChain/LangGraph/CrewAI или другой тяжёлый orchestration framework;
- multi-agent architecture;
- MCP;
- web search;
- local LLM/GPU;
- платные embeddings/vector DB;
- provider-specific типы в domain layer;
- write tools;
- hidden paid fallback;
- streaming.

## Совместная работа с другими skills

- `$backend-engineer` и `$python-engineer` - production implementation;
- `$security-engineer` - threat model, output/tool safety и access control;
- `$privacy-engineer` - provider sharing, retention и lifecycle;
- `$fitness-domain-reviewer` - корректность фитнес/питание interpretations;
- `$evidence-content-editor` - reviewed public/editorial knowledge;
- `$product-analytics-engineer` - high-level AI product events без raw text;
- `$observability-engineer` - operational metrics и alerts;
- `$qa-engineer` - test strategy и eval harness.

## Финальный отчёт

Укажи:

- provider-neutral contracts и adapters;
- cost/free-only и privacy routing decisions;
- tools/retrieval/memory scope;
- tests/evals/live smoke, реально выполненные;
- какие provider условия были перепроверены и на какую дату;
- data sharing, retention и remaining risks;
- controlled unavailable behavior.
