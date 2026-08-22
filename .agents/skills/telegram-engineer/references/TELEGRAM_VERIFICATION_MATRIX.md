# Telegram verification matrix

Используй только разделы, относящиеся к текущей задаче. Это не требование запускать все проверки для
каждого изменения.

## 1. Current-state audit

Зафиксируй:

- фактическую версию Aiogram и поддерживаемую Bot API version;
- transport: polling или webhook;
- process/service, владеющий token;
- routers/middlewares/FSM storage/jobs;
- auth/linking/TMA/login flows;
- commands/menu/deep links;
- notification and timezone flows;
- channel ids/permissions/config;
- test seams и manual-only operations;
- legacy services/tokens, которые ещё нельзя удалить.

Красные флаги:

- два polling process для одного token;
- token используется в нескольких compose services без явного ownership;
- generic handler зарегистрирован раньше security-sensitive `/start` payload;
- browser OAuth proxy settings переиспользованы для Bot API без обоснования;
- production bot/channel smoke запускается обычным CI;
- handler напрямую работает с БД и Bot API без тестируемой service boundary.

## 2. Runtime и startup

Проверить:

- один polling owner или корректный webhook ownership;
- startup/shutdown idempotency;
- lock/conflict behavior;
- allowed updates;
- transient Telegram failure не вызывает restart loop;
- metadata/channel preflight не блокирует весь runtime без необходимости;
- graceful cancellation активных jobs;
- duplicate scheduler startup исключён;
- health endpoint не раскрывает token/channel/admin ids.

Сценарии:

- нормальный startup;
- Telegram недоступен;
- invalid token/config;
- polling conflict;
- duplicate job worker;
- shutdown во время send/retry;
- restart с pending FSM/scheduled item.

## 3. Commands, menu и deep links

Проверить:

- canonical command definitions едины для runtime/help/checklist;
- `setMyCommands` идемпотентен;
- private/default/admin scopes корректны;
- language-specific commands не меняют authorization;
- public descriptions понятны и укладываются в актуальные ограничения;
- `/start` payload priority закреплён tests;
- unknown payload/command безопасен;
- links используют production config;
- `next`/path/start parameter allowlisted и bounded;
- raw payload не показывается пользователю.

Минимальная матрица `/start`:

- без payload;
- valid link token;
- expired link token;
- linking conflict;
- support payload;
- news/digest payload;
- unknown payload;
- repeated payload;
- existing linked user;
- unlinked user.

## 4. Telegram Mini App

### Auth

- backend получает raw `initData`;
- подпись проверяется server-side;
- freshness/expiry policy тестируется;
- bot binding и replay policy определены;
- `initDataUnsafe` не используется как trusted identity;
- frontend `user_id` игнорируется как authorization input;
- raw `initData` отсутствует в logs/errors/analytics;
- valid TMA launch не перенаправляется на browser `/login`;
- invalid launch не создаёт account/session.

### Platform adapter

Дополнительно использовать `../../../references/MOBILE_TMA_ACCEPTANCE_MATRIX.md`. Проверить:

- `ready`/initialization и `expand` без state reset;
- `isActive`/foreground restore;
- BackButton lifecycle и duplicate handlers;
- theme change;
- `viewportHeight`/`viewportStableHeight` и `viewportChanged`;
- keyboard-open state;
- `safeAreaInset`/`contentSafeAreaInset` и соответствующие change events;
- old/unsupported client fallback;
- close confirmation только для действительно несохранённого состояния;
- navigation history;
- deep-link context;
- reload/reopen;
- light/dark and contrast;
- 360/390/430 widths, touch/`hover: none`, Telegram Android/iOS separately and representative Telegram Desktop.

### Continuity

- один backend/account для Web/TMA;
- locale/theme preference sync;
- active workout/form state policy;
- no second API/client implementation;
- browser OAuth и TMA auth regression separate.

## 5. FSM, support и feedback

Проверить:

- start flow/category selection;
- privacy warning;
- text/photo/document allowlist;
- unsupported media;
- empty/oversized content;
- `/cancel`;
- TTL/expiry;
- restart policy;
- free text outside FSM;
- duplicate user message;
- user rate limit/abuse;
- admin allowlist;
- admin reply routing;
- no cross-user mix-up;
- blocked/deleted user;
- user blocks bot during reply;
- audit event without private text;
- no generic trainer-client messenger.

Admin reply action должен содержать server-side binding к конкретному support case/user. Reply-to message
или визуальная близость сообщений не являются достаточной binding.

## 6. Callback и moderation

Проверить:

- callback actor/role;
- resource id;
- exact revision/version;
- action allowlist;
- server-side state transition;
- idempotency;
- stale callback;
- double click;
- replay after restart;
- callback from another user/chat;
- forged callback data;
- expired draft;
- regeneration invalidates approval;
- audit actor/time/action/revision.

## 7. Channel configuration

Проверить:

- channel id/username только из config allowlist;
- bot membership;
- minimum admin rights;
- posting permission;
- edit/delete own messages only if feature uses them;
- test/dry-run channel separation;
- permission loss classification;
- channel migration/username change policy;
- no arbitrary destination from callback/API;
- no automatic production test post.

Manual owner smoke:

- controlled test message in test/non-production channel;
- store returned message id;
- edit/delete only when explicitly requested;
- verify final rendering on mobile;
- confirm no secrets in screenshot/log.

## 8. Publication and scheduling

Invariant:

```text
source -> draft revision -> optional media revision -> explicit approval -> publish exact revision
```

Проверить:

- unapproved cannot publish;
- approved exact revision publishes;
- regeneration cannot reuse old approval;
- idempotent publish key;
- retry sends same content hash;
- schedule timezone/DST;
- schedule edited/cancelled/expired;
- max-frequency product rule;
- no requirement to publish daily;
- final message id/timestamp/hash persisted;
- safe entities/escaping;
- text/caption limits from current API;
- image missing/invalid;
- concise caption/text-only fallback;
- no accidental multi-message spam;
- revoked channel rights;
- 429 `retry_after`;
- transient 5xx/network;
- permanent error and owner alert;
- silent/notification policy.

## 9. Broadcast and subscription

Проверить:

- default off;
- explicit opt-in copy includes frequency;
- duplicate subscribe;
- one-tap unsubscribe;
- `/news_off`/`/unsubscribe` aliases if supported;
- unsubscribe immediately before queued send;
- product notifications unaffected;
- idempotency `user + digest`;
- bounded send rate;
- `429 retry_after`;
- blocked/deactivated chat;
- no infinite retry;
- large broadcast spread;
- no silent re-enable;
- bot cannot initiate contact with never-contacted user;
- export/delete treatment of preference.

## 10. Security, privacy and retention

Проверить отсутствие в logs/telemetry/errors:

- token;
- raw `initData`;
- support/private message content;
- subscriber/admin lists;
- source article body;
- temporary documents/images;
- full callback payload with private identifiers.

Проверить:

- SSRF/redirect/DNS/content-type/size/time limits for source fetching;
- safe HTML/entities;
- file/media allowlist;
- secret-safe `.env.example`;
- draft/source/image retention;
- cleanup jobs;
- account export/delete;
- backup/restore scope;
- manual recovery не обходит approval.

## 11. Testing layers

### Unit

- helpers, command definitions, payload parsing;
- state transitions;
- formatting/escaping;
- rate-limit/backoff decisions;
- permission/policy functions.

### Dispatcher routing

Feed synthetic updates to `Dispatcher` with mocked dependencies. Не запускай polling для handler routing tests.

### Integration

- DB state/FSM storage;
- scheduler;
- subscriptions;
- idempotency;
- auth/linking;
- TMA backend validation;
- channel publishing adapter with fake Bot API.

### Browser/TMA

- platform adapter;
- navigation/back;
- safe areas/viewport;
- auth failure;
- responsive/a11y;
- console/network errors.

### Opt-in live

- test bot/channel only;
- explicit marker and credentials;
- minimal messages;
- no quota exhaustion simulation;
- no automatic production BotFather/channel changes.

## 12. Official sources to re-check

Use current official documentation at implementation time:

- Telegram Bot API: https://core.telegram.org/bots/api
- Telegram bots overview/features/FAQ: https://core.telegram.org/bots
- Telegram Mini Apps: https://core.telegram.org/bots/webapps
- Telegram bot developer terms: https://telegram.org/tos/bot-developers
- Aiogram latest docs: https://docs.aiogram.dev/en/latest/

Do not copy numeric limits from this checklist into code without confirming the currently used API/version.
