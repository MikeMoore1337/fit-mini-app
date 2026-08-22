# Помощь и обратная связь в Telegram

Канонический публичный бот продукта и поддержки: `@your_fitness_coach_bot`.

Ссылка на общий вход в поддержку:

```text
https://t.me/your_fitness_coach_bot?start=support
```

Команды `/support` и `/feedback` открывают категории обращения. Deep links
`support_bug`, `support_account`, `support_idea` и `support_contact` сразу открывают
соответствующий сценарий. Привязка аккаунта `/start link_<token>`, Mini App, часовой пояс и
публичное меню продолжают работать в том же Dispatcher и используют только
`TELEGRAM_BOT_TOKEN`.

## Публичный профиль и команды

Канонические name, About, Description, avatar, private-chat commands и default Menu Button
задаются единым контрактом в `bot/fitminiapp_bot/public_profile.py`. Публичный список содержит
только `/start`, `/app`, `/support`, `/settings`, `/help` и `/privacy`; технические команды
`/feedback`, `/cancel` и `/timezone` поддерживаются, но в default list не показываются. `/news`
до отдельной продуктовой task отсутствует.

`/start` сначала обрабатывает `link_<token>`, затем support payload, после чего показывает меню с
действиями «Открыть приложение», «Помощь и обратная связь», «Настройки» и «Что умеет бот».
Неизвестный payload или команда не раскрывает входные данные и безопасно возвращает пользователя
к меню. Все Web App кнопки используют стабильный `FRONTEND_BASE_URL/app` без cache-version query.
Старый per-chat Menu Button обновляется до этого контракта при следующем взаимодействии.

Команда `/privacy` использует только явно настроенный публичный HTTPS URL:

```dotenv
PRIVACY_POLICY_URL=https://your-fitness-coach.ru/privacy
```

Пока реальная production-страница не опубликована или значение невалидно, бот показывает
контролируемое состояние недоступности и предлагает `/support`; URL не выдумывается.

## Проверка и синхронизация Bot API metadata

Одноразовая команда работает отдельно от polling и всегда начинает с `getMe`. Любые writes
разрешены только при `is_bot == true` и exact username `your_fitness_coach_bot`.

```powershell
docker compose run --rm bot python -m fitminiapp_bot.profile_sync check
docker compose run --rm bot python -m fitminiapp_bot.profile_sync apply
```

`check` ничего не меняет и возвращает код `1`, если найден metadata diff или BotFather flag
mismatch. `apply` меняет только отличающиеся поля, выполняет read-back и возвращает per-field JSON
status. Исключение — первый безопасный
bootstrap canonical avatar: Bot API не раскрывает исходный asset, поэтому после успешного upload
его `file_unique_id` вместе с SHA-256 локального canonical asset сохраняется без секретов в
`BOT_PROFILE_SYNC_STATE_PATH` на существующем persistent `bot_polling_lock` volume. Последующие
запуски сравнивают эту identity и являются no-op, пока avatar не изменился.

Команда также выводит фактические `getMe` flags и точные `owner_actions` только для выявленных
BotFather-only mismatch. Она не меняет Telegram modes, Main Mini App/Web Login, token, proxy или
TLS и не отправляет сообщения пользователям.

## Границы поддержки

Поддержка принимает сообщения об ошибках, вопросы о входе и аккаунте, предложения, вопросы
о режиме тренера и другие нестандартные обращения. Это не чат тренера с клиентом, CRM,
круглосуточная линия, медицинская или экстренная помощь. Бот не обещает SLA и не показывает
статус «оператор онлайн».

Пользователь должен выбрать категорию и отправить одно текстовое сообщение, фото или документ.
Другие типы media не пересылаются. Свободный текст вне активного сценария не становится
обращением. `/cancel` завершает сценарий, а состояние ввода истекает через 15 минут. После
рестарта in-memory FSM намеренно сбрасывается: пользователь должен снова вызвать `/support`,
поэтому случайный свободный текст не будет переслан.

Перед вводом бот предупреждает не отправлять пароли, коды подтверждения, токены, платёжные
данные и лишние документы. Файлы не загружаются на сервер: бот использует Telegram
`copyMessage`.

## Маршрутизация и данные

Администраторы задаются существующей server-side настройкой
`ADMIN_TELEGRAM_USER_IDS`. Видимость служебного сообщения не заменяет проверку полномочий:
backend повторно проверяет ID администратора, а ответ атомарно привязывается к конкретному
case ID и Telegram user ID.

В PostgreSQL хранится только служебная метаинформация обращения:

- случайный case ID;
- Telegram user ID и ID исходного сообщения;
- категория, статусы и timestamps;
- ID администратора и его сообщения после попытки ответа.

Текст, подписи, фотографии и документы не сохраняются в БД, logs или telemetry. Они остаются
в Telegram. Метаданные автоматически ограничивают обращения одной категории до трёх на
пользователя в час, истекают для ответа через 7 дней и удаляются через 30 дней. При удалении
связанного аккаунта его support metadata также удаляется. Audit events содержат только action,
case ID, категорию и результат без текста обращения и Telegram user/admin IDs.
Удаление из основной БД не стирает уже созданные резервные копии раньше срока их существующей
backup-retention policy; содержимое обращения в database backups не попадает вовсе.

Заблокированный или удалённый пользователь помечается как недоступный без фоновых повторов.
Transient failure до отправки не запускает бесконечный retry: backend может снова открыть кейс
только после подтверждённого результата `failed`. Если Telegram принял ответ, но backend не
подтвердил запись результата, кейс остаётся заблокированным в состоянии `replying`, а
администратор получает явное предупреждение не повторять ответ. Это сохраняет at-most-once
доставку ценой ручного разбора такого редкого неопределённого случая. Ответ пользователю явно
помечается как ответ команды Your Fitness Coach.

## Runtime и конфигурация

Основной сервис `bot` — единственный polling owner для `TELEGRAM_BOT_TOKEN`. Он использует
существующий общий volume lock, conflict detection и network backoff. `BOT_INTERNAL_TOKEN`
аутентифицирует только внутренние bot-to-backend запросы. Bot API использует явный
`TELEGRAM_BOT_PROXY_URL`; если отдельный маршрут не задан, временно переиспользуется существующий
`TELEGRAM_OAUTH_PROXY_URL`. Ambient proxy не подхватывается, проверка TLS-сертификата и hostname
остаётся включённой. Пустые обе переменные означают прямое соединение.

Минимальная production-конфигурация:

```dotenv
TELEGRAM_BOT_TOKEN=<BotFather token основного бота>
TELEGRAM_BOT_USERNAME=your_fitness_coach_bot
BOT_INTERNAL_TOKEN=<отдельный случайный секрет не короче 32 символов>
ADMIN_TELEGRAM_USER_IDS=123456789,987654321
PRIVACY_POLICY_URL=<подтверждённый production HTTPS URL либо пусто>
BOT_PROFILE_SYNC_STATE_PATH=/var/lock/fitminiapp-bot/profile-sync-state.json
# Предпочтительный отдельный Bot API route; credentials не выводятся в logs.
TELEGRAM_BOT_PROXY_URL=socks5://host.docker.internal:1081
# Допустимый fallback для Bot API и отдельный route browser Telegram OAuth.
TELEGRAM_OAUTH_PROXY_URL=socks5://host.docker.internal:1081
```

Каждый администратор должен заранее открыть `@your_fitness_coach_bot` и нажать **Start**:
Telegram не разрешает боту первым начинать личный диалог. Реальные токены и ID не коммитятся и
не добавляются в screenshots/logs.

## Production rollout и rollback

Production runtime не содержит отдельного `support-bot`: поддержку обслуживает только сервис
`bot`, а deploy запускает один polling owner и удаляет orphan-контейнеры прежнего Compose contract.
Legacy-переменные `SUPPORT_BOT_TOKEN`, `SUPPORT_BOT_ENABLED` и
`SUPPORT_ADMIN_TELEGRAM_USER_IDS`, если они ещё остались в production `.env`, игнорируются и не
создают второй процесс. Их следует удалить из secret store после подтверждённого rollout; токен
не вращается и не отзывается автоматически.

Порядок выпуска:

1. Зафиксировать SHA текущего `master` как rollback baseline и создать штатную pre-deploy backup.
2. Применить additive migration `0033_bot_support_cases`; она создаёт только таблицу routing
   metadata и два индекса, не изменяя существующие данные.
3. Развернуть `backend`, `worker` и единственный `bot`, затем проверить health, logs и отсутствие
   `support-bot`/duplicate polling.
4. Штатный `scripts/deploy_production.sh` выполняет `profile_sync check`; при exact
   `getMe.username == "your_fitness_coach_bot"` и ожидаемом diff выполняет bounded `apply`, затем
   повторяет read-back. Identity/config/verification error останавливает workflow до любых
   небезопасных writes. Только классифицированная недоступность внешнего Bot API оставляет sync в
   состоянии `pending` и не откатывает уже healthy runtime. BotFather-only mismatch выводится как
   owner action.
5. Проверить `/start`, `/start link_<token>`, `/support`, `/app` и `/settings`.

Если прямой Bot API egress недоступен, сначала проверяется существующий Telegram OAuth tunnel.
Bot runtime и profile sync используют одну session factory, а backend worker применяет тот же
явный route через `httpx` с `trust_env=false`; apply/read-back, polling и Telegram delivery не
расходятся по сетевому пути. Для последующего разделения достаточно задать
`TELEGRAM_BOT_PROXY_URL`; менять token или отключать TLS не требуется.

При runtime blocker используется существующий rollback mechanism или revert release commit без
force-push. Additive таблицу безопаснее оставить для forward-fix: прежний runtime её игнорирует.
Downgrade `0033_bot_support_cases` допустим только после остановки нового bot/worker и проверки,
что support metadata больше не нужна. Public metadata не откатывается автоматически и token не
вращается. Telegram browser login proxy-tunnel и TLS path этим rollout не меняются.

BotFather остаётся owner-only только для Main Mini App, Web Login и platform mode toggles,
которые Bot API не может безопасно изменить. Name, About, Description, avatar, commands и Menu
Button синхронизируются deployment CLI после exact identity guard. Команды из раздела выше
остаются безопасным ручным fallback для оператора с проверенным доступом к production host.

## Ручная проверка

Реальная проверка Telegram выполняется только владельцем с тестовыми аккаунтами после deploy:

1. `/start link_<token>` по-прежнему связывает один Web/Telegram account.
2. `/support`, `/feedback` и canonical deep links открывают правильные категории.
3. Text/photo/document доставляются разрешённым администраторам; unsupported media отклоняется.
4. Обычный текст вне flow не пересылается; `/cancel` и истечение состояния работают.
5. Ответ только на служебный case header доставляется нужному пользователю.
6. Обычный пользователь не может подменить admin reply; второй ответ на закрытый case не уходит.
7. Блокировка бота пользователем даёт администратору конечный понятный результат без retry loop.
8. В logs отсутствуют токены, URL с секретами, support text и точные Telegram IDs.
9. В `docker compose ps` только `bot` использует `TELEGRAM_BOT_TOKEN`; browser OAuth и Bot API
   могут использовать один production tunnel, но остаются разными client/session contracts.
