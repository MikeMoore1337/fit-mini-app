# Telegram core backlog до первого релиза

Используется только существующий `@your_fitness_coach_bot` и один `TELEGRAM_BOT_TOKEN`.

## Scope

- TMA entry and account linking regression;
- one polling runtime;
- support/feedback;
- clear commands and BotFather setup;
- product notification delivery/deep links/preferences;
- final E2E.

## Not in this archive

- news channel;
- news ingestion/generation/images/moderation;
- weekly news digest;
- English channel;
- AI Coach.

These are post-release tasks.

## Order

```text
00 -> 01 -> 02 -> 03 -> 04
```

Task `03` integrates with main release task `64`. Workstreams may run in either order, followed by a narrow compatibility regression.

## Skills

Использовать актуальный набор `your-fitness-coach-agents-v3.zip`.
