# FitMiniApp

Telegram Mini App для тренировок: профиль пользователя, конструктор программ, режим тренера, каталог упражнений, тренировка на сегодня, подписки, уведомления и админ-панель.

## Что уже есть

- Авторизация через Telegram Mini App (`initData`)
- Dev-вход для локальной отладки, если включён `ENABLE_DEV_AUTH=true`
- Профиль пользователя
- Конструктор программ:
  - для себя
  - для клиента
- Каталог упражнений
- Тренировка на сегодня
- Отметка подходов, отмена последнего подхода
- Прогрессия по прошлой тренировке
- Уведомления
- Подписки с mock-billing
- Админ-панель

## Стек

- **Backend**: FastAPI
- **База данных**: PostgreSQL
- **Бот**: Telegram Bot API
- **Frontend**: HTML/CSS/JS
- **Инфраструктура**: Docker Compose

## Структура проекта

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    static/
      index.html
      admin.html
      app.js
      styles.css
  alembic/
  Dockerfile
  worker-entrypoint.sh
  docker-entrypoint.sh

bot/
  ...

docker-compose.yml
.env
README.md
```

## Настройка `.env`

Минимальный пример:

```env
APP_ENV=prod
APP_NAME=FitMiniApp
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false

SECRET_KEY=CHANGE_ME
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

DATABASE_URL=postgresql+psycopg://fitminiapp:STRONG_PASSWORD@db:5432/fitminiapp

ENABLE_DEV_AUTH=false

FRONTEND_BASE_URL=https://your-domain.com
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_BOT_USERNAME=your_bot_username

PAYMENT_PROVIDER=mock
PAYMENT_PUBLIC_URL=https://your-domain.com

WORKER_POLL_SECONDS=10
```

## Важно по продакшену

Перед выкладкой обязательно:

- заменить `SECRET_KEY`
- использовать сильный пароль БД
- выключить `ENABLE_DEV_AUTH`
- проверить, что в интерфейсе не осталось dev-элементов
- запускать Mini App через Telegram, иначе `initData` будет пустым

## Локальный запуск

```bash
docker compose down
docker compose up --build
```

Открыть:

- Mini App: `http://127.0.0.1:8000/app`
- Админка: `http://127.0.0.1:8000/admin`
- Swagger: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/health`

## Важные URL API

Если маршруты подключены правильно, должны работать:

- `GET /api/v1/public/config`
- `POST /api/v1/auth/dev-login`
- `POST /api/v1/auth/telegram/init`
- `GET /api/v1/me`
- `PATCH /api/v1/me/profile`
- `GET /api/v1/programs/exercises`
- `POST /api/v1/programs/exercises`
- `POST /api/v1/programs/templates`
- `GET /api/v1/programs/templates/mine`
- `GET /api/v1/programs/clients`
- `GET /api/v1/workouts/today`
- `POST /api/v1/workouts/{id}/start`
- `POST /api/v1/workouts/{id}/complete`
- `POST /api/v1/workouts/{id}/sets`
- `DELETE /api/v1/workouts/{id}/exercises/{exercise_id}/last-set`
- `GET /api/v1/billing/plans`
- `GET /api/v1/billing/subscription`
- `POST /api/v1/billing/checkout`
- `POST /api/v1/billing/mock/complete/{checkout_id}`
- `GET /api/v1/notifications/settings`
- `PATCH /api/v1/notifications/settings`
- `GET /api/v1/notifications`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/payments`
- `GET /api/v1/admin/notifications`
- `GET /api/v1/admin/templates`

## Почему Mini App может быть пустым

Самая частая причина - нет авторизации.

Признаки:

- статус `Не авторизован`
- в логах сообщение про отсутствие `initData`
- не загружаются упражнения, шаблоны, клиенты, тренировка

Что делать:

- либо открыть Mini App из Telegram
- либо временно включить dev-вход для локального теста:

```env
APP_ENV=dev
ENABLE_DEV_AUTH=true
```

После этого пересобрать контейнеры.