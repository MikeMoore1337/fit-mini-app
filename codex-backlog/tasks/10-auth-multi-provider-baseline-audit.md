# TASK 10. Multi-provider authentication - read-only implementation audit

- Фаза: **Auth baseline**
- Приоритет: **10/93**
- Зависит от: `00`, `03`, `05`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$security-engineer`, `$backend-engineer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Провести отдельный read-only аудит существующей authentication/identity реализации до её доработки.

На момент подготовки backlog в `feature/yfc-platform-v2` multi-provider auth уже существует. Не считать, что OAuth нужно строить с нуля.

## In scope

### Observed baseline - обязательно перепроверить

На ветке при подготовке task наблюдались:

- `ENABLE_WEB_AUTH=true`;
- `ENABLE_EMAIL_AUTH=false`;
- Telegram Mini App auth через signed `initData`;
- browser OAuth/OIDC;
- Telegram browser OAuth;
- Google;
- Яндекс;
- VK ID;
- Apple как optional existing provider;
- JWT access + refresh;
- HttpOnly refresh cookie;
- `AuthIdentity`;
- OAuth account linking;
- Telegram linking;
- conflict protection;
- frontend `AuthGate`, provider buttons и linking UI.

Repository/Git/docs остаются source of truth.

### Audit matrix

Для каждого provider зафиксировать:

```text
web login
TMA login
linking
credentials
callback
state/PKCE/OIDC validation
stable subject
profile/email semantics
production status
tests
```

Обязательные Web providers:

- Telegram;
- Google;
- Яндекс;
- VK ID.

Apple не удалять автоматически. Email/password не включать только потому, что routes существуют.

### Routes/UX

Проверить:

- `/`;
- `/app`;
- `/coach`;
- `/admin`;
- `/join/...`;
- verify/reset;
- наличие отдельного `/login`;
- unauthenticated browser;
- TMA auto-auth;
- OAuth success/cancel/error;
- session restore/logout.

Подтвердить фактическое поведение текущего `AuthGate` и Landing CTA.

### Identity/linking

Проверить:

- `users`;
- `auth_identities`;
- provider+subject uniqueness;
- user+provider uniqueness;
- legacy `telegram_user_id`;
- new/returning OAuth user;
- Telegram/OAuth linking;
- conflict handling;
- audit events;
- linked-provider list.

Отдельно подтвердить, что совпадение email не приводит к silent account merge.

### Sessions/security

Проверить:

- access/refresh lifecycle;
- cookie flags;
- refresh rotation/revocation;
- blocked user;
- OAuth state/session;
- safe `next`;
- open redirect;
- provider errors;
- secrets/logging.

### Root implication

Проверить связь `ADMIN_TELEGRAM_USER_IDS` -> Telegram identity -> account.

Определить риски входа root-account через linked non-Telegram provider и риск переноса Root через linking. Ничего не менять на audit-task.

### Official docs

Перед conclusions сверить актуальные official docs Telegram, Google Identity, Yandex ID, VK ID и Apple, если он остаётся в production scope.

### Visual baseline

Сравнить current Landing, `AuthGate`, provider buttons, verify/reset и account linking UI.

Сформулировать требования к единому premium public shell после task `05` и final Landing task `73`.

## Out of scope

Не менять код/DB/config. Не создавать provider apps/credentials. Не менять Admin roles. Не добавлять account merge. Не включать email auth.

## Проверки

Проверить `.env.example`, backend auth routes/services/models, Telegram validation, OAuth adapters, refresh/session code, frontend `AuthProvider`/`AuthGate`, provider buttons, linking UI, Landing CTA и auth tests.

Raw outputs - только `.artifacts/codex-audits/auth/`.

## Done when

Есть точная current-state карта, P0-P3 findings и implementation plan для `10-12`. Product code не менялся.

## Рекомендуемый commit

`docs(auth): audit multi-provider authentication`

## Процесс и отчёт

Это **read-only audit**.

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Product code, migrations и tracked docs/config не менять.

Рабочие материалы складывать только в `.artifacts/codex-audits/auth/` и не коммитить.

Не переходить к следующему task.

В финальном отчёте: current auth architecture, provider/route matrix, P0-P3 findings, identity/session/linking risks, Root/Telegram implications, UX gaps и рекомендации для tasks `10-12`.
