# Границы безопасности HTTP и production-логов

Документ фиксирует управляемые репозиторием ограничения входящих HTTP-запросов и безопасный
диагностический контракт. Сроки хранения, доступ к логам и резервным копиям здесь не определяются:
их lifecycle рассматривается отдельно.

## Лимиты тела запроса

Единый production-контракт:

- `1 MiB` (`1048576` байт) — JSON/form и остальные запросы по умолчанию;
- `64 KiB` (`65536` байт) — весь namespace `/api/v1/auth/*`, включая Telegram initData,
  email/dev-auth и GET/POST OAuth callback;
- тело ровно на границе допустимо, превышение на один байт возвращает `413` с кодом
  `request_body_too_large` без содержимого исходного payload;
- некорректный или неоднозначный `Content-Length` отклоняется с `400` и кодом
  `invalid_content_length`; отсутствие заголовка и chunked-передача контролируются по мере чтения;
- ASGI хранит для replay только допустимое тело до соответствующего лимита, прекращает чтение при
  первом превышении и не буферизует оставшуюся часть oversized payload.

Первую границу применяет `deploy/Caddyfile.edge`, вторую —
`fitminiapp_api.middleware.request_body_limit`. Тест
`backend/tests/test_request_body_limits.py` сверяет числовые значения edge и ASGI, поэтому изменение
только одной стороны ломает профильную проверку. Частные/authenticated ответы, включая ошибки
лимита, сохраняют `Cache-Control: no-store, private`.

Для прямого HTTPS public Caddy проксирует в `edge:8080`. Удалённо управляемый Cloudflare Tunnel
также обязан использовать origin `http://edge:8080`; Compose-сети не дают ему обратиться к backend
напрямую. Проверка Caddyfile и `docker compose config --quiet` обязательны перед развёртыванием.

### Процедура исключения

Глобальный лимит не повышается ради одного endpoint. Upload/import требует отдельной task и review,
в котором зафиксированы endpoint, максимальный размер, допустимые content types, способ streaming,
временное/постоянное хранение, очистка частичной загрузки, auth/authz, rate limit, timeout, защита от
decompression bombs и профильные edge/ASGI tests. До такого review broad exception запрещён.

## Безопасный production logging

Production formatter сериализует только контролируемое имя события и allowlisted поля:

- `timestamp`, `level`, `service`, `logger`;
- проверенный `request_id`, HTTP method, шаблон маршрута без path-параметров, status и duration;
- агрегированные SQL/pool metrics без SQL text и params;
- `body_limit_bytes`, безопасные `provider`/`reason`/`delivery_error` codes;
- `exception_type` без exception message и traceback;
- псевдонимный `notification_ref`, когда корреляция доставки действительно нужна.

Произвольные log messages превращаются в `application_log`. Production formatter не сериализует
traceback, exception message, URL, request/response body, SQL params, токены, food/note/measurement
text, имена или точные user/chat/notification identifiers. HTTP access log использует шаблон
маршрута (например, `/profiles/{profile_id}`), а не фактический path. Worker строит
`notification_ref` через keyed HMAC; значение пригодно для локальной корреляции и не раскрывает ID.

При `APP_DEBUG=true` backend может добавить очищенный traceback для локальной диагностики;
production validation запрещает `APP_DEBUG=true`. Добавление structured field требует отдельного
privacy/security review: поле должно быть ограничено по типу и размеру, не содержать персональных
значений и иметь конкретную операционную цель. Request ID можно передать пользователю для поиска
ошибки, но по нему нельзя восстанавливать payload.
