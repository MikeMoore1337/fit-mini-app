# FitMiniApp

Production-ready scaffold for a Telegram Mini App with:
- Telegram auth via `initData`
- JWT access/refresh tokens
- Alembic migrations
- workout program builder for self and coach mode
- recomposition goal
- mock billing and subscription activation
- notification queue + Telegram delivery worker
- simple admin panel
- pytest tests

## Main services
- `backend` - FastAPI API + Mini App pages
- `bot` - aiogram bot with `/start` and Mini App button
- `worker` - sends queued Telegram notifications and processes reminders
- `db` - PostgreSQL

## Quick start
```bash
cp .env.example .env
# fill BOT_TOKEN / TELEGRAM_BOT_TOKEN if you want real Telegram delivery
docker compose up --build
```

Then open:
- Mini App: `http://localhost:8000/app`
- Admin panel: `http://localhost:8000/admin`
- Swagger: `http://localhost:8000/docs`

## First run
Backend container automatically runs:
```bash
alembic upgrade head
```
Then it seeds:
- exercises
- demo coach `1001`
- demo clients `2001`, `2002`
- plans: Free, Premium, Coach
- public demo template

## Auth modes
### Development
By default `ENABLE_DEV_AUTH=true`.
You can log in from the UI with a debug Telegram ID.

### Telegram production auth
Frontend can call:
- `POST /api/v1/auth/telegram/init`

Request body:
```json
{
  "init_data": "query_id=...&user=...&hash=..."
}
```
Server verifies hash using Telegram spec and creates user profile.

## Billing flow
Implemented mock provider:
1. `GET /api/v1/billing/plans`
2. `POST /api/v1/billing/checkout`
3. receive `checkout_id`
4. finish payment with `POST /api/v1/billing/mock/complete/{checkout_id}`
5. subscription becomes active

## Notifications
Notification worker checks queued records and sends Telegram messages.
When a program is assigned, workout reminders are scheduled.

## Admin panel
`/admin` shows:
- users
- clients/coaches
- templates
- subscriptions
- payments
- notifications

Admin endpoints require a coach user.
In dev mode use debug user `1001`.

## Tests
Run locally:
```bash
cd backend
pytest -q
```

Covered scenarios:
- dev auth and token issuance
- creating template and assigning to self
- workout set logging rules
- mock billing activation

## Important note
This is a strong production scaffold, not a finished commercial app. Before a real public launch, still review:
- data protection and privacy policy
- payment provider integration for your jurisdiction
- rate limiting / WAF / backups / secrets management
- CI/CD and environment separation


## Каталог упражнений
- Тренер и админ могут создавать новые упражнения через Mini App в блоке `Каталог упражнений`.
- Обычные пользователи видят упражнения в конструкторе программ, но не могут создавать новые.
- API для создания: `POST /api/v1/programs/exercises`.
