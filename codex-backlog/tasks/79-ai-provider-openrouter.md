# TASK 79. OpenRouter Free provider

- Фаза: **AI provider adapters**
- Приоритет: **79/93**
- Зависит от: `77`
- Рекомендуемый reasoning: **High**

## Цель

Реализовать бесплатный OpenRouter provider как дополнительный fallback за нейтральным интерфейсом.
Он не является основанием для ослабления `AI_FREE_ONLY` или privacy policy только ради доступности ответа.

## In scope

Перед реализацией сверить актуальную официальную документацию OpenRouter минимум по:

- free router и бесплатным model routes;
- актуальным free limits;
- tool calling/structured output;
- provider routing/data-policy controls;
- фактической модели/upstream metadata, доступной в response/API;
- условиям, при которых бесплатный route может или не может гарантировать допустимую обработку content.

Реализовать `OpenRouterProvider`:

- backend-only Bearer key;
- при `AI_FREE_ONLY=true` разрешать только подтверждённые регулярно бесплатные routes/models;
- paid model slug, unknown-cost route, promo credits и paid fallback блокировать core guard из task `77`;
- не требовать покупки credits для MVP;
- configured model/route и фактический `actual_model`, если он доступен, отдавать в neutral telemetry contract;
- считать набор free models динамическим;
- корректно передавать требования tool request, чтобы routing выбирал совместимую бесплатную модель;
- если обязательный tool call проигнорирован, не считать agentic result корректным;
- нормализовать 429/free limit, timeout, 5xx, malformed response и прочие errors;
- выставлять provider free-tier/data-policy metadata на основании актуальных официальных гарантий;
- если `openrouter/free` или иной динамический free router не может гарантировать допустимую policy для
  персонализированного контекста на всех возможных upstream providers, не объявлять его `personalized`-safe;
- не подменять отсутствие privacy guarantee предположением;
- `.env.example` без secrets.

## Out of scope

Не реализовывать общий failover/router, topic gate, user tools, paid OpenRouter или UI.
Не заставлять пользователя покупать credits ради production MVP.

## Проверки

Unit tests минимум:

- Bearer auth;
- разрешённый free route/model;
- actual model normalization;
- paid/unknown/promo route blocked by `AI_FREE_ONLY`;
- 429/free limit;
- tools/structured response;
- ignored required tool;
- timeout/5xx/invalid response;
- provider metadata/free-tier/data-policy mapping;
- personalized request не проходит через route с неподтверждённой policy;
- secret-safe logging.

## Done when

OpenRouter adapter безопасно использует только допустимые бесплатные routes/models и отдаёт нейтральные
responses/errors/capabilities/policy metadata без утечки provider-specific типов в AI domain.

## Рекомендуемый commit

`feat(ai): add openrouter free provider`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
