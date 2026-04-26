# FitMiniApp

Telegram Mini App для персонального фитнес-сопровождения: клиент тренируется и
ведёт прогресс в Telegram, тренер собирает программы и назначает КБЖУ, администратор
управляет пользователями, ролями и операционными данными.

Проект закрывает полный путь от первого входа до регулярной работы с клиентом:
авторизация через Telegram WebApp, профиль и онбординг, тренировка на сегодня,
история подходов, каталог упражнений, конструктор программ, кабинет тренера,
уведомления, mock-billing и production-доставка через Cloudflare Tunnel.

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
- Docker Compose поднимает PostgreSQL, backend, bot, worker и Cloudflare Tunnel;
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
    +--> Cloudflare Tunnel -> HTTPS domain
```

Сервисы в `docker-compose.yml`:

- `db` - PostgreSQL 16;
- `backend` - FastAPI, API, статика Mini App, coach UI и admin UI;
- `bot` - aiogram-бот для открытия Mini App и выбора timezone;
- `worker` - фоновые уведомления;
- `cloudflared` - HTTPS-доступ через Cloudflare Tunnel без отдельного reverse proxy.

## Стек

- Python 3.12;
- FastAPI, SQLAlchemy, Alembic, Pydantic Settings;
- PostgreSQL, SQLite для тестов;
- Vanilla JS, HTML и CSS для Telegram Mini App;
- Telegram WebApp init data, JWT access/refresh tokens;
- aiogram для Telegram-бота;
- Docker Compose и Cloudflare Tunnel;
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

SECRET_KEY=change-me
DATABASE_URL=postgresql+psycopg://fitminiapp:change-me@db:5432/fitminiapp

ENABLE_DEV_AUTH=false
ADMIN_TELEGRAM_USER_IDS=123456789
FRONTEND_BASE_URL=https://your-domain.example
BACKEND_INTERNAL_URL=http://backend:8000

CLOUDFLARED_TOKEN=
TELEGRAM_BOT_TOKEN=change-me

PAYMENT_PROVIDER=mock
PAYMENT_PUBLIC_URL=https://your-domain.example
WORKER_POLL_SECONDS=10
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
использовать встроенный сервис `cloudflared`.

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
docker compose up -d --build
```

Проверка:

```bash
curl https://app.your-fitness-coach.ru/health
```

## Telegram bot и Mini App

Бот использует:

- `TELEGRAM_BOT_TOKEN`;
- `FRONTEND_BASE_URL`;
- `BACKEND_INTERNAL_URL`.

При `/start` бот пытается закрепить кнопку Mini App в нижнем меню Telegram. Если
Telegram не принимает menu button, бот отправляет fallback-сообщение с кнопкой
`Открыть FitMiniApp`. Для WebApp-кнопки `FRONTEND_BASE_URL` обязан начинаться с
`https://`.

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
Удаление пользователя удаляет связанные программы, связи с тренерами, pending-инвайты,
уведомления, платежные записи и refresh-токены.

## Клиенты тренера

Тренер добавляет клиента:

- по Telegram ID - самый надёжный вариант, потому что ID не меняется;
- по username - удобно для предварительного добавления до первого входа клиента.

Если клиент добавлен по username и позже входит через Telegram с тем же username,
backend связывает pending-приглашение с реальным пользователем. После первого входа
лучше ориентироваться на Telegram ID: username в Telegram может измениться.

## API

Публичные страницы:

- `/app` - Telegram Mini App;
- `/coach` - кабинет тренера;
- `/admin` - админ-панель;
- `/docs` - Swagger UI;
- `/health` - healthcheck.

Основные API-группы:

- `/api/v1/public/*` - публичная конфигурация frontend;
- `/api/v1/auth/*` - Telegram/dev login, refresh, logout;
- `/api/v1/me` - текущий пользователь, профиль и отвязка тренера;
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

Вручную внутри backend-контейнера:

```bash
docker compose exec backend alembic upgrade head
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
- `pre-commit run --all-files --show-diff-on-failure`;
- `pytest tests -q`.

## Безопасность

- Не коммить `.env`.
- Используй сильный `SECRET_KEY`.
- В production держи `ENABLE_DEV_AUTH=false`.
- Первый админ должен быть задан через `ADMIN_TELEGRAM_USER_IDS`.
- Для Telegram Mini App используй только HTTPS `FRONTEND_BASE_URL`.
- Не открывай backend напрямую наружу без HTTPS и контроля инфраструктуры.
