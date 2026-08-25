# Порядок выполнения release backlog v30

## Completed

`00-73`, включая `69B` и предшествующие буквенные подзадачи, а также owner-selected task `88`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
89 Telegram-новости: изображения, revision-bound модерация и публикация [PENDING]
```

После завершения `89` в owner-selected Telegram news потоке:

```text
90 Еженедельный Telegram-дайджест с отдельным opt-in
```

Task `88` завершена по прямому owner decision вне remaining release sequence. Task `89` назначена
текущей, но не реализуется в completion run task `88`; `90` также не запускается. Remaining release
sequence `73A -> 74 -> 74A -> 75 -> 76 -> 76A -> 77 -> 78 -> 79` и остальные trigger-gated
post-release tasks сохраняют собственные gates. Никакая task не запускает следующую автоматически.
