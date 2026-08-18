# TASK 81. LLM Router - capability, privacy-aware failover и cooldown

- Фаза: **AI routing**
- Приоритет: **81/93**
- Зависит от: `78`, `79`, `80`
- Рекомендуемый reasoning: **High**

## Цель

Собрать бесплатные adapters в конфигурируемый LLM Router, который максимально использует доступные ресурсы,
но никогда не нарушает `AI_FREE_ONLY=true`, capability requirements или требования к обработке
персонализированного пользовательского контекста.

## In scope

Реализовать `LLMRouter` как generic ordered registry, не жёстко завязанный на три provider класса.

Порядок по умолчанию для MVP:

```text
Cloudflare Workers AI -> OrcaRouter -> OpenRouter Free
```

Порядок должен задаваться config, например через существующий settings pattern (`AI_PROVIDER_ORDER` или
эквивалент), а неизвестные/disabled providers должны обрабатываться безопасно.

Router учитывает на каждом candidate:

- enabled/disabled;
- `AI_FREE_ONLY` и recurring-free metadata;
- required capabilities;
- request data classification `generic` / `personalized`;
- provider data-policy compatibility;
- provider/model health/cooldown;
- request timeout.

Для `personalized` request candidate с неизвестной или неподходящей data policy пропускается с явным internal
skip reason. Router не имеет права понижать sensitivity до `generic`, удалять часть контекста наугад или
отправлять запрос менее подходящему provider только ради получения ответа.

Если higher layer не передал явную безопасную classification, использовать консервативную policy из task `77`.
Router не анализирует текст prompt эвристически для определения privacy level.

Реализовать:

- limited safe retry отдельно от failover;
- failover;
- per-provider cooldown с recovery;
- all-providers-unavailable fallback;
- provider attempt/skip telemetry hooks;
- reason codes минимум для capability mismatch, non-recurring/paid/unknown cost, data-policy mismatch,
  disabled/misconfigured, cooldown и transient provider errors.

Failover разрешён для rate limit/quota/capacity/model/provider unavailable, timeout, network/DNS/connection,
временных 5xx. `401/403` могут перейти дальше, но provider помечается misconfigured. `400/422` трактовать
прежде всего как adapter/payload problem и не гонять заведомо неверный запрос по всем API.

Cooldown не должен вызывать частые inference healthchecks. Если Redis уже есть и подходит - можно
переиспользовать; иначе безопасный process-local cache/synchronization без добавления Redis.

При `requires_tools=true` candidate обязан иметь подтверждённый `tools`. Если остаётся только provider без tools
или только privacy-incompatible provider - вернуть контролируемую недоступность персонального анализа,
а не псевдо-tool parsing или privacy downgrade.

Streaming в MVP не использовать: failover завершается до отдачи частичного ответа пользователю.

NaraRouter/Pollinations можно подключить в будущем только как реальные adapters, удовлетворяющие тому же
registry contract. Не создавать специальные `if provider == ...` ветки в router для будущих сервисов.

## Out of scope

Не реализовывать topic gate, app tools, conversations или UI. Не делать бесконечные retries, автопокупку credits,
paid fallback или fallback на promotional/trial routes. Не писать отдельные adapters для NaraRouter/Pollinations.

## Проверки

Unit tests минимум:

- default order Cloudflare -> OrcaRouter -> OpenRouter;
- custom order из config;
- disabled/unknown provider;
- capability matching;
- recurring-free/free-only guard;
- promo/paid/unknown-cost candidate skipped;
- `generic` request routing;
- `personalized` request выбирает только policy-compatible provider;
- unknown data policy не используется для personalized;
- отсутствие privacy-compatible provider -> controlled unavailable;
- router не downgrades data sensitivity;
- retry vs failover;
- quota/429, timeout/network/5xx;
- auth misconfigured;
- invalid_request без blind failover;
- cooldown/recovery;
- all unavailable;
- tool request без tool-capable provider;
- Cloudflare -> OrcaRouter и Cloudflare/OrcaRouter -> OpenRouter сценарии;
- provider attempt/skip counts и reason codes.

## Done when

Router детерминированно выбирает только подходящие recurring-free candidates, учитывает capabilities и data policy,
корректно переключается и останавливается. Исчерпание бесплатных или privacy-compatible путей заканчивается
безопасной временной недоступностью, а не расходами или передачей данных менее подходящему provider.

## Рекомендуемый commit

`feat(ai): add privacy aware free provider router`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
