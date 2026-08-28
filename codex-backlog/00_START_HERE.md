# Your Fitness Coach - backlog первого публичного релиза v14

Backlog использует resource-aware lifecycle. Завершённые задачи архивируются в `tasks/done/` и остаются доступными для чтения.

## Текущее состояние

- tasks `00-78`, включая буквенные подзадачи, `69B`, `73A` и `74A`, а также owner-selected tasks
  `103-106` подтверждены как завершённые;
- завершённые task-файлы перенесены в `tasks/done/` без переименования;
- `DESIGN_V2_1` с owner-approved bounded Pulse pilot остаётся current production baseline;
- task `77` закрыта по explicit owner acceptance отсутствия real-user sessions и residual risk;
- task `78` завершила production operational readiness после owner approval и подтверждения
  внешних operational controls;
- task `79` назначена current final release gate, но ещё не начата;
- owner-selected tasks `107-108` созданы вне основной очереди и не являются current.

## Текущая задача

```text
79-final-integrated-release-audit.md [CURRENT NOT STARTED]
```

Не запускать заново `00-78`, `74A` и `103-106`. Назначение `79` не запускает её реализацию, а
создание owner-selected tasks `107-108` не разрешает их implementation, external actions или
юридически значимые выводы без профильной проверки.

## Design alternatives flow

```text
49A  targeted brief/current-state delta [done]
49B  exactly three cross-surface directions + renders [done]
49B1 current Design V2 UI consistency + mobile-first normalization [done]
49C  compare normalized V2/A/B/C + owner selection [done]

KEEP_V2_UNCHANGED
  -> skip 49D-49F
  -> 49G closure

V2.1 / A / B / C / explicit hybrid
  -> 49D final responsive specification
  -> owner approval
  -> 49E production-realistic pilot
  -> owner manual test
  -> 49F final owner approval
  -> 49G conditional rollout + backlog alignment

49G -> 50A mobile/TMA quality foundation [done]
50-74A feature/release/hardening tasks [done]
75 performance/motion hardening [COMPLETED]
75A design/UX/UI/motion Rethink audit [COMPLETED]
  -> KEEP: continue to 76
  -> EVOLVE: bounded remediation
  -> RETHINK [SELECTED]: 75B isolated exploration + owner selection
75B product-wide visual + motion directions [COMPLETED, SELECT_DIRECTION_PULSE]
  -> 75C bounded production pilot [COMPLETED]
  -> 76 audit [COMPLETED] -> 76A adversarial gate [COMPLETED]
  -> 77 real-user gate [CLOSED BY OWNER ACCEPTED RESIDUAL RISK]
  -> 78 production readiness [COMPLETED] -> 79 final release gate [CURRENT, NOT STARTED]
103-106 owner-selected Telegram flow/Landing tasks [done]
107 Scheduled regression + private Allure reports [OWNER-SELECTED PENDING; NOT CURRENT]
108 Russian law compliance audit + continuous legal gate [OWNER-SELECTED PENDING; NOT CURRENT]
```

## Что изменено в v14

- Task `78` завершила production readiness, restore drill и operator contract после owner approval.
- Current task назначена `79`; её реализация не начата, release/post-release порядок не изменён.
- Добавлена owner-selected pending task `107` для scheduled regression и закрытых Allure-отчётов
  на `allure.your-fitness-coach.ru` с явным access/retention owner contract.
- Добавлена owner-selected pending task `108` для полного аудита соответствия законодательству РФ,
  покрытия всех существующих tasks и непрерывного gate для ещё не созданных будущих задач.
- Resource-aware review policy `BLOCKER/HIGH only` сохранена; `MEDIUM/LOW` синхронизируются в
  `bugs/FINDINGS.md`.

Подробности: `TASK_EXECUTION_LIFECYCLE.md`, `SKILL_ASSIGNMENT_MATRIX.md`, `ACTIVE_DESIGN_SOURCE.md`.
