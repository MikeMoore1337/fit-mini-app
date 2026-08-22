# TASK 04. Финальная E2E-проверка Telegram core

- Фаза: **Release gate**
- Зависит от: `03`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$qa-engineer`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$observability-engineer`, `$accessibility-engineer`, `$release-manager`, `$code-reviewer`, `$technical-writer`
- Основная роль: **`integration-release`**
- Контракт роли: `.agents/roles/integration-release.md`

## Matrix

- one token/service/polling owner;
- `/start link_<token>` conflict/expiry;
- signed TMA initData;
- browser login proxy-tunnel/TLS;
- `/app`, menu button and deep links;
- support categories, cancel/TTL, owner reply, abuse limit;
- commands/BotFather checklist;
- timezone/settings;
- all product notification categories, opt-out/quiet hours/dedupe;
- blocked user/429/retry;
- no secrets/raw initData/support text in logs;
- no legacy support service;
- no news/channel/digest handlers or commands;
- accessibility/readability of commands, inline keyboards, errors and TMA entry on mobile.

## Output

Checks actually run, real Telegram-client checks vs mocks, config/migration changes, unresolved limitations, owner actions and commit hash.

## Done when

The single bot safely opens the app, supports users and delivers product notifications for the release.
