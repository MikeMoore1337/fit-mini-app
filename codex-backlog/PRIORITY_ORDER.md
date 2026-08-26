# Порядок выполнения release backlog v34

## Completed

`00-73A`, включая `69B` и предшествующие буквенные подзадачи, а также owner-selected tasks `88-89A`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
90 Еженедельный Telegram-дайджест с отдельным opt-in [PENDING]
```

Task `90` назначена текущей в owner-selected Telegram news потоке, но не реализуется в completion
run task `89A`. В основной release-последовательности первой pending task остаётся `74A`, после неё:

```text
74 Cross-product responsive, accessibility и states hardening
```

Task `73A` завершена после owner approval. Remaining release sequence остаётся
`74A -> 74 -> 75 -> 76 -> 76A -> 77 -> 78 -> 79`. Owner-selected tasks `88-89A` завершены вне этой
последовательности; `90` только назначена текущей внутри Telegram news потока. Trigger-gated tasks
сохраняют собственные gates. Никакая task не запускает следующую автоматически.
