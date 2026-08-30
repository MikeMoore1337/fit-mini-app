# Порядок выполнения release backlog v50

## Completed

`00-80`, включая `69B`, `73A`, `74A` и предшествующие буквенные подзадачи, а также
owner-selected Telegram tasks `103-106`.
Task-файлы находятся в локальном owner-only `tasks/done/`.

## Current

```text
113A Owner UX Stabilization [COMPLETED, OWNER ACCEPTED]
  -> 114 Nutrition search/barcode production regression [COMPLETED, OWNER APPROVED, RELEASE AUTHORIZED]
  -> 115A UX audit + IA + compactness/disclosure prototype/spec [CURRENT, NOT STARTED]
```

Tasks `75C`, `76` и `76A` завершены после применимых owner checkpoints. Task `76A` получила
adversarial verdict `PASS`, закрыла все `BLOCKER/HIGH` и архивирована. В task `77` реальные сессии
не проводились; владелец явно принял отсутствие real-user validation и residual risk, после чего
task архивирована. Task `78` завершила production readiness после owner approval и подтверждения
external controls. Tasks `79-80` завершены и архивированы после owner approval. History rewrite
`master` запустил намеренный automatic production workflow; владелец подтвердил это поведение как
feature, а точный trigger contract закреплён в обязательной документации. Task `113` завершила
branch normalization. Task `113A` выпущена в production, принята владельцем и архивирована;
production baseline остаётся `DESIGN_V2_1`. Task `114` завершена и архивирована после owner
approval; Task `115A` обозначена следующей, но её lifecycle не начат.

Conditional release sequence:

```text
75 [COMPLETED] -> 75A Rethink audit [COMPLETED] -> START_RETHINK_EXPLORATION
  KEEP -> 76 [COMPLETED] -> 76A [COMPLETED] -> 77 [COMPLETED] -> 78 [COMPLETED] -> 79 [COMPLETED]
  EVOLVE -> bounded remediation -> 76 [COMPLETED]
  RETHINK -> 75B exploration [COMPLETED] -> 75C pilot [COMPLETED] -> 76 [COMPLETED]
```

Release/smoke Task `113A` завершены, а точная owner-команда
`Stabilization принята. Можно переходить к Task 114.` получена `2026-08-30`. Task `114` затем
запущена отдельной командой, завершена и принята владельцем; Task `115A` не запускается автоматически.
Trigger-gated tasks сохраняют собственные gates. Никакая task не запускает следующую автоматически.

## Текущий UX-reset cycle

Canonical owner-driven порядок:

```text
113 [COMPLETED] -> 113A [COMPLETED, OWNER ACCEPTED] -> 114 [COMPLETED, OWNER APPROVED] -> 115A [CURRENT, NOT STARTED] -> OWNER APPROVAL
-> 116 -> 117 -> 118 -> 119 -> 120A -> 120B -> 120C -> 120D
-> 121 -> 122 -> 123 -> 81 -> 82 -> 84 -> 124A
-> OWNER RELEASE APPROVAL -> dev -> master -> production deployment
-> 124B -> 124C only if BLOCKER/HIGH
```

Task `115B` отсутствует. Реальные пользовательские сессии выполняются на deployed production build
в Task `124B`, а не блокируют implementation `116+`. Tasks `85`, `110`, `111` остаются вне critical
path и входят в `124A` только по отдельному owner решению. Каждая стрелка сохраняет Trigger,
dependency и owner gate своей task; следующая task автоматически не запускается.

Owner-selected task `106` завершена и архивирована после owner screenshot approval. Она не изменила
основную release-последовательность; после закрытия `114` current/not started task — `115A`.

Owner-selected task `107` создана для scheduled regression и закрытых Allure-отчётов на
`allure.your-fitness-coach.ru`. Она не является current, не меняет UX-reset critical path и требует
отдельного owner запуска плюс explicit approval перед DNS/Cloudflare/hosting actions.

Owner-selected task `108` создана для комплексного аудита соответствия законодательству РФ и
непрерывного legal-impact gate, охватывающего все текущие и любые будущие задачи. Она не является
current, не меняет UX-reset critical path и требует отдельного owner запуска через `product-lawyer` и
`$ru-legal-risk`; итоговый baseline/gate обязательно проверяет профильный российский юрист, а
`LEGAL_COUNSEL_REQUIRED` выделяет дополнительные спорные вопросы.

Owner-selected tasks `109-111` созданы вне основной очереди: `109` — factual Landing offer и
conversion story, `110` — private custom avatar desktop/mobile, `111` — Progress bento dashboard и
периоды `1/7/30/90/365/custom`. Они не меняют current `115A` или UX-reset critical path, не запускаются
автоматически и требуют отдельных owner запусков; для UI до commit действует screenshot approval.

Owner-selected task `112` завершена и архивирована вне основной очереди. Она добавила проверяемый
current-stack zero-downtime deployment contract. После explicit owner approval production revision
`194cf036` успешно развёрнута через `single-slot` fallback с bounded downtime из-за фактической
capacity constrained VPS; это не доказательство production blue/green zero observed downtime.
Task `112` не изменяет текущий UX-reset cycle. Task `114` завершена отдельно; Task `115A` не
запускается автоматически.
