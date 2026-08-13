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
VK ID     https://app.your-fitness-coach.ru/api/v1/auth/oauth/vk/callback
Apple     https://app.your-fitness-coach.ru/api/v1/auth/oauth/apple/callback
```

Configure credentials through the matching variables in `.env.example`.

OAuth discovery and token exchange use `OAUTH_HTTP_TIMEOUT_SECONDS` (15 seconds
by default) and deliberately ignore ambient proxy environment settings so that
OAuth secrets and authorization codes stay on a direct provider connection. A
`ConnectTimeout` in `oauth_login_failed` means the backend container could not
establish that direct outbound HTTPS connection; it does not indicate a
refresh-cookie or callback URL problem. Verify DNS and HTTPS connectivity from
the backend container before increasing the timeout further.

`OAUTH_FORCE_IPV4=true` is the safe default for deployments whose DNS resolver
returns both address families while Docker has no working IPv6 route. It binds
OAuth clients to IPv4 without pinning provider IP addresses, so DNS rotation and
TLS hostname verification continue to work. Set it to `false` only when the
container has a verified IPv6 route or runs in an IPv6-only environment.

When the server's direct route to a provider is blocked or unreliable, configure
an operator-controlled proxy only for OAuth with `OAUTH_PROXY_URL`. For an SSH
dynamic SOCKS tunnel running on the Docker host, use
`socks5://host.docker.internal:1081`; the Compose backend service resolves that
hostname to the host gateway. Do not use an untrusted public proxy: it handles
the OAuth authorization code and client secret. An explicit OAuth proxy takes
precedence over `OAUTH_FORCE_IPV4`.

The SSH tunnel must listen on the Docker host gateway (normally `172.17.0.1`),
not `127.0.0.1`, so the backend container can reach it while the port remains
unreachable from the public internet. Create a dedicated unprivileged account
and SSH key for the tunnel, restrict that key on the egress host, and run the
tunnel under a supervised system service. The tunnel should not require an
interactive password at runtime.

- Telegram: create Web Login credentials in BotFather and allow the frontend
  origin plus the callback URL.
- Google: create a Web OAuth client and request only `openid profile email`.
- Yandex: create an application for third-party user authorization and allow
  the `login:info` and `login:email` scopes.
- VK ID: create a Web application in the VK ID business console, add the exact
  callback URL above, and set its application ID as `VK_OAUTH_CLIENT_ID`. The
  backend implements VK ID OAuth 2.1 with PKCE (S256), requests only the
  `email` scope, and performs the code exchange and `user_info` request on the
  server. A VK client secret is not sent or required by this flow.
- Apple: use a Services ID for the client ID. `APPLE_OAUTH_CLIENT_SECRET` is the
  signed client-secret JWT generated with the Apple private key; rotate it
  before its configured expiry.

Never put provider secrets in frontend variables or commit them to Git.

## Explicit account linking

Logging in with a new provider does not merge accounts by matching email. An
email address returned by Google, Yandex or Apple is not sufficient proof that
an existing Telegram profile belongs to the same person.

Link an additional login method only from the already authenticated account:

1. First sign in to the account whose training history must be preserved. For
   a profile created by the Telegram bot, open the Mini App in Telegram and go
   to **Profile → Login methods**.
2. Choose **Link Telegram**, **Link Google**, **Link Yandex**, **Link VK ID** or
   **Link Apple**.
3. Complete the provider confirmation within 10 minutes.
4. Return to the profile and confirm that both login methods are marked as
   linked.

For Telegram, the browser creates a one-time bot deep link. For Google, Yandex,
VK ID and Apple, the application creates a one-time OAuth link. The token is
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
