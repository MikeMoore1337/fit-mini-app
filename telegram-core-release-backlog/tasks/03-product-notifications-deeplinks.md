# TASK 03. Доставка продуктовых уведомлений и deep links через основной бот

- Фаза: **Notifications / Bot integration**
- Зависит от: `02` и canonical notification contract main task `64`
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$telegram-engineer`, `$solution-architect`, `$backend-engineer`, `$python-engineer`, `$data-engineer`, `$security-engineer`, `$privacy-engineer`, `$platform-engineer`, `$observability-engineer`, `$accessibility-engineer`, `$qa-engineer`, `$code-reviewer`
- Основная роль: **`implementer`**
- Контракт роли: `.agents/roles/implementer.md`

## Цель

Подключить основной бот как delivery adapter единой системы уведомлений, не создавая второй scheduler/model/preferences store.

## In scope

- workout reminder;
- trainer comment;
- program changed/assigned;
- invitation/linking event;
- weekly review reminder;
- account/security messages where Telegram is allowed;
- stable TMA/Web deep links;
- quiet hours/timezone/preferences;
- dedupe/idempotency;
- blocked/deleted chat and retry/backoff;
- rate limit/429 `retry_after`;
- delivery status without raw content logs.

## Boundaries

- main task `64` owns event creation and preferences;
- this task owns Telegram serialization/delivery;
- support router cannot intercept callbacks/deep links;
- no news/digest subscription;
- no generic marketing broadcast;
- no trainer-client messenger.

## Checks

Each category on/off, quiet hours, stale event, duplicate worker, blocked user, wrong account, deep link target, TMA unavailable fallback, one polling owner.

## Done when

Product notifications arrive through the same bot predictably and respect user settings.

## Процесс

Не переходить к task `04`.
