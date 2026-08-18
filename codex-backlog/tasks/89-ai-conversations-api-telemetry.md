# TASK 89. AI conversations, API, privacy-aware telemetry и abuse protection

- Фаза: **AI product backend**
- Приоритет: **89/93**
- Зависит от: `60`, `81`, `82`, `83`, `84`, `85`, `86`, `87`, `88`
- Рекомендуемый reasoning: **High**

## Цель

Добавить persistence и backend API общего для Web/Telegram диалога, измеримость бесплатной multi-provider
цепочки и защиту общей квоты от злоупотребления, не превращая operational telemetry в копию приватной
conversation/tool history.

## In scope

Сначала переиспользовать существующие chat/message tables, если подходят. Иначе минимально создать
`ai_conversations`, `ai_messages`, `ai_usage`/эквиваленты через безопасные Alembic migrations.

История для LLM ограничена последними N сообщениями и configurable character/token budget.
Conversation summary можно предусмотреть архитектурно, но не усложнять MVP.

API в стиле проекта, ориентировочно:
`POST /ai/chat`, `GET /ai/conversations`, `GET /ai/conversations/{id}`,
`DELETE ...`, `GET /ai/status`.

Требования:

- auth/RBAC и cross-user isolation;
- input size limits;
- feature flags;
- provider errors/stack traces не раскрываются;
- status не раскрывает keys/internal infra и не обещает конкретный provider пользователю;
- общий chat для одного пользователя Web/Telegram;
- configurable per-user minute/hour/day limits и global concurrent request limit с использованием
  существующего limiter, если он есть;
- один пользователь не должен легко исчерпать общую бесплатную квоту параллельными запросами;
- provider-specific quotas/limits не хардкодить в API contract - использовать config/telemetry там, где нужно;
- `AI_FREE_ONLY` и privacy routing из tasks `77`/`81` являются обязательными backend guards, а не UI convention.

### Request data classification

Каждый LLM execution должен иметь neutral `request_data_class`/эквивалент (`generic` или `personalized`) из
provider core.

Authenticated AI Coach conversation считать `personalized` по умолчанию, если доверенный backend path явно
не доказал, что во внешний LLM не передаются user-specific history/profile/tool data.

Вызовы tools или добавление в model context данных питания, тренировок, прогресса, антропометрии, памяти,
профиля, клиента тренера или истории диалога не должны незаметно оставаться `generic`.

API/UI не позволяют пользователю вручную помечать чувствительный запрос как менее чувствительный для обхода
provider policy.

### Telemetry

Telemetry хранит, где доступно и уместно:

- request_id/conversation_id/user-scoped correlation без раскрытия лишних PII;
- provider;
- configured_model/route;
- actual_model, если provider его сообщает;
- request_type;
- `request_data_class`;
- provider free-tier classification;
- provider data-policy classification/version marker, если такой marker предусмотрен task `77`;
- token metrics nullable;
- Cloudflare-specific units отдельно;
- latency;
- число tool calls без raw tool payloads;
- provider attempts/failovers/skips;
- internal skip/failure reason codes;
- status/error class;
- timestamps.

Provider attempt telemetry минимум:
`request_id/provider/model/attempt/status/error/is_failover/skip_reason` плюс free-tier/data-policy fields,
если они реализованы в neutral contract.

Не логировать full prompts/answers в обычные application logs.
Не писать raw tool arguments/results в operational telemetry: они могут содержать питание, вес, замеры,
тренировки и другие пользовательские данные. Message/tool history хранить только там, где она действительно
нужна продукту и защищена теми же lifecycle/access rules.

Не выдумывать token counts или provider policy values, если API/metadata их не даёт.

### Abuse protection

Rate/concurrency controls должны учитывать, что бесплатные provider limits динамичны и могут отличаться.
Не пытаться синхронно "добивать" один user request десятками failover/retry attempts.
Количество provider attempts на один request ограничить и сделать наблюдаемым.

При исчерпании всех recurring-free или privacy-compatible candidates вернуть контролируемую временную
недоступность. Не предлагать приложению автоматически купить credits или включить paid inference.

## Out of scope

Не делать UI, streaming, write actions или платный routing.
Не добавлять raw prompt/response analytics.
Не создавать отдельное хранилище копий tool payloads только ради диагностики.
Не выдумывать token counts, если provider их не возвращает.

## Проверки

Migration/API tests минимум:

- auth/create/continue/history/delete/status;
- invalid conversation;
- cross-user isolation;
- AI disabled;
- all providers unavailable;
- mocked Cloudflare -> OrcaRouter -> OpenRouter failover;
- personalized request не отправляется privacy-incompatible candidate;
- no privacy downgrade when only generic-safe provider remains;
- oversized input;
- rate limiting/concurrency;
- max provider attempts;
- usage/attempt/skip telemetry;
- `request_data_class` telemetry;
- отсутствие raw prompt/answer/tool payloads в operational logs/telemetry;
- secret/error redaction.

## Done when

История сохраняется и общая для Web/Telegram текущего пользователя, API защищён, routing sensitivity проходит
сквозь backend до provider router, а эксплуатационные метрики достаточны для оценки бесплатных лимитов,
доступности и будущей стоимости без утечки приватного содержимого.

## Рекомендуемый commit

`feat(ai): add conversations api privacy telemetry and limits`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task.
После изменений запускать только профильные проверки согласно `AGENTS.md`, проверить diff и создать один
логический commit, если task меняет tracked files. В финальном отчёте перечислить:
изменения, ключевые файлы, миграции, реально запущенные проверки, ограничения и commit hash.

## Backlog v3 conversation and memory separation

Conversation history != durable memory task `87`. Web/TMA share account history. Product analytics never gets raw conversation text.

## Final release integration: export/delete

Conversation history:

- включить в user export в machine-readable form;
- account deletion удаляет conversation data по current lifecycle policy;
- ordinary product analytics не получает raw text.
