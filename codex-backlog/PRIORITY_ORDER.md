# Порядок выполнения release backlog v41

## Completed

`00-75B`, включая `69B`, `73A`, `74A` и предшествующие буквенные подзадачи, а также
owner-selected Telegram tasks `103-105`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
75C Перенос выбранных Pulse-концепций в текущий production UI [CURRENT, NOT STARTED]
```

Task `75B` завершена после owner screenshot review. Владелец выбрал `SELECT_DIRECTION_PULSE` только
как перенос chart/dock/card-artwork/motion концепций поверх текущего UI. Task `75C` назначена текущей,
но не реализуется в completion run `75B`. До pilot и отдельного owner checkpoint production baseline
остаётся `DESIGN_V2_1`.

Conditional release sequence:

```text
75 [COMPLETED] -> 75A Rethink audit [COMPLETED] -> START_RETHINK_EXPLORATION
  KEEP -> 76 -> 76A -> 77 -> 78 -> 79
  EVOLVE -> bounded remediation -> 76
  RETHINK -> 75B exploration [COMPLETED] -> 75C bounded current-UI pilot -> owner checkpoint -> 76
```

Task `75C` назначена текущей, но не выполняется автоматически в completion-сессии `75B`.
Trigger-gated tasks сохраняют собственные gates. Никакая task не запускает следующую автоматически.

## Последовательность после `79`

После release gate использовать task ID как предпочтительный порядок:

```text
80 -> 81 -> 82 -> 83 -> 84 -> 85 -> 86
-> 87 -> 88 -> 89 -> 90A -> 90B -> 91
-> independently gated 92A / 92B
-> 93 AI-assisted XLSX/CSV/TXT/DOCX program import
-> 94A -> owner Go/Narrow Go -> 94B
-> 95A -> 95B -> 96 -> 97 -> 98
-> 99A -> 99B -> 99C
-> 100A -> 100B
-> 101 private progress photos without AI/body analysis
```

Единый AI-assisted import и food-photo стоят после основного AI-блока. Billing/монетизация,
перевод и фотографии прогресса оставлены в самом конце. Анализ фото тела отсутствует. Каждая
стрелка дополнительно требует Trigger, dependency и отдельного owner decision; umbrella-файлы
отдельно не выполняются.

## Owner-selected pending вне основной последовательности

```text
106 Landing: Telegram Mini App, поддержка и новостной канал
    [TASK CREATED, IMPLEMENTATION NOT STARTED]
```

Task `106` не меняет current task `76` и порядок `76-101`. Её implementation запускается только
отдельным решением владельца.
