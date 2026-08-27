# Порядок выполнения release backlog v39

## Completed

`00-75A`, включая `69B`, `73A` и предшествующие буквенные подзадачи, task `74A`, а также owner-selected
tasks `88-90`.
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
Owner-selected tasks `88-90` завершены вне этой последовательности. Umbrella `91` отдельно не
выполняется, а `91A` не назначена без собственного Trigger, dependency и owner decision.
Trigger-gated tasks сохраняют собственные gates. Никакая task не запускает следующую автоматически.
