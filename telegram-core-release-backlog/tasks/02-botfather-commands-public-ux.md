# TASK 02. Public bot UX и автоматическая Bot API profile synchronization

- Фаза: **Bot UX / Bot API / Minimal BotFather**
- Зависит от: **уже выполненных Telegram tasks `00` и `01`**
- Можно выполнять до main task `64`: **да**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$python-engineer`, `$security-engineer`, `$product-designer`, `$accessibility-engineer`, `$qa-engineer`, `$technical-writer`
- Условные skills: `$platform-engineer` только при runtime/deploy integration; `$backend-engineer` только если sync встраивается в существующий service layer
- Основная роль: **`implementer`**
- Контракт роли: `.agents/roles/implementer.md`

## Статус prerequisites

На момент запуска этой task Telegram tasks `00` и `01` уже выполнены.

Не переисполнять их и не переигрывать принятые там архитектурные решения. Текущий код после task `01` является исходной точкой. Перед изменениями достаточно точечно проверить участки, непосредственно затрагиваемые task `02`.

Если найден дефект в уже реализованном support/feedback contract, который блокирует task `02`, исправить только подтверждённый дефект в текущем scope и покрыть регрессией. Не проводить повторный аудит или общий рефакторинг task `01`.

## Ключевое решение v5

Не перекладывать на владельца BotFather-действия, которые официальный Bot API может выполнить сам.

Сам факт явного запуска этой task владельцем является разрешением Codex на bounded reversible Bot API metadata writes ниже, если одновременно:

```text
getMe.is_bot == true
getMe.username == "your_fitness_coach_bot"
```

Любой mismatch -> никаких Bot API writes.

Разрешение не распространяется на token rotation, deploy, Main Mini App/Web Login BotFather changes, proxy, массовые сообщения и новые Telegram modes.

## 1. Canonical public profile contract

Создать один source of truth в коде/config для публичных bot metadata.

### Name

```text
Your Fitness Coach
```

### About / short description

До production enable AI Coach:

```text
Тренировки, питание, прогресс и работа с тренером - в одном приложении.
```

Не добавлять AI Coach/news/ratings/users/24x7 claims.

### Description

После task `01` использовать фактологичный текст release scope, например:

```text
Your Fitness Coach помогает планировать тренировки, вести дневник питания и отслеживать прогресс в Telegram и браузере.

Откройте приложение, чтобы работать с программами, тренировками, питанием и результатами. Через этого же бота можно получить помощь, сообщить об ошибке или предложить улучшение.
```

Текст можно слегка адаптировать к фактическому product scope, но нельзя обещать notification features main task `64`, если они ещё не реализованы.

### Avatar

Использовать canonical mark-only asset результата main task `07`.

Не редизайнить логотип.

Если есть canonical vector asset, допустим deterministic production raster export для Telegram без изменения формы/цветового contract.

Если canonical asset отсутствует или неоднозначен:

- не подставлять временную картинку;
- продолжить остальные metadata sync;
- вывести один конкретный follow-up по asset.

## 2. Commands до main task 64

Private-chat command source:

```text
start - Главное меню
app - Открыть приложение
support - Помощь и обратная связь
settings - Настройки и часовой пояс
help - Возможности и команды
privacy - Политика конфиденциальности
```

Поддержать, но не показывать в default list:

```text
/feedback
/cancel
/timezone
```

No `/news`.

После main task `64` task `03` может автоматически изменить только description `/settings` на:

```text
settings - Настройки и уведомления
```

если notification preferences действительно доступны.

## 3. `/start` и main menu

Priority:

1. `link_<token>`;
2. support payloads;
3. existing canonical app payloads;
4. unknown -> main menu without raw error.

Main menu:

```text
[Открыть приложение]
[Помощь и обратная связь]
[Настройки]
[Что умеет бот]
```

`/app` и buttons используют canonical stable HTTPS Mini App URL из config/helper.

Не использовать BotFather Main Mini App URL вида:

```text
/app?v=<cache-version>
```

Cache-busting detail может существовать во внутреннем runtime только если действительно нужен и не становится public canonical URL.

## 4. Реализовать idempotent sync tool/service

Переиспользовать текущую архитектуру проекта. Не вводить тяжёлую отдельную CLI framework.

Нужны два логических режима:

```text
check / dry-run
apply
```

Названия команды/entrypoint выбрать по repository conventions.

Sync должен:

1. вызвать `getMe`;
2. проверить exact username;
3. получить current metadata где API позволяет;
4. вычислить diff;
5. в `check` ничего не менять;
6. в `apply` изменить только отличающиеся поля;
7. использовать официальный Bot API/client methods;
8. выполнить read-back verification;
9. вернуть per-field status;
10. не печатать token/secret.

Минимальный автоматизируемый набор, если поддержан текущим Telegram client stack:

```text
setMyName
setMyShortDescription
setMyDescription
setMyProfilePhoto
setMyCommands
setChatMenuButton
```

### Client SDK gap

Если текущая версия Telegram client library не поддерживает официальный метод:

1. проверить, поддерживает ли актуальная совместимая версия библиотеки;
2. использовать минимальный dependency upgrade только при низком regression risk и успешных targeted tests;
3. не создавать самописный небезопасный transport только ради одной profile operation;
4. если безопасная поддержка невозможна в scope, пометить только конкретное поле `CLIENT_GAP`, не откатывая остальную автоматизацию.

## 5. Menu Button

Целевой default Menu Button:

```text
Открыть приложение
```

URL - canonical stable production HTTPS app URL из config.

Проверить существующие per-chat overrides. Если runtime раньше создавал старый button/text/version URL для пользователей, реализовать безопасную migration policy при следующем interaction или другую минимальную стратегию, согласованную с текущей архитектурой.

BotFather и runtime не должны постоянно перезаписывать друг друга.

## 6. `/privacy`

Команда должна вести на реальную production privacy policy page.

Если реальный URL невозможно подтвердить из current config/docs:

- не придумывать URL;
- handler даёт controlled unavailable state или использует уже подтверждённый canonical value;
- финальный report содержит один конкретный missing config action.

## 7. Автоматическая диагностика BotFather-only flags

Через `getMe` автоматически собрать release report:

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

YFC target:

- groups disabled;
- group privacy not disabled;
- guest mode disabled;
- inline mode disabled;
- business/secretary mode disabled;
- threaded mode disabled;
- bot management mode disabled;
- Main Mini App enabled к release gate.

Task `02` не должна менять BotFather-only flags автоматически. Она формирует минимальные owner actions только для фактических mismatch.

## 8. BotFather owner-only boundary

В task `02` владельцу оставляются только действия из `BOTFATHER_OWNER_CHECKLIST.md`, которые реально нужны после automated check.

Не просить владельца вручную менять:

```text
name
About
Description
avatar
commands
Menu Button
```

если Bot API sync уже успешен.

Main Mini App/Web Login/splash/previews остаются отдельной boundary согласно `TELEGRAM_AUTOMATION_BOUNDARY.md`.

## 9. Apply policy

Если в среде Codex доступен действующий token exact public bot и outbound Telegram API:

- после tests/review выполнить `check`;
- при exact identity и ожидаемом diff выполнить bounded `apply` без дополнительного owner вопроса;
- выполнить read-back;
- не делать production deploy;
- не отправлять сообщения пользователям ради metadata sync.

Если token/network недоступен:

- task всё равно может быть завершена как implementation;
- tests используют mocks/fakes;
- report указывает `NOT_APPLIED_ENVIRONMENT_LIMITATION`;
- оставить одну точную sync command для запуска позже Codex/owner в среде с token;
- не превращать это в ручное заполнение BotFather.

## 10. Accessibility и plain language

- labels понятны без emoji;
- mobile-friendly длина;
- keyboard order предсказуем;
- ошибки содержат следующий шаг;
- critical actions не различаются только цветом/emoji;
- Description/About не обещают функции вне release scope.

## Checks

Минимум:

- wrong-token/wrong-username guard запрещает write;
- `check` не меняет remote state;
- no-op apply действительно no-op;
- partial diff меняет только нужные fields;
- commands private scope;
- `/start link_<token>` regression;
- support payload regression;
- unknown payload/command;
- `/app` HTTPS/canonical URL;
- `/privacy` valid/invalid config;
- Menu Button read-back;
- profile metadata read-back where supported;
- no token logs;
- Telegram API timeout/failure не вызывает infinite restart;
- mobile labels.

После implementation обязателен independent review и QA pass.

## Done when

- public bot UX понятен;
- bot profile contract имеет один source of truth;
- name/About/Description/avatar/commands/Menu Button автоматизированы максимально безопасно;
- remote Bot API state применён и verified, если среда позволяла;
- owner checklist содержит только BotFather-only фактические действия;
- main task `64` не является blocker для task `02`.

## Процесс

Полный task lifecycle.

Не переходить к task `03`.

После этой task остановиться до main task `64`.
