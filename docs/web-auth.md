# Browser authentication rollout

Browser authentication is additive. Telegram Mini App `initData` login remains
enabled independently of `ENABLE_WEB_AUTH` and all OAuth credentials.

## Safe production order

1. Deploy the database migrations and application with `ENABLE_WEB_AUTH=false`
   and `ENABLE_EMAIL_AUTH=false`.
2. Confirm `/health/ready` and the existing Telegram Mini App login.
3. Configure only the OAuth providers that are ready.
4. Register the exact callback URLs listed below in provider consoles.
5. Set `ENABLE_WEB_AUTH=true`, keep `ENABLE_EMAIL_AUTH=false`, and restart the
   backend. Email/password endpoints and forms remain unavailable.

The production deployment script enforces the two values from step 5 in the
existing server `.env` before validating Compose and starting containers. It
does not alter OAuth credentials or any other secrets.

The public config exposes only providers that have both a client ID and client
secret. A partially configured provider never appears on the login screen.

## Common application URL

Production frontend and API are expected on the same origin:

```text
https://app.your-fitness-coach.ru
```

Keep `FRONTEND_BASE_URL` equal to that origin. Browser sessions use same-origin
HttpOnly refresh cookies; no CORS configuration is required.
The public landing page is served at `https://your-fitness-coach.ru`; it may use
the same backend, but login, invitations and OAuth callbacks should stay on the
canonical `app` origin.

## Provider callbacks

Register these exact HTTPS redirect URLs:

```text
Telegram  https://app.your-fitness-coach.ru/api/v1/auth/oauth/telegram/callback
Google    https://app.your-fitness-coach.ru/api/v1/auth/oauth/google/callback
Yandex    https://app.your-fitness-coach.ru/api/v1/auth/oauth/yandex/callback
Apple     https://app.your-fitness-coach.ru/api/v1/auth/oauth/apple/callback
```

Configure credentials through the matching variables in `.env.example`.

OAuth discovery and token exchange use `OAUTH_HTTP_TIMEOUT_SECONDS` (15 seconds
by default). A `ConnectTimeout` in `oauth_login_failed` means the backend
container could not establish an outbound HTTPS connection to the provider; it
does not indicate a refresh-cookie or callback URL problem. Verify DNS and HTTPS
connectivity from the backend container before increasing the timeout further.

- Telegram: create Web Login credentials in BotFather and allow the frontend
  origin plus the callback URL.
- Google: create a Web OAuth client and request only `openid profile email`.
- Yandex: create an application for third-party user authorization and allow
  the `login:info` and `login:email` scopes.
- Apple: use a Services ID for the client ID. `APPLE_OAUTH_CLIENT_SECRET` is the
  signed client-secret JWT generated with the Apple private key; rotate it
  before its configured expiry.

Never put provider secrets in frontend variables or commit them to Git.

## Explicit account linking

Logging in with a new provider does not merge accounts by matching email. An
email address returned by Google, Yandex or Apple is not sufficient proof that
an existing Telegram profile belongs to the same person.

Link an additional login method only from the already authenticated account:

1. Open **Profile → Login methods** in the account whose training history must
   be preserved.
2. Choose **Link Telegram**, **Link Google**, **Link Yandex** or **Link Apple**.
3. Complete the provider confirmation within 10 minutes.
4. Return to the profile and confirm that both login methods are marked as
   linked.

For Telegram, the browser creates a one-time bot deep link. For Google, Yandex
and Apple, the application creates a one-time OAuth link. The token is
single-use, a newer token replaces the previous one, and a conflict consumes
the token without merging data. If the selected Telegram or OAuth identity is
already owned by another account, the operation is rejected and both accounts
remain unchanged. Resolving such a conflict requires a separate, audited
support procedure; there is no automatic data merge.

After a successful link, both login methods resolve to the same internal user
ID. Profile data, coach relationships, programs, workouts, nutrition records
and progress therefore remain identical in Telegram and the browser.

## Optional email/password authentication

Email/password registration is controlled independently by
`ENABLE_EMAIL_AUTH` and is disabled by default. Browser OAuth does not require
SMTP. If email authentication is enabled later, production startup rejects the
configuration unless `SMTP_HOST` and `SMTP_FROM_EMAIL` are set. Configure either
STARTTLS (normally port 587) or implicit TLS, not both. Email verification and
password reset links use `FRONTEND_BASE_URL`.
