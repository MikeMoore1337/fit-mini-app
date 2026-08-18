# Authentication master brief

## Required Web providers
- Telegram
- Google
- Yandex
- VK ID

Apple is an existing optional provider.
Email/password remains behind `ENABLE_EMAIL_AUTH`.

## Target

```text
Web: Landing -> /login -> configured provider -> Internal Account
TMA: signed initData -> automatic auth -> same Internal Account
```

## Rules
- evolve existing AuthIdentity/linking/session architecture;
- no email auto-merge;
- safe internal continuation only;
- no provider secrets client-side;
- Root stays bound to trusted Telegram identity;
- `/login` is noindex;
- Landing/Login use one premium public visual language.

## Tasks
08 audit -> 09 hardening -> 10 provider readiness -> 11 premium login -> 52 visual sync -> 55 release gate.
