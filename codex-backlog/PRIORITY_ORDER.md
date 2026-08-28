# Порядок выполнения release backlog v46

## Completed

`00-78`, включая `69B`, `73A`, `74A` и предшествующие буквенные подзадачи, а также
owner-selected Telegram tasks `103-106`.
Task-файлы находятся в `tasks/done/`.

## Current

```text
79 Финальный интегрированный audit, regression и go/no-go [CURRENT, NOT STARTED]
```

Tasks `75C`, `76` и `76A` завершены после применимых owner checkpoints. Task `76A` получила
adversarial verdict `PASS`, закрыла все `BLOCKER/HIGH` и архивирована. В task `77` реальные сессии
не проводились; владелец явно принял отсутствие real-user validation и residual risk, после чего
task архивирована. Task `78` завершила production readiness после owner approval и подтверждения
external controls. Task `79` назначена текущей, но не запущена; production baseline остаётся
`DESIGN_V2_1` с bounded Pulse pilot.

Conditional release sequence:

```text
75 [COMPLETED] -> 75A Rethink audit [COMPLETED] -> START_RETHINK_EXPLORATION
  KEEP -> 76 [COMPLETED] -> 76A [COMPLETED] -> 77 [COMPLETED] -> 78 [COMPLETED] -> 79 [CURRENT]
  EVOLVE -> bounded remediation -> 76 [COMPLETED]
  RETHINK -> 75B exploration [COMPLETED] -> 75C pilot [COMPLETED] -> 76 [COMPLETED]
```

Task `79` назначена текущей, но не выполняется автоматически в completion-сессии `78`.
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

Owner-selected task `106` завершена и архивирована после owner screenshot approval. Она не изменила
основную release-последовательность; current task теперь `79`, далее сохраняется порядок `79-101`.

Owner-selected task `107` создана для scheduled regression и закрытых Allure-отчётов на
`allure.your-fitness-coach.ru`. Она не является current, не меняет порядок `78-101` и требует
отдельного owner запуска плюс explicit approval перед DNS/Cloudflare/hosting actions.
