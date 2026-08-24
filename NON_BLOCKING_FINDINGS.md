# Реестр non-blocking findings

Этот файл — единый tracked source of truth для всех findings с severity `MEDIUM` и `LOW`,
обнаруженных в любых backlog tasks, review, QA, audit, release gate или вне формализованного
backlog.

`MEDIUM/LOW` не блокируют завершение текущей task и сами по себе не расширяют её scope. Реестр
нужен, чтобы проблема не потерялась после финального сообщения, очистки `.artifacts/` или смены
сессии.

## Обязательный процесс

1. Каждый новый `MEDIUM/LOW` получает стабильный ID. Сохраняй существующий canonical finding ID;
   если его нет, используй `NBF-YYYYMMDD-<TASK_OR_AREA>-NN`.
2. Primary agent текущей task добавляет или обновляет запись **до commit и финального отчёта**, в
   том же логическом изменении, в котором finding был обнаружен. Это обязательно и для finding,
   исправленного локально в той же task.
3. Reviewer и QA остаются read-only: они возвращают primary agent данные, достаточные для записи в
   этот файл. Ответ в чате или отчёт только в `.artifacts/` не считаются долговременной фиксацией.
4. Запись не удаляется после исправления. Обновляются status, route, verification и дата. Duplicate
   ссылается на canonical ID.
5. Route в будущую task не является скрытым разрешением расширить её scope. Finding становится
   scope целевой task только после явного включения ID и acceptance criteria в task либо решения
   владельца.
6. Evidence может ссылаться на `.artifacts/`, но описание, impact и route в этом файле должны быть
   понятны без временного артефакта. Не переносить сюда secrets, personal data, raw support text,
   exploit payloads или другие чувствительные audit details.
7. Перед завершением любой task primary agent проверяет реестр: новые findings добавлены, закрытые
   обновлены, route указывает на существующую task, а финальный отчёт перечисляет затронутые IDs.

## Поля и статусы

Каждая запись содержит:

- ID и текущую severity;
- status: `OPEN`, `ROUTED`, `FIXED`, `ACCEPTED_RISK`, `INVALID`, `DUPLICATE` или `SUPERSEDED`;
- источник: task/review/QA/audit и, после commit, hash либо устойчивый tracked path;
- краткие scenario, impact и минимальное направление исправления;
- route/owner decision;
- verification и дату последнего обновления.

Если finding переклассифицирован, сохрани исходную severity в примечании и укажи новый blocking
ID/status. `ACCEPTED_RISK` требует явного решения владельца; отсутствие времени или scope им не
является.

## Текущий реестр

Начальная инвентаризация выполнена 2026-08-23 по tracked backlog, Git history и доступным локальным
audit-артефактам. В неё включены только findings, для которых удалось подтвердить ID, severity и
содержание без догадок.

| ID | Severity | Status | Краткое описание | Source / verification | Route | Updated |
| --- | --- | --- | --- | --- | --- | --- |
| `F46B-03` | `MEDIUM` | `FIXED` | Account export не включал часть nutrition/profile data. | Audit `46B`; закрыт `codex-backlog/tasks/done/46c4-account-export-browser-privacy-remediation.md`. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-23 |
| `F46B-04` | `MEDIUM` | `FIXED` | Persistent food draft переживал logout/account deletion на shared device. | Audit `46B`; закрыт `codex-backlog/tasks/done/46c4-account-export-browser-privacy-remediation.md`. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-23 |
| `F46B-05` | `MEDIUM` | `FIXED` | Отсутствовал согласованный общий HTTP request-body limit. | Audit `46B`; закрыт `codex-backlog/tasks/done/46c5-http-limits-safe-logging-remediation.md`. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-23 |
| `F46B-06` | `MEDIUM` | `FIXED` | Exception/worker logging не гарантировал PII minimization. | Audit `46B`; emission path закрыт `codex-backlog/tasks/done/46c5-http-limits-safe-logging-remediation.md`. | Retention относится к `F46B-08`. | 2026-08-23 |
| `F46B-07` | `MEDIUM` | `FIXED` | Same-day measurement read-then-insert допускал race и uncontrolled error. | Audit `46B`; закрыт `codex-backlog/tasks/done/46c2-measurement-state-concurrency-remediation.md`. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-23 |
| `F46B-08` | `MEDIUM` | `ROUTED` | Не определён полный retention/deletion lifecycle для audit events, logs и backups. | Audit `46B/46B1`; code/policy gap подтверждён, external operator controls не проверялись. | `codex-backlog/tasks/78-production-operational-readiness.md`: explicit retention/access/restore acceptance и owner decisions. | 2026-08-23 |
| `F46B-09` | `LOW` | `ROUTED` | SQLite account deletion мог оставлять nutrition orphans из-за выключенного FK enforcement; production PostgreSQL regression отдельно не доказан. | Audit `46B/46B1`; SQLite boundary подтверждён, PostgreSQL deletion probe не выполнен. | `codex-backlog/tasks/79-final-integrated-release-audit.md`: SQLite/PostgreSQL account-deletion regression. | 2026-08-23 |
| `R59-004` | `MEDIUM` | `FIXED` | После возврата из historical workout строка нужной revision исключалась из последовательной keyboard navigation из-за `tabIndex=-1`. | Independent review task `59`; исправлено в `AssignedProgramDetails` и подтверждено targeted recheck, unit и Playwright-проверками. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-23 |
| `NBF-20260824-63-01` | `LOW` | `FIXED` | Действие точной подстановки веса могло оставаться доступным после завершения всех рабочих подходов, хотя изменять уже нечего. | Independent review task `63`; `TodayWorkout` теперь передаёт действие только при наличии незавершённых рабочих подходов, targeted component/e2e recheck. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-24 |
| `NBF-20260824-64-01` | `MEDIUM` | `FIXED` | Transactional notification показывал `created_at` как локальное время, хотя поле хранится в MSK и могло искажать время пользователя в другом timezone. | Independent review task `64`; UI использует уже нормализованный для пользователя `scheduled_for`, добавлен targeted unit regression. | История сохраняется; повторно не открывать без regression evidence. | 2026-08-24 |

## Ограничение начальной инвентаризации

Историческая task `49` подтверждает, что её review находил неидентифицированные `MEDIUM/LOW`
сценарии, но сами IDs, reproduction и финальный отчёт не были сохранены в tracked-файлах или
доступных audit-артефактах. Восстанавливать их по предположениям нельзя. Это известный пробел
исторической трассируемости; обязательный процесс выше предотвращает его повторение.
