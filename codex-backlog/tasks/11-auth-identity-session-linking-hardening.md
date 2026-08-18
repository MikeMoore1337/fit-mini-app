# TASK 11. Identity, session и account-linking security hardening

- Фаза: **Auth foundation**
- Приоритет: **11/93**
- Зависит от: `10`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$security-engineer`, `$backend-engineer`, `$qa-engineer`

## Цель

Довести существующие identity/session/linking mechanics до безопасного multi-provider foundation без второй auth-системы.

## In scope

### Identity model

Переиспользовать existing `AuthIdentity`.

Цель:

```text
Internal Account
├── Telegram
├── Google
├── Yandex
├── VK
└── Apple (optional)
```

Сохранить uniqueness provider+subject и user+provider согласно фактической модели.

### No implicit email merge

Не объединять аккаунты автоматически по совпавшему email, даже verified.

Если identity уже принадлежит другому account:

- не переносить;
- не merge histories;
- controlled conflict;
- audit event.

Account merge - отдельная future feature.

### Linking

Сохранить/усилить:

- authenticated target;
- short-lived one-time action token;
- provider binding;
- replay protection;
- ownership conflict;
- audit;
- Telegram bot/deep-link linking.

### Session

Проверить/исправить:

- access expiry;
- refresh expiry/rotation/replay/revocation;
- logout;
- blocked account;
- HttpOnly/Secure/SameSite/path;
- no-store;
- reload/multi-tab behavior.

Refresh token не переносить в localStorage.

### Safe continuation

Централизовать allowlisted internal `next` минимум для:

```text
/app
/coach
/admin
/join/<safe-token>
```

Запретить external, scheme-relative и encoded open redirects.

### Browser-facing error contract

Нормализовать:

- unavailable;
- cancel/denied;
- invalid/expired state;
- conflict;
- blocked;
- network/provider failure.

Не возвращать raw exception/token/code/secret.

### Root boundary

Future Root остаётся основан на verified Telegram identity из `ADMIN_TELEGRAM_USER_IDS`.

Linking не должен позволять перенести Root authority или получить его через arbitrary `telegram_user_id`.

Если audit рекомендует auth-method/step-up для root-sensitive operations, добавить только минимальный reusable security hook; Admin UX остаётся в later tasks.

### Migration compatibility

Сохранить legacy Telegram users и consistency `telegram_user_id` + Telegram AuthIdentity. Не создавать duplicates при backfill/migration.

## Out of scope

Не делать `/login` UI, provider registration, account merge, Email auth или capability/Admin redesign.

## Проверки

New/returning identity, concurrent first login, conflict, Telegram legacy user, valid/expired/replayed link, blocked account, refresh lifecycle, logout, cookie policy, safe-next attacks, Root transfer negative cases.

## Done when

Один internal account безопасно поддерживает несколько identities; silent email merge отсутствует; linking/session/redirect безопасны и совместимы с будущим Root/Admin.

## Рекомендуемый commit

`feat(auth): harden identities sessions and account linking`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: только профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: изменения, ключевые файлы, migrations/config, реально запущенные проверки, manual provider setup, ограничения и commit hash.
