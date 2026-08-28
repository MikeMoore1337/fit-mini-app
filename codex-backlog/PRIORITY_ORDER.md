# Порядок выполнения release backlog v49

## Completed

`00-80`, включая `69B`, `73A`, `74A` и предшествующие буквенные подзадачи, а также
owner-selected Telegram tasks `103-106`.
Task-файлы находятся в локальном owner-only `tasks/done/`.

## Current

```text
81 Опциональный hydration tracking в Nutrition [CURRENT, NOT STARTED]
```

Tasks `75C`, `76` и `76A` завершены после применимых owner checkpoints. Task `76A` получила
adversarial verdict `PASS`, закрыла все `BLOCKER/HIGH` и архивирована. В task `77` реальные сессии
не проводились; владелец явно принял отсутствие real-user validation и residual risk, после чего
task архивирована. Task `78` завершила production readiness после owner approval и подтверждения
external controls. Tasks `79-80` завершены и архивированы после owner approval. History rewrite
`master` запустил намеренный automatic production workflow; владелец подтвердил это поведение как
feature, а точный trigger contract закреплён в обязательной документации. Task `81` назначена
текущей, но её Trigger/реализация не запускались; production baseline остаётся `DESIGN_V2_1`.

Conditional release sequence:

```text
75 [COMPLETED] -> 75A Rethink audit [COMPLETED] -> START_RETHINK_EXPLORATION
  KEEP -> 76 [COMPLETED] -> 76A [COMPLETED] -> 77 [COMPLETED] -> 78 [COMPLETED] -> 79 [COMPLETED]
  EVOLVE -> bounded remediation -> 76 [COMPLETED]
  RETHINK -> 75B exploration [COMPLETED] -> 75C pilot [COMPLETED] -> 76 [COMPLETED]
```

Task `81` назначена текущей, но не выполняется автоматически в completion-сессии `79/80`.
Trigger-gated tasks сохраняют собственные gates. Никакая task не запускает следующую автоматически.

## Последовательность после `80`

После release gate использовать task ID как предпочтительный порядок:

```text
81 -> 82 -> 83 -> 84 -> 85 -> 86
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
основную release-последовательность; current task теперь `81`, далее сохраняется порядок `81-101`.

Owner-selected task `107` создана для scheduled regression и закрытых Allure-отчётов на
`allure.your-fitness-coach.ru`. Она не является current, не меняет порядок `81-101` и требует
отдельного owner запуска плюс explicit approval перед DNS/Cloudflare/hosting actions.

Owner-selected task `108` создана для комплексного аудита соответствия законодательству РФ и
непрерывного legal-impact gate, охватывающего все текущие и любые будущие задачи. Она не является
current, не меняет порядок `81-101` и требует отдельного owner запуска через `product-lawyer` и
`$ru-legal-risk`; итоговый baseline/gate обязательно проверяет профильный российский юрист, а
`LEGAL_COUNSEL_REQUIRED` выделяет дополнительные спорные вопросы.

Owner-selected tasks `109-111` созданы вне основной очереди: `109` — factual Landing offer и
conversion story, `110` — private custom avatar desktop/mobile, `111` — Progress bento dashboard и
периоды `1/7/30/90/365/custom`. Они не меняют current `81` или порядок `81-101`, не запускаются
автоматически и требуют отдельных owner запусков; для UI до commit действует screenshot approval.

Owner-selected task `112` завершена и архивирована вне основной очереди. Она добавила проверяемый
current-stack zero-downtime deployment contract, но не выполняла production rollout и не изменила
current `81`: следующей по основной pending-последовательности остаётся task `81`, затем `82` только
после её Trigger, completion и отдельного owner decision.
