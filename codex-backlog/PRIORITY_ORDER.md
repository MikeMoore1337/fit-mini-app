# Порядок выполнения release backlog v40

## Completed

`00-75A`, включая `69B`, `73A`, `74A` и предшествующие буквенные подзадачи, а также
owner-selected Telegram tasks `103-105`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
75B Product-wide visual + motion directions и owner selection [CURRENT, PENDING]
```

Task `75A` завершена после owner screenshot approval. Владелец выбрал
`START_RETHINK_EXPLORATION`; task `75B` только назначена и не реализуется в completion run `75A`.
До owner selection, specification и pilot текущим production baseline остаётся `DESIGN_V2_1`.

Conditional release sequence:

```text
75 [COMPLETED] -> 75A Rethink audit [COMPLETED] -> START_RETHINK_EXPLORATION
  KEEP -> 76 -> 76A -> 77 -> 78 -> 79
  EVOLVE -> bounded remediation -> 76
  RETHINK -> 75B exploration + owner selection -> specification -> pilot/rollout/performance verification -> 76
```

Task `75B` назначена текущей, но не выполняется автоматически в completion-сессии `75A`.
Trigger-gated tasks сохраняют собственные gates. Никакая task не запускает следующую автоматически.

## Последовательность после `79`

После release gate использовать task ID как предпочтительный порядок:

```text
80 -> 81 -> 82 -> 83 -> 84 -> 85 -> 86 -> 87
-> 88 -> 89 -> 90 -> 91A -> 91B -> 92
-> independently gated 93A / 93B
-> 94A -> owner Go/Narrow Go -> 94B
-> 95 -> 96A -> 96B -> 97 -> 98 -> 99
-> 100A -> 100B -> 100C
-> 101A -> 101B
-> 102 private progress photos without AI/body analysis
```

Food-photo стоит после AI-блока. Billing/монетизация, перевод и фотографии прогресса оставлены в
самом конце. Анализ фото тела отсутствует. Каждая стрелка дополнительно требует Trigger, dependency
и отдельного owner decision; umbrella-файлы отдельно не выполняются.
