# TASK 77. AI provider core - neutral DTO, free-tier policy и data-sensitivity guard

- Фаза: **AI provider foundation**
- Приоритет: **77/93**
- Зависит от: `76`
- Рекомендуемый reasoning: **High**

## Цель

Создать provider-independent фундамент AI Coach, который позволяет подключать и заменять бесплатные LLM API
без изменений domain layer, отличает постоянный бесплатный тариф от промо-кредитов/триала и не отправляет
персонализированный пользовательский контекст провайдеру с неподходящей или неизвестной политикой обработки данных.

## In scope

Создать в стиле проекта нейтральные структуры:
`LLMRequest`, `LLMMessage`, `LLMTool`, `LLMToolCall`, `LLMResponse`, `LLMUsage`,
`ProviderCapabilities`, `ProviderHealth`, `ProviderError` и нейтральные error types.

Создать `LLMProvider` Protocol/interface и provider registry. Capability model минимум:
`chat`, `tools`, `structured_output`, `streaming`, `reasoning`.

Добавить нейтральные provider metadata/policy contracts, не привязанные к конкретному API.
Точные имена типов выбрать по стилю проекта, но они должны выражать как минимум:

- тип бесплатности: recurring/free allocation, promotional/trial/credits, paid, unknown;
- может ли route/model автоматически перейти на платный inference;
- подтверждена ли политика хранения/обработки prompt/response/tool content;
- допускается ли provider для персонализированного пользовательского контекста;
- источник/дата последней проверки policy metadata, если проект уже имеет подходящий config/docs pattern.

Не кодировать marketing-формулировки провайдеров как вечные истины. Provider adapter обязан выставлять metadata
по актуально проверенным официальным условиям, а неизвестное состояние обрабатывается fail-closed.

Добавить request-level classification минимум:

- `generic` - запрос не требует передачи истории, профиля, питания, тренировок, прогресса, замеров или другого
  пользовательского контекста;
- `personalized` - запрос или tool context может содержать пользовательские данные.

Не пытаться определять sensitivity эвристикой по тексту prompt. Classification передаётся доверенным backend-кодом.
Без явной безопасной классификации authenticated AI Coach request должен трактоваться консервативно как `personalized`.

Добавить конфигурационный фундамент:

- `AI_COACH_ENABLED=false`;
- `AI_FREE_ONLY=true`;
- provider enabled flags;
- provider/model metadata, достаточные для free-only и privacy routing;
- конфигурируемый порядок providers без жёсткой зависимости от их количества.

`AI_FREE_ONLY=true` должен кодом запрещать:

- явно платную модель/route;
- route/model с неизвестной стоимостью;
- promotional/trial/free credits как production fallback, если бесплатность не является регулярно возобновляемой;
- auto-router, способный уйти в paid inference;
- paid fallback, autopurchase, auto top-up или автоматическое включение платного тарифа.

Для `personalized` request дополнительно запрещать provider/model, если текущая подтверждённая policy metadata не
разрешает такой класс данных или имеет неизвестный статус. Отсутствие подходящего provider должно давать
контролируемую недоступность, а не privacy downgrade.

Не реализовывать streaming в MVP. Нейтральный AI/domain code не должен импортировать типы Cloudflare,
OrcaRouter, OpenRouter или любых будущих provider adapters.

## Out of scope

Не делать HTTP-вызовы к конкретным провайдерам, failover/router, topic gate, tools, persistence или UI.
Не добавлять LangChain/LangGraph/CrewAI. Не добавлять Redis.
Не реализовывать отдельный NaraRouter/Pollinations adapter в этой задаче.

## Проверки

Unit tests минимум:

- DTO/serialization;
- provider registry;
- capabilities;
- disabled/unknown provider;
- feature flags;
- recurring-free route разрешён;
- paid/unknown-cost route запрещён;
- promo/trial/credits route запрещён при `AI_FREE_ONLY=true`;
- auto-paid fallback запрещён;
- `generic` и `personalized` policy checks;
- unknown data policy блокирует `personalized` request;
- отсутствие явной classification не ослабляет privacy;
- neutral error model.

## Done when

Есть стабильный нейтральный provider contract и тестируемые инварианты бесплатности и data sensitivity.
Приложение нормально запускается с AI disabled и без provider credentials. Нового provider можно добавить
адаптером и metadata без изменения domain layer.

## Рекомендуемый commit

`feat(ai): add provider core free-tier and data policy guards`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.
