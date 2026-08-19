# TASK 46C.1. Root/Admin/Trainer authorization remediation

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C.1/93 — первая implementation task umbrella 46C**
- Зависит от: `46B1`, owner-approved umbrella `46C`
- Canonical findings: `F46B-01`, `F46B-02`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$commercial-product-builder`, `$solution-architect`, `$security-engineer`, `$privacy-engineer`, `$backend-engineer`, `$frontend-engineer`, `$python-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Закрыть подтверждённые privilege/cross-user defects: сделать Root, Admin и Trainer независимыми
server-side capabilities и убрать недопустимый доступ Admin к trainer/client data.

## Owner-approved contract

- Только verified Root назначает и снимает Admin.
- Root нельзя понизить, заблокировать или удалить, включая self-delete.
- Admin и Trainer — независимые capabilities.
- Admin без Trainer не получает Coach workspace.
- Admin без active trainer-client relation не получает доступ к приватным тренировкам, питанию,
  замерам и прогрессу другого пользователя.
- Notification bodies пользователей не возвращаются обычному Admin.

## Scope

1. На каждом admin role/status/delete boundary проверять actor capability и protected target
   server-side; UI visibility не является защитой.
2. Admin grant/revoke разрешить только `require_root_admin` с повторной проверкой verified Root
   identity из server-configured source.
3. Любые role/status/delete mutations над Root и Root self-delete должны завершаться безопасным
   отказом без изменения данных.
4. Назначение/снятие Admin не должно автоматически назначать/снимать Trainer.
5. `require_coach` и Coach routes не должны принимать Admin без Trainer.
6. Удалить blanket `is_admin` arbitrary-target bypass из nutrition/program/measurement/progress и
   других trainer-domain services. Доступ к client data требует active relation.
7. Обычный Admin notification list возвращает только минимальные operational metadata без title,
   body, comment preview или другого user content. Более широкая capability не вводится в этой task.
8. Сохранить Personal functionality для Trainer/Admin и сочетание Trainer+Admin как две независимые
   capabilities.

## Compatibility и данные

- Новая DB schema по умолчанию не требуется: текущие `is_admin` и `is_coach` уже независимы.
- Не переписывать исторические role/audit records без отдельной доказанной необходимости.
- Legacy tests/workflows, закрепляющие Admin-as-Trainer или arbitrary-client access, должны быть
  заменены на owner-approved negative contract, а не сохранены как compatibility behavior.
- Если фактический code path требует migration, остановиться до её создания и показать минимальную
  безопасную migration/rollback стратегию владельцу.

## Targeted regression

- Delegated Admin не назначает/снимает Admin и не меняет Root role/status/account.
- Verified Root выполняет только разрешённые admin-management actions.
- Root self-delete невозможен.
- Admin without Trainer получает `403` на Coach workspace/API.
- Admin without active relation не читает и не меняет private nutrition/program/measurement/progress.
- Trainer+Admin сохраняет отдельные Personal/Coach/Admin contexts.
- Unrelated/former/revoked trainer negative paths не регрессируют.
- Admin notification responses не содержат user bodies/previews.
- Audit events фиксируют разрешённые/значимые privileged mutations без sensitive payloads.

Запустить только профильные backend API/security tests, затронутые frontend auth/route tests,
typecheck/lint и generated API drift, если контракт изменился. Полный suite без необходимости не
запускать.

## Documentation

Синхронизировать durable admin/auth documentation с независимой capability matrix и Root-only
delegation. Не публиковать raw audit scenarios.

## STOP CONDITION

После закрытия только `F46B-01` и `F46B-02`, targeted review, `git diff` и отдельного commit
остановиться. Не начинать `46C.2`.

## Рекомендуемый commit

`fix(auth): enforce root and admin capability boundaries`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. В финале указать findings, changed files,
migrations/config, реально выполненные checks, review result, ограничения и commit hash.
