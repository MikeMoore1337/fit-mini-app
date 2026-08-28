# Порядок выполнения release backlog v42

## Completed

`00-76`, включая `69B`, `73A`, `74A` и предшествующие буквенные подзадачи, а также
owner-selected Telegram tasks `103-105`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
76A Pre-human adversarial negative и destructive testing gate [CURRENT, NOT STARTED]
```

Tasks `75C` и `76` завершены после owner screenshot review. Task `76A` назначена текущей, но не
реализуется в completion run `76`. Её pre-human adversarial QA начинается только отдельным запуском
после проверки Preconditions; production baseline остаётся `DESIGN_V2_1` с bounded Pulse pilot.

Conditional release sequence:

```text
75 [COMPLETED] -> 75A Rethink audit [COMPLETED] -> START_RETHINK_EXPLORATION
  KEEP -> 76 [COMPLETED] -> 76A [CURRENT] -> 77 -> 78 -> 79
  EVOLVE -> bounded remediation -> 76 [COMPLETED]
  RETHINK -> 75B exploration [COMPLETED] -> 75C pilot [COMPLETED] -> 76 [COMPLETED]
```

Task `76A` назначена текущей, но не выполняется автоматически в completion-сессии `76`.
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

Task `106` не меняет current task `76A` и порядок `76A-101`. Её implementation запускается только
отдельным решением владельца.
