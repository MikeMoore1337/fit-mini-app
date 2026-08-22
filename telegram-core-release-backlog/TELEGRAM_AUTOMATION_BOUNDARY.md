# Telegram automation boundary

Актуальность контракта: 22 августа 2026 года. Пакет применяется начиная с Telegram task `02`; tasks `00` и `01` уже выполнены и не переисполняются.

Этот файл определяет, что Codex должен делать автоматически, а что оставлять владельцу.

## A. Автоматизировать через Bot API

При наличии действующего `TELEGRAM_BOT_TOKEN`, сети и exact `getMe.username == "your_fitness_coach_bot"` Codex должен уметь безопасно синхронизировать:

```text
setMyName
setMyShortDescription
setMyDescription
setMyProfilePhoto
setMyCommands
setChatMenuButton
```

И проверять результат через соответствующие read methods и `getMe`.

Все write-операции:

- idempotent;
- используют canonical source в коде;
- не логируют token;
- сначала проверяют identity;
- не выполняются против другого bot username;
- имеют check/dry-run режим;
- возвращают per-field результат;
- не должны провоцировать restart loop при Telegram outage.

## B. Диагностировать автоматически, менять владельцу

`getMe` позволяет автоматически проверить среди прочего:

```text
can_join_groups
can_read_all_group_messages
supports_guest_queries
supports_inline_queries
can_connect_to_business
has_main_web_app
has_topics_enabled
allows_users_to_create_topics
can_manage_bots
```

Если флаг противоречит YFC contract, Codex формирует ровно одно конкретное действие владельца в BotFather вместо общего "проверьте настройки".

## C. Owner-only BotFather actions

Оставлять владельцу только реально необходимые действия, включая где применимо:

- включить/изменить Main Mini App и canonical production URL;
- Web Login Allowed URLs / Client ID / Client Secret, только если текущий auth contract действительно требует изменения;
- splash/loading screen;
- Main Mini App previews;
- отключить Groups/Privacy/Inline/Guest/Threaded/Business/Management modes, если automated `getMe` verification показывает mismatch;
- проверить, что Mini App origin protection не отключена.

Не просить владельца менять поле, если Bot API может сделать это безопасно сам.

## D. Никогда автоматически

Без отдельного явного решения владельца не выполнять:

- `/token`, revoke/rotation;
- создание нового public bot;
- смену username;
- изменение login proxy-tunnel;
- отключение TLS verification;
- production deploy;
- массовую рассылку;
- включение Telegram modes "на будущее";
- доступ Codex к личной Telegram Web-сессии владельца ради кликов в BotFather.

## E. Official references

Перед реализацией Codex обязан точечно перепроверить актуальные official Telegram docs, если API/интерфейс мог измениться:

- `https://core.telegram.org/bots/api`
- `https://core.telegram.org/bots/features`
- `https://core.telegram.org/bots/webapps`
- `https://core.telegram.org/api/bots/webapps`
- `https://core.telegram.org/api/links`
- `https://core.telegram.org/bots/telegram-login`

Не использовать сторонние статьи как source of truth для BotFather/Bot API contract.
