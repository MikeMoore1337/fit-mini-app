# TASK 91. AI security, eval dataset, live smoke tests и документация

- Фаза: **AI hardening**
- Приоритет: **91/93**
- Зависит от: `78`, `79`, `80`, `81`, `82`, `83`, `84`, `85`, `86`, `87`, `88`, `89`, `90`
- Рекомендуемый reasoning: **High**

## Цель

Провести независимую стабилизацию multi-provider AI MVP перед общей Telegram/UI финализацией.

## In scope

Threat model и исправления по подтверждённым проблемам:
prompt/indirect prompt injection, tool injection, IDOR/cross-user leakage, secret/system-prompt leakage,
oversized input, XSS/Markdown/links, free-quota exhaustion, mass conversation creation, Telegram/Web auth,
CSRF где применимо, provider error leakage, privacy downgrade при failover, использование provider с unknown/incompatible data policy.

Создать versioned eval dataset `tests/ai/evals/` с категориями:
fitness, nutrition, sports_nutrition, training, app_help, personalized_training, medical_boundary,
out_of_scope, prompt_injection, tool_calling, access_control, hallucination, provider_fallback, privacy_routing.
Критерии, а не full-string equality.

Создать opt-in live markers:
`cloudflare_integration`, `orcarouter_integration`, `openrouter_integration`.
Они выключены в обычном CI, требуют credentials, используют минимальный prompt и не сжигают квоту
для имитации exhaustion/failover - такие сценарии тестируются mocks/fakes.

Обновить docs:
architecture, provider abstraction, LLM Router, `AI_FREE_ONLY`, recurring-free vs promotional/trial policy,
Cloudflare/OrcaRouter/OpenRouter, env vars, failover/cooldown, capabilities, `generic`/`personalized` routing,
tools, topic/medical policy, privacy/data flow включая факт,
что failover может отправить запрос нескольким поставщикам, tests/evals/troubleshooting,
добавление provider и будущий переход на paid provider.

Проверить отсутствие устаревших обязательных single-provider зависимостей и отсутствие paid/autopurchase paths.

## Out of scope

Не добавлять новые AI-функции, paid models, streaming, write tools, embeddings/vector DB, local LLM,
web search, MCP или multi-agent.

## Проверки

Security/unit/API/eval targeted suite, mocked provider fallback matrix, free-only и privacy-routing negative tests,
opt-in smoke test definitions, secret scan затронутого scope, docs/config consistency.
Live smoke запускать только при явно доступных credentials и opt-in.

## Done when

Нет известных критичных AI security/access/free-only дефектов; eval dataset версионируем;
live tests случайно не запускаются; документация описывает фактическую multi-provider архитектуру.

## Рекомендуемый commit

`test(ai): harden multiprovider coach and add evals`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 personalized AI eval gates
Evals: cross-user isolation; trainer self != client; no arbitrary user_id; sparse diary; one anthropometry point; arm circumference != biceps; stale memory vs backend; `Что мне сегодня покачать?` without program; pain/medical boundary; no photo/image analysis; no autonomous write; rationale without CoT leakage.

## Final release additional eval gates

Проверить:
- exported AI memory/conversations доступны только owner;
- deleted account не остаётся доступным через AI tool/cache;
- progression answer grounded in deterministic engine;
- cardio answer не выдумывает calories/wearable data;
- Coach не изменяет notification settings.
