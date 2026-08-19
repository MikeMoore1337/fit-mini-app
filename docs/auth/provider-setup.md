# Настройка провайдеров аутентификации

Это руководство описывает ручную production-настройку браузерного OAuth/OIDC для
Telegram, Google, Яндекс и VK ID. Apple остаётся необязательным провайдером.
Telegram Mini App использует отдельный поток с подписанным `initData` и не зависит от
реквизитов браузерного OAuth.

Проверяйте официальную документацию перед изменением приложения провайдера:
поля кабинетов, требования к модерации и фирменному оформлению могут меняться.

## Общий контракт

Канонический origin приложения задаётся в `FRONTEND_BASE_URL`. Для production
он должен быть абсолютным HTTPS URL без дополнительного path, например:

```text
https://app.your-fitness-coach.ru
```

Зарегистрируйте точные callback URL:

| Провайдер | Callback URL |
|---|---|
| Telegram | `https://app.your-fitness-coach.ru/api/v1/auth/oauth/telegram/callback` |
| Google | `https://app.your-fitness-coach.ru/api/v1/auth/oauth/google/callback` |
| Яндекс | `https://app.your-fitness-coach.ru/api/v1/auth/oauth/yandex/callback` |
| VK ID | `https://app.your-fitness-coach.ru/api/v1/auth/oauth/vk/callback` |
| Apple, необязательно | `https://app.your-fitness-coach.ru/api/v1/auth/oauth/apple/callback` |

Redirect URI должен совпадать посимвольно, включая scheme, host, path и
отсутствие завершающего `/`. Не регистрируйте production callback в test app и
наоборот.

Все credentials задаются только backend-переменными окружения:

```text
TELEGRAM_OAUTH_CLIENT_ID
TELEGRAM_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
YANDEX_OAUTH_CLIENT_ID
YANDEX_OAUTH_CLIENT_SECRET
VK_OAUTH_CLIENT_ID
APPLE_OAUTH_CLIENT_ID
APPLE_OAUTH_CLIENT_SECRET
```

Провайдер появляется в `GET /api/v1/public/config` только при
`ENABLE_WEB_AUTH=true` и полном наборе необходимых полей. Endpoint возвращает
в OAuth-части ответа только имена доступных провайдеров, но не client IDs,
secrets, endpoints, tokens или внутреннее состояние OAuth. Частично настроенный
провайдер считается отключённым.

OAuth state хранится в короткоживущей подписанной HttpOnly session cookie.
OIDC-провайдеры дополнительно используют nonce; Telegram, Google, Яндекс и VK ID
используют PKCE S256. Provider email сохраняется как атрибут identity, но никогда
не используется как ключ аккаунта и не вызывает автоматическое объединение.

## Telegram

### OIDC в браузере

1. Откройте настройки бота в `@BotFather` → **Bot Settings** → **Web Login**.
2. Добавьте origin приложения и точный callback URL из таблицы.
3. Получите Web Login Client ID и Client Secret и задайте
   `TELEGRAM_OAUTH_CLIENT_ID` и `TELEGRAM_OAUTH_CLIENT_SECRET`.
4. Убедитесь, что имя и изображение бота соответствуют продукту: именно их
   пользователь видит при подтверждении входа.

Backend использует Telegram OIDC discovery, scope `openid profile`, Authorization
Code Flow, state, nonce и PKCE S256. Stable account key — числовой OIDC `sub`.
Телефон не запрашивается.

Официальные источники:

- [Log In With Telegram](https://core.telegram.org/bots/telegram-login)
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)

Если Web Login credentials отсутствуют, browser-кнопка Telegram не публикуется.
При заданном `TELEGRAM_BOT_USERNAME` пользователь всё ещё может открыть продукт
в Telegram.

### Telegram Mini App

Frontend автоматически передаёт только `Telegram.WebApp.initData` в
`POST /api/v1/auth/telegram/init`. Backend проверяет HMAC signature, `auth_date`,
ограничение возраста и положительный стабильный user ID. `initDataUnsafe` не
является источником identity.

`TELEGRAM_INIT_DATA_MAX_AGE_SECONDS` задаёт допустимое окно между запуском Mini
App и обменом assertion; default — 300 секунд, допустимый диапазон — 60–3600.
После истечения окна пользователь должен заново открыть Mini App.

## Google

1. В Google Auth Platform создайте OAuth client типа **Web application**.
2. Настройте branding/consent screen и подтвердите production domains.
3. Добавьте точный Authorized redirect URI из таблицы.
4. Задайте `GOOGLE_OAUTH_CLIENT_ID` и `GOOGLE_OAUTH_CLIENT_SECRET`.

Backend использует официальный OIDC discovery document и scopes
`openid profile email`. Authlib проверяет подпись ID token, issuer, audience,
expiry и nonce; account key — неизменяемый `sub`. Email хранится как verified
только при JSON claim `email_verified: true` и не заменяет `sub`.

Кнопка должна содержать понятное действие «Продолжить с Google», стандартный
цветной знак `G` и быть не менее заметной, чем другие provider-кнопки.

Официальные источники:

- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
- [Sign in with Google branding](https://developers.google.com/identity/branding-guidelines)

## Яндекс

1. Создайте приложение для авторизации пользователей в Яндекс OAuth.
2. В разделе Web services добавьте точный Redirect URI из таблицы.
3. Разрешите только `login:info` и `login:email`.
4. Задайте `YANDEX_OAUTH_CLIENT_ID` и `YANDEX_OAUTH_CLIENT_SECRET`.

Backend использует `https://oauth.yandex.ru/authorize`,
`https://oauth.yandex.ru/token` и `https://login.yandex.ru/info`, state и PKCE
S256. Stable account key — поле profile `id`. `default_email` является контактным
адресом; API не возвращает отдельный verification claim, поэтому приложение не
помечает его verified и не использует для поиска аккаунта.

Используйте фирменный знак и явный текст «Войти с Яндекс ID»; не меняйте цвета,
пропорции и внутренние отступы официального знака.

Официальные источники:

- [Получение кода из URL](https://yandex.ru/dev/id/doc/ru/codes/code-url)
- [Информация о пользователе](https://yandex.ru/dev/id/doc/ru/user-information)
- [Оформление кнопки](https://yandex.ru/dev/id/doc/ru/codes/buttons-design)

## VK ID

1. Создайте Web-приложение в кабинете подключения VK ID.
2. Добавьте точный Redirect URI из таблицы.
3. Задайте public application ID в `VK_OAUTH_CLIENT_ID`. Client secret этому
   server-side PKCE flow не требуется и во frontend не передаётся.

Backend использует `https://id.vk.ru/authorize`, `https://id.vk.ru/oauth2/auth`
и `https://id.vk.ru/oauth2/user_info`, scope `email`, state и обязательный PKCE
S256. Callback должен вернуть `code`, `state` и `device_id`; поддерживаются flat
query и JSON `payload` варианты. Конфликтующие варианты отклоняются. Stable
account key — `user.user_id`; email не считается явно verified.

Используйте обозначение «VK ID» и актуальный фирменный знак из кабинета или
официального SDK, не заменяя его произвольным логотипом VK.

Официальные источники:

- [VK ID для бизнеса](https://id.vk.ru/about/business/go/docs/ru/vkid/latest/vk-id/connection/start-integration)
- [Официальный VK ID Web SDK](https://github.com/VKCOM/vkid-web-sdk)

## Apple — необязательно

Apple не входит в обязательный набор. Чтобы безопасно оставить его доступным:

1. Создайте и свяжите Services ID, primary App ID, domain и Return URL.
2. Задайте Services ID в `APPLE_OAUTH_CLIENT_ID`.
3. Создайте подписанный JWT client secret и задайте его в
   `APPLE_OAUTH_CLIENT_SECRET`; контролируйте срок действия и ротацию.

Backend использует Apple OIDC discovery и scopes `openid email`. Apple может
вернуть имя/email только при первом согласии и может использовать private relay;
account key всегда `sub`.

Официальные источники:

- [Configure Sign in with Apple for the web](https://developer.apple.com/help/account/capabilities/configure-sign-in-with-apple-for-the-web/)
- [Generate and validate tokens](https://developer.apple.com/documentation/signinwithapplerestapi/generate-and-validate-tokens)

## Сетевые параметры

`OAUTH_HTTP_TIMEOUT_SECONDS` ограничивает discovery, token exchange и profile
requests (5–60 секунд, default 15). `OAUTH_FORCE_IPV4=true` помогает Docker-host
без рабочего IPv6 route. `OAUTH_PROXY_URL` относится к Google, Яндексу, VK ID и
Apple. `TELEGRAM_OAUTH_PROXY_URL` используется только canonical Telegram browser
OIDC client и обязателен в `prod`, если одновременно включён `ENABLE_WEB_AUTH` и
настроены оба Telegram OAuth credential. Отсутствующая или некорректная
конфигурация в этом режиме останавливает startup вместо silent direct fallback.

Telegram Mini App `initData` проверяется локально, а Telegram account linking
подтверждается через одноразовый bot deep link и внутренний backend endpoint;
эти потоки не используют `TELEGRAM_OAUTH_PROXY_URL`. Bot API и notification
delivery также не являются частью browser OIDC network path.

OAuth-клиенты игнорируют ambient proxy variables. Явный proxy не отключает TLS
certificate/hostname verification. Не используйте недоверенный публичный proxy:
через него проходят authorization codes и client secrets.

Compose передаёт server-only `.env` в backend и сохраняет
`host.docker.internal:host-gateway` для operator-managed tunnel на Docker-хосте.
Сам tunnel service не создаётся и не управляется приложением. При его
недоступности browser flow возвращает `unavailable`/`provider_failure`, не
создавая identity или session; другие providers и TMA продолжают работать.
Диагностируйте по безопасным event code, `provider=telegram`, `reason` и request
ID, не печатая proxy URL, credentials, authorization code или полный provider
response.

## Необязательная smoke-проверка

Live smoke выполняется вручную только после явной настройки provider app и
credentials. Локальные тесты и CI не требуют secrets и не обращаются к provider
API.

1. Откройте `GET /api/v1/public/config` и проверьте точный список
   `oauth_providers`; убедитесь, что response не содержит credential values.
2. Для каждого настроенного провайдера откройте `/login`, начните вход и
   проверьте правильный provider app name, domain, scopes и callback.
3. Отмените вход и убедитесь, что приложение возвращает безопасную ошибку без
   provider payload/token в URL или UI.
4. Завершите вход тестовым аккаунтом и проверьте `/app`, затем refresh страницы и
   logout. Refresh token не должен появляться в URL или `localStorage`.
5. Повторите вход той же identity и убедитесь, что новый внутренний аккаунт не
   создаётся. Совпадающий email другого provider не должен объединять аккаунты.
6. Для VK ID отдельно проверьте обычный redirect и поддерживаемый кабинетом JSON
   `payload` flow с обязательным `device_id`.
7. Для Telegram Mini App откройте приложение из Telegram и убедитесь, что вход
   происходит автоматически без browser `/login`. Изменённый или просроченный
   `initData` должен получить 401.
8. Временно заблокируйте тестового пользователя через штатный admin flow и
   убедитесь, что provider callback возвращает `auth_error=blocked`.

Не вставляйте secrets, authorization codes, tokens или полный `initData` в shell
history, screenshots, issue tracker и логи smoke-проверки.

## Безопасное отключение

Чтобы отключить один provider, удалите только его OAuth env values и
перезапустите backend. Чтобы отключить весь browser auth, установите
`ENABLE_WEB_AUTH=false`. Не удаляйте identities из БД: существующие аккаунты и
другие способы входа должны сохраниться.

После отключения проверьте `/api/v1/public/config`, отсутствие кнопки на `/login`
и возврат `auth_error=unavailable` при прямом обращении к start endpoint.
Telegram Mini App `initData` flow продолжает работать независимо от
`ENABLE_WEB_AUTH`.
