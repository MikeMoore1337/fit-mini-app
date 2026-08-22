# Telegram core backlog - продолжение с task 02

Актуально для состояния проекта, в котором Telegram tasks `00` и `01` **уже выполнены**.

Этот пакет намеренно содержит только новые/актуализированные tasks:

```text
02 -> WAIT main 64 -> 03 -> WAIT main 72 -> 04
```

Исторические `00` и `01` не включены, чтобы Codex не мог случайно переисполнить или переиграть их результаты.

## Что можно делать сейчас

При основном backlog, выполненном до `49B1` включительно:

```text
Telegram 02
-> STOP
```

Task `02` можно запускать сейчас. Она использует текущую реализацию после уже выполненной task `01` как source of truth.

После выполнения main task `64`:

```text
Telegram 03
-> STOP / продолжить main backlog
```

После выполнения main task `72` и Telegram `03`:

```text
Telegram 04
```

## Максимальная автономность Codex

Task `02` должна автоматически через официальный Bot API, где среда и текущий Telegram client позволяют:

- синхронизировать bot name;
- About / short description;
- Description;
- profile photo;
- commands;
- Menu Button;
- выполнить identity guard через `getMe`;
- выполнить read-back verification;
- диагностировать BotFather-only flags через `getMe`.

Владелец вмешивается только для действительно owner-only действий: Main Mini App/Web Login, отдельных BotFather modes, splash/previews, secrets/deploy boundary или иных явно неавтоматизируемых шагов.

Не давать Codex доступ к личной Telegram Web-сессии ради кликов в BotFather.

## Не менять выполненные tasks 00/01

Если task `02-04` обнаруживает regression существующего single-bot/support contract, исправляется только конкретный подтверждённый дефект в рамках текущей task. Повторный аудит или перепроектирование `00/01` запрещены без отдельного owner decision.
