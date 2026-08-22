---
name: telegram-engineer
description: >
  Design, implement or review Telegram Bot API, Aiogram, Telegram Mini App, BotFather,
  commands, deep links, channel publishing, moderation and broadcasts. Use when Telegram
  platform behavior or integration contracts change. Do not use for ordinary responsive web
  work or generic notifications that have no Telegram-specific behavior.
---

# telegram-engineer

Работай с Telegram как с отдельной платформой, но не создавай отдельный продукт без необходимости.
Бот, Telegram Mini App и канал могут использовать общий backend и общие доменные сервисы, однако у
каждой поверхности есть собственные trust boundaries, ограничения и failure modes.

## Сначала

Перед изменением кода:

- прочитай корневой `AGENTS.md`, релевантные `docs/`, task и текущую конфигурацию;
- определи фактические версии Telegram Bot API, Aiogram и Mini App API;
- проверь текущий runtime, routers, Dispatcher, FSM storage, polling/webhook, jobs и tests;
- найди существующие auth/linking, notification, timezone, proxy и deep-link contracts;
- проверь, какой процесс владеет bot token и кто запускает polling/webhook;
- сверяй изменяемые Telegram API, лимиты и BotFather-процедуры с актуальной официальной
  документацией на момент реализации;
- не меняй token, production channel, BotFather или реальные права администратора без явного
  запроса владельца.

Не создавай второй bot runtime, token или дублирующую TMA только потому, что новая функция связана
с поддержкой, новостями или модерацией.

## Границы платформы

Разделяй минимум три поверхности:

1. **Личный чат с ботом** - команды, support/feedback, настройки, уведомления, moderation.
2. **Telegram Mini App** - общий Web-интерфейс внутри Telegram с отдельным platform adapter.
3. **Канал** - публикация только в заранее настроенные каналы с проверенными правами.

Bot API polling и browser Telegram OAuth/login - разные сетевые сценарии. Не объединяй их в
неявную proxy/TLS-конфигурацию и не ломай один поток ради другого.

## Bot runtime и Aiogram

- Один bot token имеет одного владельца long polling. Несколько polling-процессов для одного token
  недопустимы.
- Если требуется горизонтальное масштабирование, сначала проверь, оправдан ли webhook; не меняй
  transport без отдельной причины и migration plan.
- Делай `Dispatcher` корневым orchestration layer, а функции разделяй на небольшие `Router`.
- Не размещай доменную логику, SQL и внешние интеграции прямо в handlers.
- Используй явные dependencies/services и тестируемые adapters для Bot API.
- Startup metadata sync, health checks и registration должны быть идемпотентными и не создавать
  бесконечный restart loop при временной ошибке Telegram.
- Сохраняй существующие polling lock, retry/backoff, graceful shutdown и allowed-updates policy.
- Не удаляй legacy runtime до переноса функций, тестов и контролируемого отключения.

## Команды, меню и `/start`

Храни canonical command definitions в одном месте и переиспользуй их для:

- runtime `setMyCommands`;
- `/help`;
- BotFather owner checklist;
- tests.

Учитывай command scopes и language variants, но не считай видимость команды authorization boundary.
Backend всегда повторно проверяет роль и разрешение пользователя.

Для `/start` зафиксируй явный порядок payload handlers. Более специфичные и security-sensitive
payloads, например account linking, должны обрабатываться раньше generic menu handler.

Требования:

- неизвестный payload безопасно приводит к понятному состоянию, а не к raw error;
- unknown command не пересылается автоматически администратору;
- admin-only команды не попадают в default public scope;
- Mini App URL, privacy URL и public deep links берутся из общей проверенной конфигурации;
- menu button и команды не должны указывать на временный tunnel или staging в production.

## FSM и многошаговые сценарии

Для support, редактирования, moderation и других многошаговых потоков:

- зафиксируй состояния и допустимые переходы;
- поддержи `/cancel`, timeout/TTL и понятный restart policy;
- не считай in-memory FSM достаточным, если потеря состояния после restart нарушает критический
  сценарий;
- свободный текст вне активного flow не должен неожиданно становиться обращением или admin action;
- поддерживаемые media types должны иметь allowlist, ограничения и безопасный fallback;
- не загружай файл на сервер, если достаточно безопасного Bot API copy/forward contract;
- исключи cross-user state mix-up и повторное применение stale state.

## Telegram Mini App

TMA должна переиспользовать общий frontend, API, auth model и design system. Делай отдельный
platform adapter, а не второй frontend tree.

### Per-feature mobile/TMA gate

Для client-facing feature task Telegram review не откладывается до финальной TMA-hardening задачи.
Текущая task обязана расширить shared smoke и исправить созданную ею TMA regression в пределах scope.
Финальный hardening проверяет интеграцию целиком, но не является первым mobile pass.

Используй вместе с `$mobile-engineer` и `references/MOBILE_TMA_ACCEPTANCE_MATRIX.md`:

- `$mobile-engineer` отвечает за smartphone interaction, keyboard, safe area, lifecycle, touch и performance;
- `$telegram-engineer` отвечает за Telegram API, initData trust boundary, BackButton, deep links и client compatibility.

Обязательно:

- передавай на backend только raw `initData` и валидируй подпись, freshness и bot binding на
  доверенной стороне;
- не доверяй `initDataUnsafe`, query params, frontend `user_id` или `language_code` как identity;
- не отправляй raw `initData` в logs, analytics, errors или third-party telemetry;
- сохраняй auth/account-linking invariants и не заставляй valid TMA launch проходить browser login;
- учитывай `isActive`, `BackButton`, theme changes, `viewportHeight`/`viewportStableHeight`, keyboard, `safeAreaInset` и `contentSafeAreaInset`;
- обрабатывай применимые `viewportChanged`, `safeAreaChanged` и `contentSafeAreaChanged` без сброса route/form/dialog state;
- проверяй unsupported/older client behavior и graceful degradation;
- не используй Telegram theme colors как единственный источник контраста или semantic meaning;
- при смене Web/TMA context не теряй незавершённое пользовательское состояние без причины;
- deep links должны открывать разрешённый внутренний контекст, а не arbitrary URL/path.

## Callback queries и admin actions

Каждый security-sensitive callback связывай минимум с:

- actor;
- resource/draft/user scope;
- immutable revision/version;
- конкретным action;
- сроком действия или stale-state check, если это нужно.

Проверяй всё server-side. Callback data - недоверенный ввод.

Actions должны быть идемпотентными. Повторный callback, Telegram retry или двойное нажатие не должны
создавать двойную публикацию, ответ, подписку или изменение. Stale callback должен объяснять, что
revision уже заменена, а не применять действие к новому состоянию.

## Канал, moderation и публикация

- Channel id/username берётся только из server-side allowlist/configuration.
- Не принимай arbitrary chat id из callback, command или frontend.
- Проверяй membership и минимально необходимые admin rights до публикации.
- Не выдавай отсутствие прав за transient retry навсегда.
- Generated content не публикуется автоматически, если task требует owner moderation.
- Approval привязывается к точной immutable revision и exact media hash.
- Regeneration создаёт новую revision и отменяет старое approval.
- Retry публикует только ранее approved revision, а не самый новый draft.
- Храни idempotency key, итоговый content hash, channel id, message id и audit metadata.
- Форматируй через безопасные entities/HTML; не вставляй недоверенный HTML без escaping.
- Текущие text/caption/media limits проверяй по используемой версии Bot API, не по памяти.
- Если content не помещается, используй заранее определённую concise/text-only strategy. Не дроби
  один пост в неожиданную серию сообщений.
- Изображение является optional: provider failure не должен блокировать весь editorial flow.

## Рассылки и anti-spam

- News/marketing digest выключен по умолчанию и требует явного opt-in.
- Product notifications и optional digest имеют разные preferences.
- Отписка должна быть мгновенной, идемпотентной и без обязательного подтверждения.
- Перепроверяй subscription непосредственно перед send, включая queued delivery.
- Используй bounded rate ниже актуального бесплатного лимита, обрабатывай `429` и `retry_after`.
- Ограничивай retries и provider attempts; blocked/deactivated chat отключает будущую optional
  доставку по зафиксированной policy.
- Никогда не включай подписку повторно молча.
- Bots не могут рассчитывать на доставку пользователю, который не начал взаимодействие с ботом;
  проектируй opt-in flow соответственно.

## Security и privacy

Не логируй и не включай в ошибки:

- bot tokens и provider secrets;
- raw TMA `initData`;
- тексты private support requests;
- subscriber lists;
- admin/member lists;
- документы и фотографии пользователя;
- лишние Telegram/user identifiers.

Дополнительно:

- admin ids хранятся в безопасной server-side конфигурации;
- role visibility в Telegram UI не заменяет authorization;
- external source fetch должен быть SSRF-safe и ограничен по redirect, DNS, content type, size и
  timeout;
- временные media/source artifacts имеют retention и cleanup;
- не ослабляй TLS verification;
- не раскрывай raw Telegram/API errors пользователю.

Для security-sensitive потока используй также `$security-engineer` и `$privacy-engineer`.

## Проверки

Выбирай уровень проверки по риску:

- чистые handler/service unit tests;
- routing tests через `Dispatcher` без реального polling;
- mocked/fake Bot API adapter;
- persistence/integration tests для FSM, jobs, subscriptions и idempotency;
- Web/TMA browser tests для platform adapter;
- reusable TMA mock с version/platform/theme/viewport/safe-area/BackButton events;
- реальные Telegram Android и iOS smoke отдельно от mock, Telegram Desktop дополнительно;
- opt-in manual smoke с test bot/channel только при явной конфигурации;
- production owner checklist без автоматического изменения BotFather/channel.

Для TMA-проверок прочитай `references/MOBILE_TMA_ACCEPTANCE_MATRIX.md` и используй только применимые разделы. Для Bot/channel flow следуй матрице рисков этой task и существующим bot tests.

## Совместная работа с другими skills

- `$backend-engineer` - API, services, transactions и integrations;
- `$frontend-engineer` - общий Web/TMA UI;
- `$localization-engineer` - locale preference и localized bot product messages;
- `$evidence-content-editor` - новости, дайджесты и editorial revisions;
- `$llm-engineer` - provider-neutral generation, если Telegram использует LLM;
- `$platform-engineer` - runtime, jobs, secrets и deployment;
- `$observability-engineer` - safe metrics, stuck jobs и outage diagnosis;
- `$qa-engineer` - regression strategy.

Не используй `$mobile-engineer` вместо этого skill только потому, что Telegram открыт на телефоне. Для client-facing TMA flow обычно нужны оба: `$mobile-engineer` закрывает smartphone UX/runtime, `$telegram-engineer` - Telegram-specific API и trust boundaries.

## Финальный отчёт

Укажи:

- какие Telegram surfaces изменены;
- сохранён ли один polling/webhook owner;
- какие commands/deep links/auth contracts затронуты;
- какие BotFather/channel действия остаются ручными;
- какие tests и smoke checks реально выполнены;
- ограничения, rate-limit и deployment implications.
