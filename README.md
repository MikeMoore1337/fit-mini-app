# FitMiniApp

Telegram Mini App для ведения тренировок: личный кабинет клиента, инструменты тренера,
админ-панель, бот для открытия Mini App и backend на FastAPI.

## Что умеет

Для клиента:

- тренировка на сегодня;
- логирование подходов, веса и повторений;
- история занятий и базовая статистика;
- профиль, цель, уровень подготовки;
- настройки напоминаний.

Для тренера:

- создание и редактирование шаблонов программ;
- добавление своих клиентов по Telegram ID или username;
- назначение программ клиентам;
- редактирование программ и упражнений для своих клиентов.

Для администратора:

- просмотр пользователей;
- назначение ролей `client`, `coach`, `admin`;
- блокировка и разблокировка пользователей;
- удаление пользователей;
- просмотр платежей и уведомлений;
- просмотр и удаление шаблонов программ.

Подписка и mock-billing в backend пока есть, но раздел подписки скрыт в UI.

## Архитектура

```text
Telegram Bot
    |
    | /start -> Mini App button
    v
Telegram Mini App / Admin UI
    |
    v
FastAPI backend
    |
    v
PostgreSQL
```

Сервисы в `docker-compose.yml`:

- `db` - PostgreSQL 16;
- `backend` - FastAPI, статика Mini App и admin UI;
- `bot` - Telegram bot, отправляет кнопку открытия Mini App;
- `worker` - фоновые задачи и напоминания;
- `cloudflared` - Cloudflare Tunnel для HTTPS-доступа без публичного 443 на сервере.

## Стек

- Python 3.12;
- FastAPI, SQLAlchemy, Alembic;
- PostgreSQL;
- Vanilla JS для Telegram Mini App;
- JWT + Telegram WebApp init data;
- Docker Compose;
- Ruff, ruff-format, mypy, pytest, pre-commit;
- GitHub Actions CI.

## Быстрый старт

Скопируй env-файл:

```bash
cp .env.example .env
```

Заполни минимум:

```env
POSTGRES_DB=fitminiapp
POSTGRES_USER=fitminiapp
POSTGRES_PASSWORD=change-me

SECRET_KEY=change-me
DATABASE_URL=postgresql+psycopg://fitminiapp:change-me@db:5432/fitminiapp

TELEGRAM_BOT_TOKEN=change-me
TELEGRAM_BOT_USERNAME=your_bot_username
FRONTEND_BASE_URL=https://app.your-fitness-coach.ru
PAYMENT_PUBLIC_URL=https://app.your-fitness-coach.ru

ADMIN_TELEGRAM_USER_IDS=123456789
CLOUDFLARED_TOKEN=
```

Запуск:

```bash
docker compose up --build
```

Локальные адреса backend:

- Mini App: `http://localhost:8000/app`
- Admin UI: `http://localhost:8000/admin`
- API docs: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

В production Telegram Mini App должен открываться по HTTPS. Текущий рабочий домен:

```text
https://app.your-fitness-coach.ru
```

## Production через Cloudflare Tunnel

Если 443 занят другим сервисом, можно не поднимать Caddy/Nginx на сервере. В проекте уже есть
сервис `cloudflared`, который прокидывает HTTPS-домен к локальному backend.

Нужно:

1. Создать tunnel в Cloudflare Zero Trust.
2. Привязать hostname, например `app.your-fitness-coach.ru`.
3. Направить public hostname на `http://backend:8000`.
4. Положить token tunnel в `.env`:

```env
CLOUDFLARED_TOKEN=...
FRONTEND_BASE_URL=https://app.your-fitness-coach.ru
PAYMENT_PUBLIC_URL=https://app.your-fitness-coach.ru
```

После этого:

```bash
docker compose up -d --build
```

Проверка:

```bash
curl https://app.your-fitness-coach.ru/health
```

## Telegram bot и Mini App

Бот использует `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` и `FRONTEND_BASE_URL`.

При `/start` бот отправляет кнопку `Открыть FitMiniApp`. Если `FRONTEND_BASE_URL` начинается
с `https://`, кнопка создаётся как Telegram Web App button. Если URL не HTTPS, Telegram такую
Mini App кнопку не примет.

Для production также проверь настройки в BotFather:

- домен Mini App должен совпадать с `FRONTEND_BASE_URL`;
- URL Mini App должен указывать на `/app`;
- после изменения домена или URL иногда нужно заново открыть чат или отправить `/start`.

## Роли и доступы

В production новые Telegram-пользователи создаются как клиенты.

Первый админ задаётся через:

```env
ADMIN_TELEGRAM_USER_IDS=123456789
```

Если ID несколько, укажи через запятую:

```env
ADMIN_TELEGRAM_USER_IDS=123456789,987654321
```

Роли:

| Роль | Что может |
| --- | --- |
| `client` | вести тренировки, профиль, уведомления |
| `coach` | создавать программы, добавлять клиентов, назначать программы |
| `admin` | всё, включая роли, блокировки, удаления пользователей и шаблонов |

Админ назначает роли в admin UI. Чтобы сделать тренера, админ переводит пользователя из
`client` в `coach`.

Админ может заблокировать пользователя. Заблокированный пользователь не проходит авторизацию
и не может пользоваться API. Удаление пользователя удаляет связанные программы, связи с
тренерами, приглашения и токены.

## Клиенты тренера

Тренер добавляет клиента через UI:

- по Telegram ID - лучший вариант, потому что ID не меняется;
- по username - можно заранее создать pending-приглашение.

Если клиент добавлен по username и позже входит через Telegram с тем же username, backend
связывает pending-приглашение с реальным пользователем. Username в Telegram может измениться,
поэтому после первого входа лучше ориентироваться на Telegram ID.

## Dev-вход

Для локальной разработки без Telegram можно включить:

```env
ENABLE_DEV_AUTH=true
```

Тогда на `/app` доступен dev-login. В production оставляй:

```env
ENABLE_DEV_AUTH=false
```

Demo-пользователи seed-данных:

- `1001` - админ/тренер;
- `2001` - клиент;
- `2002` - клиент.

## API

Основные страницы:

- `/app` - Telegram Mini App;
- `/admin` - admin UI;
- `/docs` - Swagger UI;
- `/health` - healthcheck.

Основные API-группы:

- `/api/v1/auth/*` - Telegram/dev login, refresh, logout;
- `/api/v1/me` - текущий пользователь и профиль;
- `/api/v1/programs/*` - упражнения, шаблоны, клиенты тренера;
- `/api/v1/workouts/*` - тренировка на сегодня, подходы, история;
- `/api/v1/notifications/*` - настройки и уведомления;
- `/api/v1/admin/*` - админские пользователи, платежи, уведомления, шаблоны;
- `/api/v1/billing/*` - mock-billing API.

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

Запустить все проверки вручную:

```bash
pre-commit run --all-files
pytest tests -q
```

`pre-commit` запускает:

- базовые проверки YAML/TOML, trailing whitespace, merge conflict markers;
- `ruff --fix` для lint и автоисправлений;
- `ruff-format` для форматирования;
- `mypy` для backend-пакета `app`.

Отдельные `isort`, `black` и `flake8` не запускаются: их функции закрывает Ruff
(`I` rules для импортов, lint rules для flake8-подобных проверок, `ruff-format`
для black-совместимого форматирования).

## CI

GitHub Actions workflow находится в `.github/workflows/ci.yml`.

CI запускается на:

- push в `main` или `master`;
- pull request.

CI делает:

- установку backend и bot зависимостей;
- `pre-commit run --all-files --show-diff-on-failure`;
- `pytest tests -q`.

## Миграции

Backend использует Alembic. В Docker backend стартует через entrypoint, который применяет
миграции перед запуском приложения.

Если нужно выполнить миграции вручную внутри backend-контейнера:

```bash
docker compose exec backend alembic upgrade head
```

## Безопасность

- Не коммить `.env`.
- Используй сильный `SECRET_KEY`.
- В production держи `ENABLE_DEV_AUTH=false`.
- Первый админ должен быть задан через `ADMIN_TELEGRAM_USER_IDS`.
- Для Telegram Mini App используй только HTTPS `FRONTEND_BASE_URL`.
