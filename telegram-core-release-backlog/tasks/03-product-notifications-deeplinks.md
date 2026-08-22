# TASK 03. Доставка продуктовых уведомлений и deep links через основной бот

- Фаза: **Notifications / Bot integration**
- Зависит от: Telegram `02` и завершённой main task `64`
- Запускать до main task `64`: **нет**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$backend-engineer`, `$python-engineer`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$qa-engineer`, `$code-reviewer`
- Условные skills: `$solution-architect` при конфликте с main `64`; `$data-engineer` при изменении persistence; `$observability-engineer` при изменении telemetry pipeline; `$accessibility-engineer` при новых пользовательских bot controls
- Основная роль: **`implementer`**
- Контракт роли: `.agents/roles/implementer.md`

## Статус предыдущих Telegram tasks

Telegram `00` и `01` были выполнены до этого пакета, Telegram `02` должна быть выполнена перед запуском `03`. Не переисполнять `00/01` и не перестраивать single-bot/support architecture без доказанного blocker для notification adapter.


## Цель

Подключить `@your_fitness_coach_bot` как delivery adapter уже существующей canonical notification architecture main task `64`, не создавая второй scheduler/model/preferences store.

## 1. Сначала прочитать результат main 64

Не проектировать notification semantics заново.

Из main `64` переиспользовать:

- canonical event model;
- category identifiers;
- preferences;
- quiet hours;
- timezone/DST semantics;
- dedupe/idempotency keys;
- scheduler/background jobs;
- destination/deep-link contract;
- observability expectations.

Если фактическая main `64` отличается от ожидаемого task текста, current code/docs после main `64` являются source of truth.

## 2. Telegram delivery adapter

Telegram task владеет только:

- serialization message/button;
- target linked Telegram user;
- Telegram send/copy API handling;
- platform rate limit;
- retry classification;
- blocked/deleted chat behavior;
- Telegram-specific delivery status;
- bot-facing deep-link/button representation.

Не создавать:

- второй scheduler;
- второй preferences store;
- второй token/process;
- отдельную notification entity только для Telegram.

## 3. Категории

Покрыть только категории, реально созданные main `64`, включая где применимо:

- workout reminder;
- trainer comment;
- program changed/assigned;
- weekly review/check-in reminder;
- measurement reminder;
- invitation/relationship event;
- account/security transactional event, если Telegram разрешён для него.

Не добавлять marketing/news/digest.

## 4. Deep links

Переиспользовать canonical route/destination builder main `64`.

Bot adapter должен выбирать Telegram representation без дублирования business route logic.

Правила:

- внутренний destination allowlist;
- stale/deleted/revoked target -> graceful fallback;
- wrong account/ownership -> safe fallback;
- Web/TMA aware;
- support `/start` payloads и notification destinations не конфликтуют;
- `link_<token>` priority не меняется.

Если Main Mini App настроен (`getMe.has_main_web_app == true`) и canonical contract использует `startapp`, разрешён официальный формат:

```text
https://t.me/your_fitness_coach_bot?startapp=<safe-start-param>
```

Если Main Mini App ещё не настроен или конкретный route не поддерживает `start_param`, использовать текущий safe WebAppInfo/Web URL fallback из product contract, а не придумывать второй роутер.

## 5. Delivery semantics

- linked user only;
- category preferences;
- quiet hours;
- timezone/DST;
- dedupe;
- cancelled/rescheduled reminder invalidation;
- bounded retry/backoff;
- 429 `retry_after` respected;
- blocked/deleted chat не ретраится бесконечно;
- stale events не оживают после retry;
- duplicate worker не создаёт duplicate delivery.

## 6. Privacy

На lock screen/message preview не раскрывать лишние sensitive details.

Operational logs:

- event/category/status IDs допустимы только в безопасной форме;
- no message body;
- no raw `initData`;
- no token;
- no feedback text;
- no unnecessary Telegram username/chat ID.

## 7. `/settings` public UX update

Если main `64` действительно реализовала notification preferences:

обновить canonical command description через profile sync helper task `02`:

```text
settings - Настройки и уведомления
```

Не просить владельца делать это в BotFather вручную.

`/settings` ведёт в существующий canonical settings/preference UX и сохраняет timezone access.

Если notification settings не существуют вопреки prerequisite, не симулировать их - это blocker main `64` contract.

## 8. Bot API/profile compatibility

После integration запустить task `02` profile sync `check` и применить только ожидаемый bounded diff, если среда позволяет.

Не менять About/Description для рекламирования notifications, если это не нужно продукту.

## Проверки

Минимум:

- each implemented category enabled/disabled;
- quiet hours;
- timezone/DST;
- stale/cancelled/rescheduled event;
- dedupe/duplicate worker;
- blocked/deleted user;
- 429/retry_after;
- transient Telegram outage;
- wrong/unlinked account;
- revoked trainer/relationship;
- deep link exact target;
- stale target fallback;
- Main Mini App available/unavailable representation;
- support/link payload regression;
- one polling owner;
- profile sync only updates expected `/settings` description;
- no sensitive logs.

После implementation обязателен independent review и QA pass.

## Done when

Product notifications приходят через тот же bot, используют canonical main `64` preferences/scheduling и предсказуемо открывают безопасный target.

## Процесс

Полный task lifecycle.

Не deploy. Не переходить к task `04`.

После этой task продолжить основной backlog и дождаться main task `72` перед final Telegram gate.
