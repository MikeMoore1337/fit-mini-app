# TASK 76. AI Coach - multi-provider integration audit

- Фаза: **AI foundation**
- Приоритет: **76/93**
- Зависит от: `22`, `38`, `40`, `41`, `43`, `44`, `48`, `58`, `59`, `60`, `61`, `75`
- Рекомендуемый reasoning: **High**

## Цель

После стабилизации основных продуктовых сервисов провести узкий read-only аудит именно для нового
бесплатного multi-provider AI Coach. Определить реальные точки интеграции и не тащить в реализацию
предположения из предыдущей single-provider архитектуры.

## In scope

Изучить существующие HTTP clients, config/feature flags, logging, retry/backoff, rate limiting, Redis и
background tasks при наличии; auth/RBAC; chat/message tables; AI/LLM abstractions; workout/program/history,
progress, nutrition, КБЖУ и heart-rate services; docs/FAQ/search; frontend integration point.

Определить:
- нейтральные provider DTO/interface и registry;
- capability model: `chat`, `tools`, `structured_output`, `streaming`, `reasoning`;
- где и как enforcing `AI_FREE_ONLY=true`;
- как отличать recurring free allocation от promotional/trial credits, paid и unknown-cost routes;
- neutral data-policy metadata и request classification `generic`/`personalized` без эвристики по prompt;
- provider config для Cloudflare Workers AI, OrcaRouter Free и OpenRouter Free;
- LLM Router, retry/failover/cooldown seams;
- конкретный read-only tool allowlist;
- privacy/data-minimization policy;
- knowledge retrieval mechanism без платных embeddings/vector DB;
- минимальные conversation/usage entities и API;
- abuse/rate-limit/concurrency controls;
- UI entry point в текущем shell;
- тестовые seam'ы для mocked adapters и opt-in live smoke tests.

Результат аудита хранить в `.artifacts/codex-audits/ai-multiprovider/`.

## Out of scope

Не писать AI-код, provider adapters, migrations, prompts или UI. Не выполнять реальные LLM-запросы.
Не повторять полный repository audit.

## Проверки

Проверить, что вывод основан на текущем коде после задач 03-19. Проверить отсутствие tracked changes.

## Done when

Есть конкретная минимальная архитектура multi-provider AI Coach, перечень provider/tool/API/UI integration
points и список уже существующих компонентов, которые надо переиспользовать. Commit не создаётся.

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 execution principle
AI Coach начинается только после core product, Demo, Admin, TMA, Landing, responsive и performance. Audit строит tool inventory по фактическим final API/domain contracts.

## Final release execution principle

AI Coach начинается только после tasks `00-75`.

К этому моменту приложение обязано быть полезным и полноценно работающим с `AI_FREE_ONLY=false`
или при полной недоступности всех AI providers.

AI audit строит tool inventory по фактически реализованным onboarding/training/nutrition/
progress/cardio/notification/account contracts.
