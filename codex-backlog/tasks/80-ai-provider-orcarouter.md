# TASK 80. OrcaRouter Free provider

- Фаза: **AI provider adapters**
- Приоритет: **80/93**
- Зависит от: `77`
- Рекомендуемый reasoning: **High**

## Цель

Реализовать OrcaRouter как основной резервный бесплатный provider после Cloudflare и до OpenRouter,
с OpenAI-compatible transport там, где это действительно подтверждается актуальной документацией,
и с fail-closed policy для стоимости и пользовательских данных.

## In scope

Перед реализацией сверить актуальную официальную документацию OrcaRouter минимум по:

- API compatibility/authentication/endpoints;
- бесплатным routes/models и их текущим ограничениям;
- является ли free tier регулярно возобновляемым, а не разовыми promotional credits;
- tool calling и structured outputs;
- rate/quota/error semantics;
- data handling/retention для prompt, response, tool arguments/results;
- роль upstream model providers и ограничения их собственных data policies.

Не считать model aliases, список моделей, лимиты или privacy wording вечными. Адаптер должен использовать config
и neutral metadata из task `77`.

Реализовать `OrcaRouterProvider`:

- backend-only API key;
- model/route только через config;
- при `AI_FREE_ONLY=true` использовать только подтверждённый recurring-free route/model;
- запрещать paid fallback, auto top-up, purchase credits и unknown-cost routes;
- OpenAI-compatible request/response mapping переиспользовать только через существующую общую инфраструктуру,
  если это не создаёт provider leakage в domain layer;
- response/usage normalization;
- configured model/route и `actual_model`, если API его возвращает;
- capabilities по фактическому route/model;
- tool request разрешать только при подтверждённой `tools` capability;
- обязательный tool call, проигнорированный моделью, считать некорректным agentic result;
- нормализовать quota/rate limit, timeout/network/5xx, capacity/model/provider unavailable, malformed response;
- выставлять free-tier/data-policy metadata по актуальным официальным условиям;
- `personalized` разрешать только если подтверждённая provider/upstream policy удовлетворяет core contract;
- отсутствие/изменение такой гарантии не должно автоматически переводить запрос на менее приватный режим;
- `.env.example` без secrets.

## Experimental providers

NaraRouter и Pollinations.ai не входят в обязательный production MVP этой задачи.
Их можно добавить позже отдельными adapters после повторной проверки бесплатности, доступности и data policy.
Не добавлять фиктивные registry entries для providers, которых фактически нет в коде.

## Out of scope

Не реализовывать общий router/failover, topic gate, app tools или UI.
Не добавлять NaraRouter/Pollinations/AgentRouter/Token Harbor/FreeRouter adapters в рамках этой задачи.
Не использовать promotional credits как production free tier.

## Проверки

Unit tests минимум:

- auth/config;
- recurring-free route/model;
- paid/unknown/promo route blocked;
- success/usage/actual-model normalization;
- tools/structured output capability;
- ignored required tool;
- quota/429/timeout/network/5xx/malformed response;
- provider/upstream data-policy metadata;
- personalized request blocked при неподходящей/unknown policy;
- secret-safe logging.

Подготовить opt-in smoke seam, но не требовать live credentials в обычном CI.

## Done when

OrcaRouter adapter полностью изолирован за neutral provider API, годится как второй кандидат в бесплатной цепочке,
не использует разовые кредиты как production free tier и не обходит privacy/free-only guards.

## Рекомендуемый commit

`feat(ai): add orcarouter free provider`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
