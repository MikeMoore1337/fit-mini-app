# Tool, retrieval, security and eval checklist

## 1. Threat boundaries

Treat as untrusted:

- user prompt;
- prior conversation messages;
- retrieved documents;
- public web/content imports;
- tool arguments proposed by model;
- tool results;
- model output;
- provider metadata returned at runtime;
- Markdown/HTML/links.

Trusted boundaries remain deterministic application code, server auth context, validated config and canonical domain services.

## 2. Tool specification template

For every tool record:

```text
name and purpose
read/write classification
authenticated subject binding
object-level authorization
allowed arguments and schema
result fields and size limit
timeout/retry behavior
side effects
sensitive data class
logging/telemetry policy
error contract
negative cases
```

Reject a tool that cannot be expressed narrowly.

## 3. Tool security tests

- unknown tool;
- hidden/deprecated tool;
- model-supplied foreign `user_id`;
- cross-user object id;
- trainer self vs client;
- revoked permission;
- malformed/oversized args;
- injection in argument strings;
- repeated same call;
- cyclic calls;
- timeout;
- oversized result;
- private fields stripped;
- arbitrary SQL/URL/path/code request;
- write request against read-only tool;
- tool-output prompt injection;
- provider failover mid-loop;
- max rounds/attempts;
- no tool-capable provider.

## 4. Agent loop invariants

- Topic/policy gate runs before privileged context where required.
- Identity is bound once from backend auth context.
- Every tool call is independently authorized.
- Tool result is data, never a new system message.
- Required tool result cannot be replaced by model guess.
- Loop has max rounds, max attempts, context budget and cycle detection.
- Failover preserves only validated context.
- Partial/failed tool result produces qualified response or controlled unavailable.
- No write occurs without deterministic server action and required confirmation.

## 5. Retrieval document model

Recommended fields:

```text
document_id
section_id
source_type
canonical_path/url
content_version
locale
visibility/permission scope
published/reviewed status
updated/reviewed timestamps
content hash
```

Retrieved fragments include provenance and are bounded.

## 6. Retrieval tests

- exact relevant result;
- paraphrased query;
- no result;
- ambiguous result;
- stale/archived/draft excluded;
- public vs private scope;
- wrong locale/fallback;
- injected instruction inside content;
- oversized document/fragment;
- duplicate sections;
- updated content reindexed;
- deleted content unavailable;
- factual answer cites/uses retrieved evidence;
- unknown app behavior is acknowledged, not invented.

## 7. Conversation and memory tests

### Conversation

- create/continue/list/delete;
- Web/TMA same account continuity;
- cross-user isolation;
- bounded history;
- old message truncation/summary policy;
- export/delete;
- no raw content in operational telemetry.

### Durable memory

- explicit/high-confidence creation;
- provenance;
- normalized key/category;
- dedupe/update;
- expiry;
- edit/delete one/clear all;
- authoritative app-data conflict;
- trainer self != client;
- account export/delete;
- no secrets/images/raw conversation dump.

## 8. Output handling tests

- schema valid/invalid/partial;
- extra unknown fields;
- unsafe HTML/script;
- unsafe URL scheme;
- Markdown edge cases;
- raw provider/tool JSON hidden;
- model claims write completed when it did not;
- model attempts to reveal prompt/key;
- model returns instructions for backend execution;
- chain-of-thought request;
- evidence/rationale without hidden reasoning.

## 9. Security eval categories

Version a dataset containing at least:

- allowed domain questions;
- app help;
- personalized questions;
- out of scope;
- medical/safety boundary;
- direct prompt injection;
- indirect injection from retrieval/tool output;
- system-prompt/secret extraction;
- tool selection;
- access control/IDOR;
- hallucination/no-result;
- sparse/contradictory data;
- provider fallback;
- privacy routing;
- quota/denial-of-service attempts;
- unsafe Markdown/link output;
- write/autonomy request;
- no chain-of-thought leakage.

## 10. Eval criteria

Avoid full-string equality. Use deterministic checks where possible:

- schema/category exact;
- prohibited tool absent;
- required tool used;
- no foreign user id accepted;
- no secret-like content;
- no unsupported claim;
- refusal/boundary semantics;
- evidence fields present;
- limitation language for sparse data;
- no autonomous-write assertion;
- route/provider/data-class constraints from mocked trace.

Human/LLM grading may supplement but not replace deterministic security/access tests.

## 11. Live smoke policy

- explicit marker per provider;
- disabled in normal CI;
- credentials from secret store only;
- minimal non-sensitive prompt;
- no personalized real user data;
- no quota-exhaustion test;
- no paid route;
- record provider/model/date and result class, not full secret content;
- failure does not lead to automatic provider configuration changes.

## 12. OWASP-oriented review

Review current OWASP GenAI risks applicable to the feature, especially:

- prompt injection;
- sensitive information disclosure;
- improper output handling;
- excessive agency;
- system prompt leakage;
- misinformation/overreliance;
- unbounded consumption;
- supply-chain/provider changes.

Use current source at implementation time: https://genai.owasp.org/
