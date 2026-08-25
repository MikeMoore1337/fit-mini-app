# Порядок выполнения release backlog v31

## Completed

`00-73`, включая `69B` и предшествующие буквенные подзадачи, а также owner-selected tasks `88-89`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
89A Telegram-новости: финальная композиция поста и exact preview parity [PENDING]
```

После завершения `89A` в owner-selected Telegram news потоке:

```text
90 Еженедельный Telegram-дайджест с отдельным opt-in
```

Tasks `88-89` завершены по прямому owner decision вне remaining release sequence. Task `89A`
назначена текущей, но не реализуется в completion run task `89`; `90` также не запускается.
Remaining release sequence `73A -> 74 -> 74A -> 75 -> 76 -> 76A -> 77 -> 78 -> 79` и остальные
trigger-gated post-release tasks сохраняют собственные gates. Никакая task не запускает следующую
автоматически.
