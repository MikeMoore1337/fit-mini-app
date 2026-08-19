# TASK 59A. Единый Telegram-бот: понятная навигация, помощь и обратная связь

- Фаза: **Platform / Telegram / Feedback**
- Порядок выполнения: **после task `59` и до task `60`**
- Зависит от: `07`, `13`, `47`, `59`
- Не изменяет и не переигрывает выполненные tasks `00-47`
- Downstream dependency: task `72` должна учитывать результат `59A`; task `73` должна использовать реальную ссылку на основной бот
- Обязательный инвариант: сохранить существующий Telegram login proxy-tunnel и результат `46C.6`, если он уже выполнен
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$backend-engineer`, `$security-engineer`, `$qa-engineer`, `$product-designer`, `$devops-engineer`, `$technical-writer`

## Зафиксированное решение владельца

Использовать только основной публичный бот:

```text
@your_fitness_coach_bot
```

Он продолжает использовать существующий:

```text
TELEGRAM_BOT_TOKEN
```

Отдельный `support-bot`, отдельный `SUPPORT_BOT_TOKEN` и отдельный polling process в целевой архитектуре не нужны.

Обратная связь должна быть встроена в основной бот, который уже:

- открывает Telegram Mini App;
- обрабатывает `/start` и account linking;
- позволяет выбрать часовой пояс;
- отправляет продуктовые уведомления;
- использует существующую защиту от параллельного polling.

Не создавать новый Telegram-бот и не запрашивать новый токен в BotFather.

## Почему это отдельная задача

Task `59` унифицирует уведомления и сначала должен определить итоговую bot/notification infrastructure. Сразу после него нужен отдельный ограниченный task, который:

- превращает основной Telegram-бот в понятную точку входа в продукт;
- добавляет человеческий канал обратной связи;
- переносит полезную relay-логику из текущего отдельного support runtime в основной бот;
- удаляет постоянную двухботовую архитектуру;
- не расширяет notification task до generic messenger, CRM или helpdesk.

Task `72` должен проводить финальную TMA-интеграцию уже с готовыми bot commands и support deep links, а не впервые проектировать bot logic.

## Текущий контекст, который нужно подтвердить

Текущий код, Git history, текущая feature-ветка и актуальный `docs/` являются source of truth.

На момент подготовки задачи в репозитории присутствуют как минимум:

- основной runtime `bot/fitminiapp_bot/bot.py`;
- отдельный `bot/fitminiapp_bot/support_bot.py`;
- отдельный `bot/fitminiapp_bot/support_config.py`;
- отдельный сервис `support-bot` в `docker-compose.yml`;
- переменные `SUPPORT_BOT_TOKEN`, `SUPPORT_ADMIN_TELEGRAM_USER_IDS`, `SUPPORT_BOT_ENABLED` в config/env contract;
- tests для отдельного support runtime.

Перед изменениями точечно проверить фактическое состояние этих файлов и связанные изменения task `59`.

Не проводить повторный полный аудит репозитория.

## Цель

Оставить один публичный Telegram-бот Your Fitness Coach с понятным контрактом:

```text
@your_fitness_coach_bot
  ├─ открыть приложение
  ├─ получить уведомления
  ├─ настроить часовой пояс
  ├─ получить справку
  └─ сообщить об ошибке, предложить улучшение или связаться с разработчиком
```

Пользователь должен сразу понимать, что делать, не угадывать команды и не искать отдельный аккаунт поддержки.

## Продуктовые границы

Обратная связь предназначена для:

- сообщения об ошибке;
- проблемы со входом, аккаунтом или привязкой Telegram;
- вопроса о заявке тренера, если автоматический статус и причина решения не помогли;
- предложения по улучшению;
- связи с владельцем/разработчиком проекта;
- другого нестандартного вопроса, который не закрывается интерфейсом приложения.

Этот канал не является:

- trainer-client messenger;
- общим чатом внутри приложения;
- заменой AI Coach;
- автоматической модерацией заявки тренера;
- медицинской, экстренной или круглосуточной помощью;
- тикет-системой, CRM или операторской панелью;
- способом отправить пароль, код подтверждения, токен, платёжные данные или лишние документы.

Не обещать SLA, время ответа, статус `оператор онлайн` или обязательный ответ на каждое обращение.

## 1. Один bot runtime

### Целевая архитектура

Встроить feedback handlers в основной bot runtime, использующий `TELEGRAM_BOT_TOKEN`.

Предпочтительно вынести функциональность в отдельный модуль/router, например:

```text
bot/fitminiapp_bot/feedback.py
```

или в эквивалентное место, соответствующее фактической архитектуре.

Не добавлять всю логику в один растущий `bot.py`, если её можно изолировать без широкого рефакторинга.

После миграции:

- основной bot process остаётся единственным владельцем polling для `TELEGRAM_BOT_TOKEN`;
- account linking, timezone, Mini App launch, notifications и feedback работают через один `Bot`/`Dispatcher` lifecycle;
- используется существующий polling lock/conflict protection;
- отдельный `support-bot` service удалён из steady-state `docker-compose.yml`;
- отдельный `support_bot.py` entrypoint и `support_config.py` удалены после переноса нужной логики;
- отдельные support-token settings удалены из `.env.example`, deploy docs и runtime config;
- tests перенесены на единый runtime и расширены.

### Production migration boundary

Task не выполняет production deploy и не перевыпускает токены.

Перед удалением legacy support runtime проверить, использовался ли он фактически в production. Если отдельный support-бот уже был опубликован пользователям, подготовить короткий owner-controlled переход:

1. в старом боте оставить только сообщение о переносе;
2. добавить кнопку/deep link на `@your_fitness_coach_bot?start=support`;
3. после подтверждения владельца отключить старый service;
4. не принимать новые обращения параллельно в двух ботах дольше переходного периода;
5. не удалять и не перевыпускать старый токен автоматически.

Целевая архитектура всё равно остаётся одноботовой.

## 2. Критические инварианты

Нельзя сломать или перепроектировать без отдельного подтверждения:

- `/start link_<token>`;
- текущую привязку Telegram к существующему account;
- защиту от linking conflict и просроченного token;
- signed Telegram Mini App `initData` auth;
- browser Telegram login/OAuth contract;
- существующий Telegram login proxy-tunnel;
- `TELEGRAM_OAUTH_PROXY_URL` или фактический эквивалент;
- TLS verification;
- notification delivery/deep links task `59`;
- timezone selection и legacy `/timezone`;
- polling lock, retry/backoff и обработку Telegram polling conflicts;
- один internal account для Web и Telegram;
- Demo/security boundaries;
- запрет на secrets, tokens, raw `initData` и приватный текст в логах.

Bot API polling и Telegram browser login/OAuth являются разными сетевыми сценариями. Не объединять их в неявный общий proxy contract и не обходить существующий auth tunnel прямыми запросами.

## 3. Канонический набор команд

Команды должны быть короткими, предсказуемыми и иметь ясные русские описания.

Публичный список для private chats:

```text
start - Главное меню
app - Открыть приложение
support - Помощь и обратная связь
settings - Настройки и часовой пояс
help - Возможности и команды
privacy - Политика конфиденциальности
```

Поддержать, но не обязательно показывать в основном command list:

```text
cancel - Отменить текущее действие
feedback - alias для /support
```

Legacy compatibility:

```text
timezone - оставить рабочим alias, если команда уже использовалась
```

Требования:

- одна каноническая константа/структура команд в коде;
- idempotent регистрация через `setMyCommands` при startup/setup;
- scope только для private chats, если бот не предназначен для групп;
- русские descriptions;
- `/help` и BotFather checklist используют тот же список;
- не показывать служебную `/id` пользователям;
- admin-only utility commands не входят в default scope;
- неизвестная команда не пересылается разработчику;
- ошибка синхронизации metadata/commands логируется безопасно и не создаёт бесконечный restart loop;
- runtime command setup является source of truth, BotFather используется для первоначальной настройки, проверки и аварийного fallback.

## 4. Главное меню и открытие приложения

### Обычный `/start`

Обычный `/start` без payload показывает короткое сообщение и inline keyboard:

```text
Your Fitness Coach

Откройте приложение или выберите нужное действие.

[Открыть приложение]
[Помощь и обратная связь]
[Настройки]
[Что умеет бот]
```

Текст можно адаптировать к текущему plain-language UX, но нельзя перегружать длинной рекламой.

### Приоритет обработки `/start`

Обработчики должны различать payload строго и в безопасном порядке:

1. существующий `link_<token>`;
2. `support` и support category payload;
3. другие существующие canonical payload;
4. неизвестный payload приводит в главное меню без raw error.

Канонические deep-link payload:

```text
support
support_bug
support_account
support_idea
support_contact
```

Они должны удовлетворять ограничениям Telegram deep linking и не конфликтовать с `link_<token>`.

### `/app`

Команда `/app` и primary inline button открывают текущий Mini App HTTPS URL.

Требования:

- URL берётся из единого current config/helper;
- production canonical URL не дублируется в нескольких модулях;
- не использовать временную version query в BotFather Main Mini App URL;
- текущий ожидаемый production URL проверить по config, ориентир:

```text
https://app.your-fitness-coach.ru/app
```

### Menu button

Сохранить быстрый product entry:

```text
Открыть приложение
```

Menu button может оставаться `MenuButtonWebApp`, если это текущий согласованный продуктовый контракт. Команды при этом должны быть доступны через `/`, profile shortcuts, `/help` и явные inline actions в `/start`.

Не менять menu button на другой режим только ради рефакторинга. Если выбран другой режим, доказать, что Mini App не стал менее доступен.

## 5. Сценарий обратной связи

### Вход

Команда `/support`, alias `/feedback`, кнопка главного меню или deep link открывает:

```text
Помощь и обратная связь

Выберите тему:

[Сообщить об ошибке]
[Проблема со входом или аккаунтом]
[Предложить улучшение]
[Связаться с разработчиком]
[Назад]
```

### Граница с AI Coach

Этот task не вызывает LLM и не делает AI-routing.

После включения AI Coach в tasks `76-91` можно добавить отдельный entry point для вопросов о тренировках, питании и функциях приложения. Человеческий канал должен остаться доступным для ошибок, account problems, жалоб, предложений и прямой связи.

До фактического production enable AI Coach не показывать неработающую кнопку и не обещать AI-функцию.

### Сбор сообщения

После выбора темы бот пишет:

```text
Опишите ситуацию одним сообщением. Можно приложить скриншот или файл.

Не отправляйте пароли, коды подтверждения, токены, платёжные данные
или документы с лишними персональными сведениями.

Для отмены используйте /cancel.
```

Поддержать безопасный набор message types без скачивания вложений на сервер:

- text;
- photo с caption;
- document;
- video;
- voice/audio только если `copy_message` и tests покрывают сценарий;
- media group только при корректной дедупликации и понятной доставке.

Unsupported content получает понятный ответ, а не silent drop.

### Поведение вне активного flow

Свободный текст вне явно открытого support flow не должен автоматически пересылаться разработчику.

Ответ:

```text
Выберите действие в меню. Чтобы написать разработчику, используйте /support.
```

Это предотвращает случайную пересылку личного сообщения.

### Состояние flow

- использовать короткоживущее FSM/state с явной отменой;
- состояние имеет TTL или безопасный reset;
- потеря state при restart не приводит к пересылке произвольного следующего сообщения;
- после restart бот предлагает снова открыть `/support`;
- не создавать persistent ticket schema только ради одного шага ввода.

### Подтверждение

После успешной доставки:

```text
Сообщение передано разработчику. Если потребуется ответ, он придёт в этот чат.
```

Допустимо добавить:

```text
Бот не предназначен для срочной помощи.
```

Не обещать срок ответа.

## 6. Доставка владельцу и ответ пользователю

### Получатели

Использовать отдельный server-side allowlist получателей, не связанный автоматически с application Admin RBAC.

Предпочтительный naming:

```text
TELEGRAM_FEEDBACK_ENABLED
TELEGRAM_FEEDBACK_RECIPIENT_IDS
```

Точные имена согласовать с current settings style.

Требования:

- использовать тот же `TELEGRAM_BOT_TOKEN`;
- отдельного support token нет;
- recipient IDs не дают `support_admin`, `super_admin`, Root или другие application capabilities;
- application admins не становятся получателями автоматически;
- allowlist валидируется при включённой функции;
- пустой allowlist даёт controlled unavailable state;
- значения не попадают во frontend bundle и публичную документацию;
- пользователь не видит личный username/ID владельца.

### Служебное сообщение

Для каждого обращения основной бот отправляет каждому configured recipient:

- категорию;
- opaque request identifier;
- display name и username с корректным escaping;
- Telegram user ID только в приватном recipient chat, если он нужен для routing;
- время получения;
- инструкцию ответить именно reply на служебный header.

Затем бот использует `copy_message` для исходного текста/медиа, не скачивая файл локально.

### Надёжный reply routing

Routing должен работать после restart.

Допустим marker в служебном сообщении, если одновременно выполняются условия:

- служебное сообщение отправлено текущим ботом;
- reply handler проверяет `reply_to_message.from_user.id` текущего бота;
- marker имеет строгий формат;
- target Telegram ID не берётся из произвольного текста пользователя;
- invalid/forged marker не приводит к отправке на произвольный chat ID.

Не хранить единственную связь `request -> user` только в оперативной памяти.

### Ответ пользователю

- только configured recipient может выполнить relay response;
- recipient обязан ответить reply на служебный header;
- текст/media копируются пользователю без раскрытия личного аккаунта recipient;
- перед содержимым допустим нейтральный заголовок `Ответ разработчика`;
- обычное сообщение владельца без reply не отправляется пользователю;
- обычные команды и сообщения владельца в основном боте продолжают работать;
- если пользователь заблокировал бот, recipient получает безопасное сообщение о недоставке;
- bot не создаёт read receipts, online status, assignment queue или conversation thread в application DB.

## 7. Защита от спама и утечек

Обязательно:

- feedback только в private chats;
- игнорировать сообщения от bot accounts;
- per-user rate limit;
- небольшой burst для текста + скриншота;
- cooldown после превышения;
- отсутствие auto-ban;
- ограничение поддерживаемых типов вложений по metadata;
- не скачивать вложения без необходимости;
- duplicate update protection/idempotent handling;
- обязательный `answerCallbackQuery` для каждого callback;
- HTML/Markdown escaping;
- no message body, caption, filename, username, raw auth data или attachment content в обычных logs;
- safe error codes;
- отсутствие token/secret logging;
- graceful Telegram API outage behavior;
- запрет на автоматическое изменение account, role, trainer application или user data по тексту обращения;
- отсутствие bot-to-bot loop.

Выбрать разумный rate limit после проверки текущей инфраструктуры. Ориентир для первого релиза:

```text
до 5 пересылаемых сообщений от одного пользователя за 10 минут
```

Он должен быть конфигурируемым и покрытым tests, но не превращаться в отдельную антифрод-систему.

## 8. Очистка legacy support runtime

После переноса и тестирования удалить или безопасно deprecated-маркировать:

```text
SUPPORT_BOT_TOKEN
SUPPORT_BOT_ENABLED
отдельный support-bot service
отдельный polling entrypoint
support_config.py
obsolete support_bot tests
```

Существующий `SUPPORT_ADMIN_TELEGRAM_USER_IDS`:

- либо заменить на ясный `TELEGRAM_FEEDBACK_RECIPIENT_IDS`;
- либо оставить временный backward-compatible alias на один release;
- в документации явно указать, что это только recipient allowlist и он не связан с application role `support_admin`.

Не менять:

- `TELEGRAM_BOT_TOKEN`;
- `TELEGRAM_BOT_USERNAME` кроме фиксации реального `your_fitness_coach_bot` в deployment config;
- OAuth credentials;
- proxy/tunnel secrets;
- BotFather ownership;
- production token.

## 9. Web, TMA, Profile и Landing

### Profile/help

Добавить или уточнить entry point:

```text
Помощь и обратная связь
```

Он открывает основной бот, а не личный Telegram аккаунт и не deprecated support-bot.

Canonical link:

```text
https://t.me/your_fitness_coach_bot?start=support
```

Category links:

```text
https://t.me/your_fitness_coach_bot?start=support_bug
https://t.me/your_fitness_coach_bot?start=support_account
https://t.me/your_fitness_coach_bot?start=support_idea
https://t.me/your_fitness_coach_bot?start=support_contact
```

Не строить встроенный messenger.

### Task `72`

Финальный TMA pass обязан проверить:

- открытие support deep link через поддерживаемый Telegram API/helper;
- возврат из bot chat в Mini App;
- отсутствие потери auth state;
- `/start support`;
- menu button и `/app`;
- отсутствие конфликта с `link_<token>`;
- отсутствие конфликтов с notification deep links.

При интеграции полного backlog добавить `59A` в зависимости task `72`.

### Task `73`

Landing использует только реальную canonical ссылку на `@your_fitness_coach_bot` в support/contact section.

Не публиковать личный username владельца.

При интеграции полного backlog добавить `59A` в product truth/dependency contract task `73`.

### Tasks `83` и `90`

После реализации AI Coach объяснить границу:

```text
AI Coach -> вопросы о тренировках, питании и использовании функций
Telegram feedback -> ошибка, аккаунт, предложение, жалоба или связь с разработчиком
```

AI Coach не блокирует возможность написать человеку.

## 10. BotFather и публичное оформление

Codex обязан подготовить, но не применять от имени владельца:

- canonical display name;
- About/short description;
- full description;
- command list;
- avatar из mark-only asset task `07`;
- optional description media;
- Main Mini App URL checklist;
- menu button checklist;
- splash screen values из canonical YFC Light/Dark tokens;
- Main Mini App preview checklist;
- privacy/group/inline settings;
- verification и rollback checklist.

Использовать отдельный owner guide из этого пакета:

```text
BOTFATHER_SETUP_your_fitness_coach_bot.md
```

BotFather actions являются ручным owner checkpoint. Codex не должен утверждать, что настройка выполнена, пока владелец её фактически не применил и не проверил.

## 11. Документация

Обновить durable documentation на русском языке:

- назначение единого `@your_fitness_coach_bot`;
- command contract;
- `/start` payload contract;
- support/feedback flow;
- recipient configuration;
- privacy/retention boundary;
- удаление отдельного support runtime;
- BotFather setup;
- local/staging testing;
- production enable/disable;
- Telegram API outage handling;
- связь с notification infrastructure;
- отдельность Bot API polling и Telegram login proxy-tunnel;
- запрет на публикацию bot token.

В privacy/legal surface фактически объяснить, что пользователь добровольно отправляет обращение через Telegram и Telegram участвует в передаче/хранении сообщений по правилам своей платформы.

Не придумывать сроки хранения, SLA или юридические гарантии, которых система не обеспечивает.

## Out of scope

Не делать:

- отдельный новый support-бот;
- отдельный support token;
- второй polling process для основного token;
- generic messenger;
- ticket inbox в Admin Workspace;
- CRM/helpdesk integration;
- trainer-client chat;
- AI auto-triage или AI-ответ владельца;
- автоматические действия с account/role/data по сообщению;
- emergency/medical support;
- group/community bot;
- inline mode;
- bot-to-bot communication mode;
- Telegram Business integration;
- оплату или Telegram Stars;
- production deploy;
- token rotation без подтверждённой компрометации;
- изменение Telegram login proxy-tunnel.

## Проверки

### Unit

- canonical command list и private scope;
- `/start` без payload;
- `/start link_<token>` regression;
- `/start support`;
- каждый support category payload;
- unknown start payload;
- `/app`;
- `/support` и `/feedback` alias;
- `/help`;
- `/settings`;
- `/privacy`;
- `/cancel`;
- legacy `/timezone`;
- unknown command;
- free text outside support flow;
- category selection/back/cancel;
- state reset/expiry;
- safe escaping;
- supported/unsupported message types;
- rate limit/cooldown;
- duplicate update;
- no-recipient/misconfigured recipient;
- one/multiple recipients;
- admin reply to valid bot-generated header;
- unauthorized reply;
- missing reply;
- invalid/forged marker;
- normal owner command/message is not hijacked;
- user blocked/delivery failed;
- no private content/secrets in logs.

### Integration/config

- один основной bot runtime;
- отдельный support service отсутствует в steady-state compose;
- main polling lock/conflict protection сохранён;
- notification delivery task `59` не сломан;
- Mini App menu button и `/app`;
- Profile deep link;
- environment validation;
- no `SUPPORT_BOT_TOKEN` in final steady-state contract;
- auth/tunnel variables не изменены;
- targeted lint/typecheck/tests/build согласно `AGENTS.md`.

### Manual Telegram smoke

Если доступен реальный Telegram client:

- открыть профиль `@your_fitness_coach_bot`;
- новый пользователь нажимает Start;
- `/start` показывает понятное меню;
- `Открыть приложение` запускает правильную Mini App;
- команды видны через `/`;
- `/help` и `/settings` доступны;
- каждая support category работает;
- screenshot/file relay работает;
- `/cancel` работает;
- ответ владельца возвращается пользователю;
- личный аккаунт владельца не раскрывается;
- linking flow не сломан;
- timezone работает;
- notifications продолжают приходить;
- support deep link из Web/TMA открывает правильный flow;
- отдельный support-бот не требуется.

Если реальный client недоступен, выполнить mock/integration checks и честно указать ограничение.

## Done when

- используется один публичный `@your_fitness_coach_bot`;
- используется один основной `TELEGRAM_BOT_TOKEN`;
- отдельный support token/process удалён из целевой архитектуры;
- пользователь сразу понимает, как открыть приложение и как связаться с разработчиком;
- команды совпадают в code/docs/BotFather checklist;
- свободный текст не пересылается без явного входа в support flow;
- bug/account/idea/contact обращения доставляются configured recipient;
- ответ возвращается в тот же bot chat;
- owner/admin messages не перехватываются ошибочно;
- нет generic messenger, CRM или fake SLA;
- notifications, linking, TMA auth, timezone и auth proxy-tunnel не сломаны;
- подготовлен и проверен подробный BotFather owner guide;
- профильные tests проходят;
- документация соответствует реализации.

## Рекомендуемый commit

```text
feat(telegram): add feedback flow to main bot
```

## Процесс и отчёт

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными. Текущий код, Git history и `docs/` являются source of truth.

Не проводить повторный полный аудит. Исследовать только:

- bot runtime;
- task `59` notification integration;
- Telegram Profile/TMA deep links;
- config/deploy;
- related tests/docs.

Работать в текущей feature-ветке.

Не:

- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- менять BotFather settings или token от имени владельца;
- переходить к следующему task.

После реализации:

1. запустить только профильные проверки;
2. проверить `git diff` и отсутствие secrets;
3. создать один логический commit при tracked changes;
4. в финальном отчёте указать:
   - что переиспользовано;
   - что изменено;
   - какие legacy support files/config удалены;
   - command/deep-link contract;
   - config/docs/assets;
   - реально запущенные проверки;
   - ручные действия владельца в BotFather/production;
   - ограничения;
   - commit hash.
