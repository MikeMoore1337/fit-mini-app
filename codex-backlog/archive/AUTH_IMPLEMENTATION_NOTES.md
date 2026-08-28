# Authentication implementation notes

Observed on `feature/yfc-platform-v2` while preparing this backlog.
Observed branch head: `89d2f185e1275744209192edd01883058231cf6d`.

Re-check repository at execution time.

## Already present

### Config
`.env.example` includes Web/Email flags, Telegram/Google/Yandex/VK/Apple OAuth settings and OAuth network/proxy options.

### Backend
- Telegram Mini App `initData` auth.
- Generic browser OAuth start/callback.
- Telegram browser OIDC.
- Google OIDC.
- Yandex OAuth + profile.
- VK ID custom PKCE flow.
- Apple OIDC.
- JWT access/refresh.
- `AuthIdentity`.
- OAuth linking.
- Telegram linking.
- conflict/audit handling.

### Frontend
- `AuthProvider`.
- `AuthGate`.
- OAuth provider buttons.
- automatic TMA auth.
- Account "Способы входа".
- verify/reset auxiliary pages.

## Main gap

There is no canonical dedicated `/login`.

Unauthenticated protected routes currently render auth via `AuthGate`, and Landing points to app entry.

Target:

```text
Landing -> /login -> Telegram / Google / Yandex / VK -> safe product route
```

TMA remains automatic.

## Important safety properties
- preserve one internal account + multiple provider identities;
- no silent email merge;
- no open redirect;
- no Root transfer via account linking;
- no secrets in frontend;
- `/login` noindex.

## Design
`/login` must use the same public premium design system as the new Landing. Final Landing task must QA/update auth shell too.
