# TASK 04. Финальная E2E-проверка Telegram core с минимальным owner checkpoint

- Фаза: **Release gate**
- Зависит от: Telegram `03` и завершённой main task `72`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$qa-engineer`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$accessibility-engineer`, `$release-manager`, `$code-reviewer`, `$technical-writer`
- Условные skills: `$observability-engineer` только при release blocker в telemetry/logging
- Основная роль: **`integration-release`**
- Контракт роли: `.agents/roles/integration-release.md`

## Статус предыдущих Telegram tasks

Telegram `00` и `01` являются уже выполненной историей и не входят в пакет. Release gate проверяет их фактический текущий результат как regression surface, но не переисполняет эти задачи и не создаёт им новые commits/reports.


## Цель

Сделать один финальный Telegram release gate после TMA hardening main task `72`, максимально автоматизировав проверку remote bot state и не заставляя владельца повторять проверки, которые Codex может доказать сам.

## 1. Не повторять main 72 без причины

Сначала прочитать фактический результат main task `72`.

Если после main `72` уже есть свежий real Telegram Android/iOS evidence и после него не менялся соответствующий TMA/platform code:

- переиспользовать evidence;
- не просить владельца повторять те же ручные действия.

Если Telegram-related code изменился после этого evidence, повторить только затронутый smoke.

## 2. Automated remote bot state gate

При доступном `TELEGRAM_BOT_TOKEN` выполнить безопасный read-only remote check:

- `getMe` exact username;
- public bot flags;
- `getMyName`;
- `getMyShortDescription`;
- `getMyDescription`;
- `getMyCommands` нужного scope/language;
- `getChatMenuButton` default;
- `has_main_web_app`;
- profile photo verification, если текущий client/API позволяет надёжный read-back;
- profile sync `check` task `02` должен давать zero unexpected diff.

Release target flags:

```text
username == your_fitness_coach_bot
can_join_groups == false
can_read_all_group_messages != true
supports_guest_queries != true
supports_inline_queries != true
can_connect_to_business != true
has_main_web_app == true
has_topics_enabled != true
allows_users_to_create_topics != true
can_manage_bots != true
```

Optional missing fields не интерпретировать как true.

Если token/network недоступен, не выдумывать remote verification. Пометить exact limitation.

## 3. Runtime/E2E matrix

### Identity/auth

- `/start` fresh;
- `/start link_<token>` valid/expired/conflict;
- unknown start payload;
- signed TMA `initData`;
- browser Telegram login/Web Login;
- existing proxy-tunnel/TLS;
- Web/TMA identity continuity.

### Entry/UI

- `/app`;
- inline Open App;
- default Menu Button;
- Main Mini App profile launch;
- `https://t.me/your_fitness_coach_bot?startapp`;
- canonical URL without accidental `?v=...` public contract;
- YFC light/dark;
- mobile labels/accessibility;
- return/back behavior from main `72`.

### Support

- `/support`;
- `/feedback`;
- all support deep links;
- categories;
- `/cancel`;
- TTL/restart reset;
- unsupported media;
- rate limit;
- recipient permission;
- forged reply rejection;
- reply delivery;
- blocked user;
- no cross-user mix-up.

### Notifications

Для каждой фактической main `64` category:

- enabled/disabled;
- quiet hours;
- timezone/DST;
- dedupe;
- stale/rescheduled/cancelled;
- wrong/unlinked user;
- blocked/deleted chat;
- Telegram 429/transient failure;
- deep-link target/fallback.

### Architecture/security/privacy

- один public token contract;
- один polling owner;
- no legacy support service in steady-state repository/deploy config;
- no support token required;
- no news/channel/digest handlers/commands;
- no token/raw initData/support message body в logs;
- origin protection не должна быть knowingly disabled;
- Web Login/proxy contract unchanged unless explicitly required.

## 4. Maximum-autonomy owner checkpoint

Сначала выполнить все automated checks.

После них сформировать `OWNER_ACTION_REQUIRED` только для фактических owner-only gaps.

Допустимые примеры:

### Main Mini App отсутствует

Если `getMe.has_main_web_app == false`:

- дать exact BotFather path;
- дать exact canonical URL из current config;
- после действия владельца Codex повторяет `getMe` и startapp check.

### Ненужный mode включён

Если `getMe` показывает неправильный флаг:

- назвать только конкретный mode;
- владелец выключает его в BotFather;
- Codex повторно проверяет `getMe`.

### Web Login mismatch

Просить владельца открыть Web Login только если automated/live auth evidence показывает реальный mismatch, который нельзя исправить в коде.

Нельзя писать владельцу общий checklist из десяти пунктов, если девять уже доказаны автоматически.

## 5. Splash/previews

После main `72` они являются owner-only visual polish.

Codex должен подготовить точные assets/тексты/источники из canonical design system, но не требовать от владельца переделывать Bot API-manageable profile fields.

Если splash/previews не являются release blocker по current release contract, отметить их как optional owner polish, а не блокировать core bot readiness.

## 6. Live message safety

Автоматические live sends допускаются только:

- в явно configured owner/test chat;
- без sensitive content;
- в минимальном количестве;
- если current task/environment уже содержит approved test recipient.

Не отправлять тестовые сообщения реальным пользователям случайным образом.

При отсутствии безопасного live recipient использовать mocks/integration harness и reuse main `72` real-client evidence.

## Output

Финальный release report должен разделять:

```text
AUTOMATED_VERIFIED
REAL_CLIENT_VERIFIED
MOCK_VERIFIED
OWNER_ACTION_REQUIRED
OPTIONAL_OWNER_POLISH
NOT_VERIFIED / LIMITATION
```

Также указать:

- checks actually run;
- remote Bot API read-back;
- config/migration state;
- review/QA findings;
- exact remaining owner actions;
- commit hash или `no commit`.

## Done when

- один bot безопасно открывает приложение, поддерживает пользователей и доставляет product notifications;
- automated profile check не имеет unexpected diff;
- Main Mini App подтверждён;
- auth/proxy/TMA contracts не сломаны;
- owner actions сведены только к реально неавтоматизируемым Telegram surfaces;
- нет критических Telegram release blockers.

## Процесс

Полный task lifecycle.

Не deploy и не rotate token.

Это последняя task Telegram core backlog.
