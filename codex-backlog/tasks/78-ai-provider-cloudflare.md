# TASK 78. Cloudflare Workers AI provider

- Фаза: **AI provider adapters**
- Приоритет: **78/93**
- Зависит от: `77`
- Рекомендуемый reasoning: **High**

## Цель

Реализовать основной бесплатный provider MVP - Cloudflare Workers AI - за нейтральным интерфейсом и
с явной metadata по бесплатности, capabilities и допустимости персонализированного контекста.

## In scope

Перед реализацией сверить актуальную официальную документацию Cloudflare Workers AI минимум по:

- REST API и authentication;
- актуальной free allocation/pricing модели;
- отсутствию автоматического paid fallback для выбранной конфигурации;
- errors/rate limits/quota semantics;
- доступным моделям и function calling/structured output;
- официально заявленной обработке/retention пользовательского content, достаточной для provider metadata из task `77`.

Не переносить численные лимиты или model IDs из backlog как вечные константы. Зафиксировать в config/docs только
то, что необходимо для работы, а изменяемые условия проверять по официальным источникам при реализации.

Реализовать `CloudflareWorkersAIProvider` через существующий HTTP client/`httpx`, если этого достаточно:

- backend-only `Account ID` и API Token;
- model ID только через config;
- только подтверждённый регулярно доступный бесплатный режим при `AI_FREE_ONLY=true`;
- никакого автоматического включения Workers Paid/paid inference;
- response/usage normalization;
- provider-specific units/neurons отдельно от token metrics;
- error mapping, включая quota exhaustion, 429, capacity/model/provider unavailable, timeout/network/5xx;
- capabilities по фактически выбранной модели;
- tool requests только на модели с подтверждённым function calling;
- provider metadata/free-tier/data-policy из task `77` по актуально подтверждённым официальным условиям;
- если policy для `personalized` нельзя подтвердить - adapter остаётся доступным для допустимого класса запросов,
  но не должен сам ослаблять privacy guard;
- healthcheck без частых inference-запросов;
- `.env.example` без secrets.

Не считать конкретный model ID, лимит или pricing wording вечными.

## Out of scope

Не создавать Cloudflare Worker только как прокси, если backend может вызывать REST API напрямую.
Не реализовывать router/failover, domain policy или UI. Не включать платный режим.

## Проверки

Unit tests минимум:

- auth/account/model config;
- success и malformed/empty response;
- usage/neurons mapping;
- recurring-free metadata;
- free quota exhausted;
- 429/5xx/timeout/network;
- tool call совместимой модели;
- unsupported tool capability;
- personalized request блокируется core policy, если adapter metadata не разрешает его;
- secret-safe logging.

Подготовить opt-in marker/smoke seam, но live credentials не обязательны.

## Done when

Cloudflare adapter полностью изолирован за neutral provider API, корректно сообщает capabilities/errors/free-tier/
data-policy metadata и не способен автоматически перейти на платный inference или обойти privacy guard.

## Рекомендуемый commit

`feat(ai): add cloudflare workers ai provider`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
