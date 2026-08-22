# BotFather owner checklist - minimal manual actions

Этот checklist используется начиная с task `02`, после уже выполненных Telegram tasks `00` и `01`, и только после того, как Codex выполнил автоматические проверки и Bot API sync. Не повторять руками name/About/Description/avatar/commands/Menu Button, если automated sync уже успешен.

## После task 02

Codex сначала должен показать automated state через `getMe` и profile sync check.

Владелец делает только пункты, которые Codex пометил `OWNER_ACTION_REQUIRED`.

### Main Mini App

Если `getMe.has_main_web_app == false` или Main Mini App URL неверен:

```text
@BotFather
-> /mybots
-> @your_fitness_coach_bot
-> Bot Settings / Configure Mini App
-> Main Mini App
```

Установить canonical production HTTPS URL, подтверждённый кодом/config. Не использовать `?v=...`, preview URL, localhost, token или user-specific params.

После сохранения Codex повторно проверяет `getMe.has_main_web_app` и `https://t.me/your_fitness_coach_bot?startapp`.

### Web Login

Ничего не менять, если текущий Telegram browser login работает и task `00` не нашла реальный mismatch.

Если требуется изменение, Codex должен назвать конкретный missing/incorrect Allowed URL или redirect URI. Тогда владелец открывает BotFather Web Login и меняет только указанное значение.

Не менять proxy-tunnel, Client Secret или `/setdomain` наугад.

### Ненужные modes

Codex проверяет `getMe`. Владелец меняет BotFather только если соответствующий флаг неверен:

- `can_join_groups == true` -> отключить Groups;
- `can_read_all_group_messages == true` -> включить Group Privacy;
- `supports_inline_queries == true` -> отключить Inline Mode;
- `supports_guest_queries == true` -> отключить Guest Mode;
- `can_connect_to_business == true` -> отключить Secretary/Business mode;
- `has_topics_enabled == true` или `allows_users_to_create_topics == true` -> отключить Threaded Mode;
- `can_manage_bots == true` -> отключить Bot Management Mode.

Если флаг уже корректен - ничего не трогать.

### Origin protection

В Mini App settings проверить только одно: усиленная origin protection не должна быть отключена через opt-out.

## После main task 72

Только финальный visual/platform polish:

- Splash Screen из canonical YFC Light/Dark tokens;
- Main Mini App previews реального production UI;
- реальный mobile client smoke, если такой evidence ещё не был получен task `72` после последнего Telegram-related изменения.

## Никогда без отдельного решения

- token rotation/revoke;
- новый bot;
- username change;
- proxy/tunnel changes;
- новые Telegram modes;
- массовая рассылка.
