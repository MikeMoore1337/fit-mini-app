# FitMiniApp

Telegram Mini App для персонального фитнес-сопровождения: клиент тренируется и
ведёт прогресс в Telegram, тренер собирает программы и назначает КБЖУ, администратор
управляет пользователями, ролями и операционными данными.

Проект закрывает полный путь от первого входа до регулярной работы с клиентом:
авторизация через Telegram WebApp, профиль и онбординг, тренировка на сегодня,
история подходов, каталог упражнений, конструктор программ, кабинет тренера,
уведомления, mock-billing и production-доставка через прямой HTTPS или Cloudflare
Tunnel.

## Зачем это нужно

FitMiniApp превращает Telegram в лёгкий фитнес-кабинет без отдельной установки
приложения. Клиент открывает тренировку из бота, отмечает подходы, видит историю
и получает напоминания. Тренер быстро добавляет клиента, собирает программу,
назначает её и сохраняет пищевые ориентиры. Владелец проекта получает backend,
роли, админку, CI и понятную docker-инфраструктуру для запуска.

## Ключевые возможности

**Для клиента**

- вход из Telegram Mini App и dev-вход для локальной разработки;
- профиль: имя, цель, уровень, рост, вес, частота тренировок и timezone;
- план запуска с подсказками до первой тренировки;
- тренировка на сегодня со статусами, таймером, прогрессом подходов и вводом
  веса/повторений;
- история тренировок с пагинацией и очисткой;
- калькулятор КБЖУ: BMR, TDEE, калории, белки, жиры и углеводы;
- настройки напоминаний и ручное создание уведомлений.

**Для тренера**

- отдельный кабинет `/coach` и тренерский режим внутри Mini App;
- добавление клиентов по Telegram ID или username;
- pending-приглашения для клиентов, которые ещё не заходили в приложение;
- создание личных упражнений и шаблонов программ;
- назначение программ и КБЖУ закреплённым клиентам;
- просмотр связи клиент-тренер в профиле клиента.

**Для администратора**

- админ-панель `/admin`;
- просмотр пользователей и профилей;
- назначение ролей `client`, `coach`, `admin`;
- блокировка, разблокировка и удаление пользователей;
- просмотр платежей и уведомлений;
- просмотр и удаление шаблонов программ.

**Для продукта и эксплуатации**

- Telegram bot закрепляет кнопку Mini App и даёт fallback-ссылку, если Telegram
  не принимает WebApp-кнопку;
- команда `/timezone` сохраняет IANA timezone пользователя через backend;
- worker отправляет Telegram-уведомления по расписанию;
- mock-billing API поддерживает планы, checkout, завершение mock-платежа и
  активную подписку;
- FastAPI отдаёт API, Mini App, coach UI и admin UI из одного backend-сервиса;
- Docker Compose поднимает PostgreSQL, backend, bot, worker и опционально Caddy
  или Cloudflare Tunnel;
- pre-commit, Ruff, mypy, pytest и GitHub Actions уже настроены.

## Архитектура

```text
Telegram Bot
    |
    | /start, /timezone
    v
Telegram Mini App / Coach UI / Admin UI
    |
    v
FastAPI backend
    |
    +--> PostgreSQL
    |
    +--> Worker -> Telegram notifications
    |
    +--> Caddy / Cloudflare Tunnel -> HTTPS domain
```

Сервисы в `docker-compose.yml`:

- `db` - PostgreSQL 16;
- `backend` - FastAPI, API, статика Mini App, coach UI и admin UI;
- `bot` - aiogram-бот для открытия Mini App и выбора timezone;
- `worker` - фоновые уведомления;
- `caddy` - прямой HTTPS reverse proxy на 80/443, profile `direct-https`;
- `cloudflared` - HTTPS-доступ через Cloudflare Tunnel, profile `cloudflare`.

## Стек

- Python 3.12;
- FastAPI, SQLAlchemy, Alembic, Pydantic Settings;
- PostgreSQL, SQLite для тестов;
- Vanilla JS, HTML и CSS для Telegram Mini App;
- Telegram WebApp init data, JWT access/refresh tokens;
- aiogram для Telegram-бота;
- Docker Compose, Caddy и Cloudflare Tunnel;
- Ruff, ruff-format, mypy, pytest, pre-commit;
- GitHub Actions CI.

## Быстрый старт

Скопируй пример окружения:

```bash
cp .env.example .env
```

Заполни минимум:

```env
POSTGRES_DB=fitminiapp
POSTGRES_USER=fitminiapp
POSTGRES_PASSWORD=change-me

APP_ENV=prod
APP_NAME=FitMiniApp
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
APP_DOMAIN=your-domain.example

SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
REFRESH_COOKIE_NAME=fit_refresh_token
DATABASE_URL=postgresql+psycopg://fitminiapp:change-me@db:5432/fitminiapp

ENABLE_DEV_AUTH=false
ADMIN_TELEGRAM_USER_IDS=123456789
FRONTEND_BASE_URL=https://your-domain.example
BACKEND_INTERNAL_URL=http://backend:8000

CLOUDFLARED_TOKEN=
TELEGRAM_BOT_TOKEN=change-me
TELEGRAM_BOT_USERNAME=your_bot_username
BOT_INTERNAL_TOKEN=replace-with-a-separate-random-secret-at-least-32-characters
BOT_POLLING_ENABLED=true

PAYMENT_PROVIDER=mock
PAYMENT_PUBLIC_URL=https://your-domain.example
WORKER_POLL_SECONDS=10
REMINDER_SYNC_SECONDS=60
```

Запусти приложение:

```bash
docker compose up --build
```

Локальные адреса:

- Mini App: `http://localhost:8000/app`;
- Coach UI: `http://localhost:8000/coach`;
- Admin UI: `http://localhost:8000/admin`;
- API docs: `http://localhost:8000/docs`;
- Healthcheck: `http://localhost:8000/health`.

Для Telegram Mini App в production нужен HTTPS-домен. Например:

```text
https://app.your-fitness-coach.ru
```

## Production напрямую через 443

На сервере, где свободны порты 80 и 443, можно запускать приложение без
Cloudflare Tunnel. В этом режиме Caddy принимает внешний HTTPS, сам выпускает
Let's Encrypt сертификат и проксирует запросы во внутренний backend.

Что нужно сделать:

1. В DNS направить домен на IP нового сервера: `A` record для IPv4 и, если есть,
   `AAAA` record для IPv6.
2. Открыть входящие порты `80/tcp`, `443/tcp` и желательно `443/udp`.
3. Если домен управляется в Cloudflare, удалить или отключить tunnel-route. При
   включённом orange-cloud proxy использовать SSL/TLS mode `Full (strict)`.
4. В `.env` указать публичный домен и URL приложения.

```env
APP_DOMAIN=app.your-fitness-coach.ru
FRONTEND_BASE_URL=https://app.your-fitness-coach.ru
PAYMENT_PUBLIC_URL=https://app.your-fitness-coach.ru
CLOUDFLARED_TOKEN=
```

`APP_DOMAIN` - только hostname без `https://`. `FRONTEND_BASE_URL` и
`PAYMENT_PUBLIC_URL` - полный внешний HTTPS URL без пути. Именно эти URL
используют bot-кнопка Mini App и checkout-ссылки, поэтому после переезда
приложение будет указывать пользователей на новый сервер.

Запуск:

```bash
docker compose --profile direct-https up -d --build
```

Проверка:

```bash
curl https://app.your-fitness-coach.ru/health
```

## Локальная разработка

Для входа без Telegram включи dev-auth:

```env
APP_ENV=dev
ENABLE_DEV_AUTH=true
```

В dev-режиме на `/app` появится демо-вход. Seed-данные создают пользователей:

- `1001` - админ и тренер;
- `2001` - клиент;
- `2002` - клиент.

Для production оставляй:

```env
APP_ENV=prod
ENABLE_DEV_AUTH=false
```

## Production через Cloudflare Tunnel

Если на сервере не хочется поднимать Caddy/Nginx или 443 уже занят, можно
использовать сервис `cloudflared`.

Нужно:

1. Создать tunnel в Cloudflare Zero Trust.
2. Привязать public hostname, например `app.your-fitness-coach.ru`.
3. Направить hostname на `http://backend:8000`.
4. Положить token tunnel в `.env`.
5. Указать тот же HTTPS-домен в `FRONTEND_BASE_URL` и `PAYMENT_PUBLIC_URL`.

```env
CLOUDFLARED_TOKEN=...
FRONTEND_BASE_URL=https://app.your-fitness-coach.ru
PAYMENT_PUBLIC_URL=https://app.your-fitness-coach.ru
```

Запуск:

```bash
docker compose --profile cloudflare up -d --build
```

Проверка:

```bash
curl https://app.your-fitness-coach.ru/health
```

## Telegram bot и Mini App

Бот использует:

- `TELEGRAM_BOT_TOKEN`;
- `BOT_INTERNAL_TOKEN` — отдельный секрет для запросов bot → backend;
- `TELEGRAM_BOT_USERNAME`;
- `FRONTEND_BASE_URL`;
- `BACKEND_INTERNAL_URL`.

При `/start` бот пытается закрепить кнопку Mini App в нижнем меню Telegram. Если
Telegram не принимает menu button, бот отправляет fallback-сообщение с кнопкой
`Открыть FitMiniApp`. Для WebApp-кнопки `FRONTEND_BASE_URL` обязан начинаться с
`https://`.

`BOT_POLLING_ENABLED=false` отключает long polling в конкретном контейнере бота.
Это полезно, если один и тот же токен временно есть в двух деплоях: Telegram
разрешает только один активный `getUpdates`, иначе в логах будет
`TelegramConflictError`.

Compose подключает к `bot` общий Docker volume с блокировкой. Поэтому даже если
на одном сервере случайно подняты две копии проекта с одинаковым токеном, polling
ведёт только один контейнер, а второй автоматически ждёт освобождения блокировки.
Имя файла блокировки зависит от токена, поэтому разные боты друг другу не мешают.

Если второй экземпляр находится на другом сервере или запущен вне Compose,
Telegram всё равно может вернуть `TelegramConflictError`. В этом случае бот
освобождает локальную блокировку и повторяет попытку через
`BOT_CONFLICT_RETRY_SECONDS` (по умолчанию 300 секунд), не создавая постоянную
борьбу запросов. Для полного устранения конфликта останови лишний экземпляр либо
задай ему `BOT_POLLING_ENABLED=false`.

В BotFather проверь:

- домен Mini App совпадает с `FRONTEND_BASE_URL`;
- URL Mini App указывает на `/app`;
- после смены домена или URL иногда нужно заново открыть чат с ботом или отправить
  `/start`.

Команда `/timezone` открывает список регионов и IANA timezones. Выбранный timezone
сохраняется в backend и используется для "сегодня", расписания тренировок и
уведомлений. JWT и Telegram init data продолжают использовать UTC/Unix time как
системное время протоколов.

## Роли и доступы

Новые Telegram-пользователи создаются как клиенты. Первый админ задаётся через:

```env
ADMIN_TELEGRAM_USER_IDS=123456789
```

Несколько ID можно указать через запятую:

```env
ADMIN_TELEGRAM_USER_IDS=123456789,987654321
```

| Роль | Что может |
| --- | --- |
| `client` | Вести профиль, тренировки, историю, КБЖУ и уведомления |
| `coach` | Добавлять клиентов, создавать упражнения и программы, назначать программы и КБЖУ |
| `admin` | Управлять ролями, пользователями, блокировками, платежами, уведомлениями и шаблонами |

Заблокированный пользователь не проходит авторизацию и не может пользоваться API.
При блокировке или снятии роли тренера его активные связи и pending-приглашения
закрываются, но назначенные клиентам программы и история тренировок сохраняются.
Удаление пользователя удаляет его собственные данные, связи, pending-инвайты,
уведомления, платежные записи и refresh-токены. Шаблоны отвязываются от уже
назначенных программ: история других пользователей при этом не удаляется.

## Клиенты тренера

Тренер добавляет клиента:

- по Telegram ID - самый надёжный вариант, потому что ID не меняется;
- по username - удобно для предварительного добавления до первого входа клиента.

Если клиент добавлен по username и позже входит через Telegram с тем же username,
backend показывает ему pending-приглашение в профиле. Доступ к программам и КБЖУ
тренер получает только после явного подтверждения клиентом. Смена действующего
тренера также требует подтверждения. После первого входа лучше ориентироваться на
Telegram ID: username в Telegram может измениться.

## API

Публичные страницы:

- `/app` - Telegram Mini App;
- `/coach` - кабинет тренера;
- `/admin` - админ-панель;
- `/docs` - Swagger UI;
- `/health` и `/health/ready` - readiness с проверкой базы данных;
- `/health/live` - liveness процесса без проверки зависимостей.

Основные API-группы:

- `/api/v1/public/*` - публичная конфигурация frontend;
- `/api/v1/auth/*` - Telegram/dev login, refresh, logout;
- `/api/v1/me` - текущий пользователь, профиль, приглашения и отвязка тренера;
- `/api/v1/programs/*` - упражнения, шаблоны, назначение программ и клиенты;
- `/api/v1/coach/*` - кабинет тренера, клиенты и pending-инвайты;
- `/api/v1/workouts/*` - тренировка на сегодня, подходы, статусы и история;
- `/api/v1/nutrition/*` - сохранение КБЖУ для себя или клиента;
- `/api/v1/notifications/*` - настройки и пользовательские уведомления;
- `/api/v1/billing/*` - mock-планы, checkout и подписка;
- `/api/v1/admin/*` - пользователи, роли, платежи, уведомления и шаблоны;
- `/api/v1/bot/*` - внутренние действия бота, сейчас сохранение timezone.

## Миграции

Backend использует Alembic. Docker-entrypoint ждёт базу данных, применяет миграции
и затем запускает Uvicorn.

Текущий head — `0014_hardening_data_integrity`. Перед обновлением существующей базы обязательно сделайте резервную копию PostgreSQL.

После обычного `docker compose up -d --build` отдельно запускать `alembic upgrade head` не нужно: backend уже делает это при старте. Если миграции всё же нужно применить вручную, остановите сервисы приложения и запустите одноразовый backend-контейнер:

```bash
docker compose stop backend worker bot
docker compose up -d db
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d backend worker bot
```

## Качество кода

Установить зависимости для разработки:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r bot/requirements.txt
```

Установить pre-commit hook:

```bash
pre-commit install
```

Запустить проверки вручную:

```bash
pre-commit run --all-files
pytest tests -q
```

`pre-commit` запускает:

- базовые проверки YAML/TOML, trailing whitespace, merge conflict markers и крупных файлов;
- `ruff --fix` для lint и автоисправлений;
- `ruff-format` для форматирования;
- `mypy` для backend-пакета `app`.

Ruff закрывает сортировку импортов, flake8-подобные правила и black-совместимое
форматирование. Отдельные `isort`, `black` и `flake8` в pipeline не запускаются.

## CI

GitHub Actions workflow находится в `.github/workflows/ci.yml`.

CI запускается на:

- push в `main` или `master`;
- pull request.

CI делает:

- установку backend и bot зависимостей;
- проверку совместимости установленных зависимостей через `pip check`;
- синтаксическую проверку frontend JavaScript через `node --check`;
- `pre-commit run --all-files --show-diff-on-failure`;
- применение всей цепочки Alembic к PostgreSQL 16;
- `pytest tests -q` на PostgreSQL.

## Безопасность

- Не коммить `.env`.
- Используй сильный `SECRET_KEY`.
- Используй отдельный сильный `BOT_INTERNAL_TOKEN`; не переиспользуй Telegram bot token.
- В production держи `ENABLE_DEV_AUTH=false`.
- Первый админ должен быть задан через `ADMIN_TELEGRAM_USER_IDS`.
- Для Telegram Mini App используй только HTTPS `FRONTEND_BASE_URL`.
- Не открывай backend напрямую наружу без HTTPS и контроля инфраструктуры.
- Production-конфигурация проверяется при старте: placeholder-секреты, debug,
  dev-auth и не-HTTPS публичные URL приводят к отказу запуска.
- Refresh-токен хранится только в `HttpOnly Secure SameSite=Strict` cookie, а
  короткоживущий access-токен — в `sessionStorage`. CSP разрешает inline-скрипты
  только по явно зафиксированным SHA-256 хешам.
- Endpoint завершения mock-платежа требует авторизацию и разрешён только владельцу
  checkout, когда `PAYMENT_PROVIDER=mock`.
