# Browser authentication rollout

Browser authentication is additive. Telegram Mini App `initData` login remains
enabled independently of `ENABLE_WEB_AUTH` and all OAuth credentials.

## Safe production order

1. Deploy the database migrations and application with `ENABLE_WEB_AUTH=false`.
2. Confirm `/health/ready` and the existing Telegram Mini App login.
3. Configure SMTP and only the OAuth providers that are ready.
4. Register the exact callback URLs listed below in provider consoles.
5. Set `ENABLE_WEB_AUTH=true` and restart backend containers.

The public config exposes only providers that have both a client ID and client
secret. A partially configured provider never appears on the login screen.

## Common application URL

Production frontend and API are expected on the same origin:

```text
https://app.your-fitness-coach.ru
```

Keep `FRONTEND_BASE_URL` equal to that origin. Browser sessions use same-origin
HttpOnly refresh cookies; no CORS configuration is required.

## Provider callbacks

Register these exact HTTPS redirect URLs:

```text
Telegram  https://app.your-fitness-coach.ru/api/v1/auth/oauth/telegram/callback
Google    https://app.your-fitness-coach.ru/api/v1/auth/oauth/google/callback
Yandex    https://app.your-fitness-coach.ru/api/v1/auth/oauth/yandex/callback
Apple     https://app.your-fitness-coach.ru/api/v1/auth/oauth/apple/callback
```

Configure credentials through the matching variables in `.env.example`.

- Telegram: create Web Login credentials in BotFather and allow the frontend
  origin plus the callback URL.
- Google: create a Web OAuth client and request only `openid profile email`.
- Yandex: create an application for third-party user authorization and allow
  the `login:info` and `login:email` scopes.
- Apple: use a Services ID for the client ID. `APPLE_OAUTH_CLIENT_SECRET` is the
  signed client-secret JWT generated with the Apple private key; rotate it
  before its configured expiry.

Never put provider secrets in frontend variables or commit them to Git.

## SMTP requirement

Production startup rejects `ENABLE_WEB_AUTH=true` unless `SMTP_HOST` and
`SMTP_FROM_EMAIL` are set. Configure either STARTTLS (normally port 587) or
implicit TLS, not both. Email verification and password reset links use
`FRONTEND_BASE_URL`.
