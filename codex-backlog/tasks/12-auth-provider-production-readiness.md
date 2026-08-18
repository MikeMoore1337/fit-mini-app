# TASK 12. Telegram, Google, Yandex и VK authentication production readiness

- Фаза: **Auth providers**
- Приоритет: **12/93**
- Зависит от: `10`, `11`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$security-engineer`, `$backend-engineer`, `$qa-engineer`

## Цель

Довести существующие provider adapters до production readiness для обязательного Web-набора:

- Telegram;
- Google;
- Яндекс;
- VK ID.

Apple сохранить как optional existing provider, если он остаётся корректным.

## In scope

### Official contracts

Перед изменениями открыть актуальные official docs каждого provider и проверить endpoints/discovery, redirect URI, state/nonce/PKCE, scopes, stable subject, email semantics и branding requirements.

### Telegram Mini App

Сохранить signed `initData` validation:

- signature;
- auth_date/max age;
- stable user ID;
- no trust in `initDataUnsafe`;
- automatic TMA login.

### Telegram browser OAuth

Проверить current OIDC/browser adapter и callback. Если credentials отсутствуют, browser provider не должен притворяться рабочим; допустим `Открыть в Telegram`.

### Google

Проверить OIDC discovery/client/callback/state/nonce/scopes/`sub`/email_verified/error handling.

### Яндекс

Проверить authorization/token/profile endpoints, stable ID, scopes/email semantics и callback errors. Email не использовать как account key.

### VK ID

Проверить current official protocol, PKCE, state, device_id, token/user-info и callback payload variants. Не добавлять insecure fallback.

### Apple optional

Не делать обязательным Done, но не ломать/удалять существующий adapter без причины.

### Config

Server-only env:

```text
TELEGRAM_OAUTH_*
GOOGLE_OAUTH_*
YANDEX_OAUTH_*
VK_OAUTH_*
APPLE_OAUTH_* optional
```

`/public/config` отдаёт только available provider names.

Проверить existing timeout/IPv4/proxy options и не отключать TLS verification.

### Runbook

Добавить `docs/auth/provider-setup.md`:

- provider application setup;
- callback URLs;
- env vars;
- scopes;
- smoke check;
- safe disable.

Без реальных credentials.

Live provider smoke - opt-in; local CI не требует secrets.

## Out of scope

Не создавать credentials за пользователя, не коммитить secrets, не включать Email auth, не делать login redesign, не удалять Apple без причины, не ослаблять TLS/state/PKCE.

## Проверки

Configured/unconfigured, start, success mock, cancel, invalid state/claims, blocked user, timeout. TMA valid/invalid/stale initData. VK PKCE/state/device variants. Public config без secrets.

## Done when

Telegram/Google/Яндекс/VK production-ready по текущим official contracts; TMA auto-auth сохранён; provider absence безопасен; operator runbook готов.

## Рекомендуемый commit

`feat(auth): harden web and telegram auth providers`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: только профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: изменения, ключевые файлы, migrations/config, реально запущенные проверки, manual provider setup, ограничения и commit hash.
