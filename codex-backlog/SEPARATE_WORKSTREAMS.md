# Separate workstreams

## Before release, parallel

### Telegram core bot

Самостоятельный вложенный backlog:

```text
codex-backlog/telegram-core-release-backlog/
```

Scope: one bot runtime, TMA entry, account linking regression, support/feedback, BotFather commands and product notification delivery. No news/channel/digest.

Main task `64` owns the canonical notification model and preferences. Telegram task `03` owns the delivery adapter and bot-facing deep links. If either is implemented first, run a narrow compatibility check after the other.

## After release

Separate archive:

```text
your-fitness-coach-post-release-priority-backlog-v2.zip
```

It contains all deferred ideas in priority order: photos, program import, PWA, monetization, AI beta, news, translation and later integrations.
