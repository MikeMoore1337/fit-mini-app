# TASK_EXECUTION_LIFECYCLE v1

Этот файл определяет обязательный полный lifecycle одной backlog task.

Фраза владельца `выполни полный task lifecycle` означает: прочитать этот файл и пройти применимые стадии ниже в рамках одной Codex-сессии, не переходя к следующей task.

## 0. Вход и обязательные контракты

Перед работой:

1. Прочитать корневой `AGENTS.md`.
2. Прочитать `GLOBAL_RULES.md` текущего backlog.
3. Прочитать текущую task.
4. Прочитать файл основной роли из `.agents/roles/`, указанный в task.
5. Открыть только реально применимые `Рекомендуемые skills` из task.
6. Проверить фактическое состояние кода, docs, migrations, tests и текущей ветки/worktree.
7. Не повторять полный аудит репозитория, если task этого не требует.

Фраза `Все предыдущие tasks считаются выполненными` означает только sequencing prerequisite. Она НЕ:

- проходит owner checkpoint или owner approval;
- создаёт отсутствующий Trigger/evidence;
- подтверждает внешний сервис, секрет, токен, платёж, BotFather или production action;
- отменяет conditional/skip condition текущей task;
- разрешает считать непроверенное действие выполненным.

Если текущая task требует явного решения владельца или внешнего действия, использовать только реально предоставленное подтверждение.

Если сама task явно фиксирует, что её запуск владельцем является предварительным bounded approval на конкретный обратимый внешний Bot API action, это считается реально предоставленным подтверждением только в перечисленных task границах. Такое разрешение нельзя расширять на token rotation, deploy, BotFather-only settings, proxy changes или другие внешние действия.

## 1. Основная роль

Основная роль берётся только из строки `Основная роль` текущей task.

- `researcher` - ограниченное read-only исследование и evidence.
- `implementer` - scoped production implementation одной task.
- `orchestrator` - координация сложной/cross-cutting task и делегирование естественных подзадач.
- `independent-reviewer` - независимый аудит готового результата/diff, по умолчанию без production-изменений.
- `qa-verifier` - риск-ориентированная проверка поведения.
- `integration-release` - integration/release convergence и только необходимые integration fixes.

Роль не расширяет scope task. Task и repository contracts имеют приоритет над общими возможностями роли.

## 2. Предварительное исследование

Для `implementer`, `orchestrator` или `integration-release` использовать отдельного read-only subagent в роли `researcher` только если есть реальная неизвестность, которую выгодно исследовать отдельно:

- существующий flow/архитектурная граница;
- модели/migrations/API/contracts;
- auth/RBAC/privacy boundary;
- Telegram/platform behavior;
- fitness/data semantics;
- места изменения и regression surface.

Не создавать researcher для очевидной локальной task.

Researcher возвращает компактные факты, релевантные файлы, зависимости, риски и существующие проверки. Production-код researcher не меняет.

Если текущий режим Codex не поддерживает настоящих subagents, выполнить этот этап последовательно в той же сессии как отдельный read-only pass и явно не смешивать его с реализацией.

## 3. Выполнение основной task

Выполнить task согласно её основной роли.

### Если роль `implementer`

- сделать минимальный законченный vertical slice;
- использовать существующие contracts/components/services;
- не проводить побочный refactor;
- добавить/обновить необходимые tests;
- обновить docs при изменении долговечного поведения;
- закрыть применимые loading/empty/error/retry/mobile/TMA/a11y/security состояния.

### Если роль `researcher`

- не писать production-код;
- вернуть evidence, вывод, Go/No-Go/defer или план, который требует task;
- не превращать discovery в скрытую реализацию.

### Если роль `orchestrator`

- определить естественные независимые подзадачи;
- использовать минимальное число subagents;
- write-работу делегировать `implementer`, если task действительно требует production changes;
- не разрешать двум write-agents одновременно менять одну область/contract;
- определить convergence и критерии завершения task.

### Если роль `independent-reviewer`

- проверить фактический результат относительно task и repository contracts;
- не подменять owner decision;
- production-код по умолчанию не менять;
- если сама task явно требует исправить подтверждённые findings, передать узкие исправления отдельному `implementer` pass/subagent и затем перепроверить их.

### Если роль `qa-verifier`

- проверить фактическое поведение и риски;
- production-код не менять;
- подтверждённые дефекты исправляет `implementer`, после чего QA перепроверяет их.

### Если роль `integration-release`

- интегрировать только готовые/разрешённые изменения;
- не расширять feature scope;
- исправлять только integration blockers;
- выполнять более широкие проверки только по фактическому integration risk.

## 4. Самопроверка перед независимой проверкой

Если task изменила tracked production/test/config/docs artifacts:

1. Сопоставить результат с каждым acceptance/done-when пунктом.
2. Запустить только профильные targeted checks по `AGENTS.md`, `GLOBAL_RULES.md` и task.
3. Не запускать полный suite без необходимости или прямого требования.
4. Проверить provisional `git diff` на лишний scope, secrets, migrations и config changes.
5. Не считать task завершённой только потому, что код собирается.

## 5. Independent review

После реализации code/config/data/UI behavior отдельный read-only subagent в роли `independent-reviewer` обязан проверить готовый diff.

Reviewer:

- читает task, diff и релевантные contracts;
- использует `$code-reviewer` и только нужные профильные skills;
- проверяет correctness, security/privacy, data integrity, compatibility, races/retry/idempotency, критичные tests, UX/a11y/performance по поверхности task;
- возвращает findings с severity и минимальным вариантом исправления;
- для каждого `MEDIUM/LOW` возвращает registry-ready ID, scenario/impact, source, route и
  verification для корневого `NON_BLOCKING_FINDINGS.md`;
- production-код не исправляет.

Повторный reviewer не нужен для чистой read-only research/decision task, если `independent-reviewer` уже является основной ролью и task не создаёт implementation diff.

Если настоящие subagents недоступны, сделать отдельный review pass в той же сессии. В финальном отчёте честно указать, что это был отдельный pass, а не независимый subagent.

## 6. Исправление review findings

Основной агент или отдельный `implementer` исправляет только подтверждённые findings текущего scope.

- Не исправлять вкусовые замечания без production impact.
- Не расширять task ради соседнего технического долга.
- Finding, требующий owner decision, нового scope или внешнего действия, вынести как blocker/follow-up.
- После исправления повторить затронутые targeted checks.
- Blocker/high finding должен быть перепроверен reviewer до финализации.

## 7. QA verification

Для task, изменяющей пользовательское, API, data, auth, platform или runtime behavior, после review/fixes провести отдельный read-only QA pass в роли `qa-verifier`.

Проверять по риску:

- happy path;
- invalid/empty/boundary;
- auth/ownership/permissions;
- duplicate/retry/idempotency;
- concurrency, если применимо;
- network/external dependency failure;
- timezone/date/DST;
- stale/backward-compatible data;
- loading/empty/error/recovery;
- mobile/responsive/TMA;
- accessibility;
- migration/rollback compatibility, если применимо;
- regression вокруг изменённой подсистемы.

QA не обязан запускать полный suite. Использовать минимальный набор проверок, дающий достаточную уверенность.

Для чистой research/docs/decision task QA можно пропустить, если task сама его не требует.

Если настоящие subagents недоступны, сделать отдельный QA pass в той же сессии и явно указать это в отчёте.

## 8. Исправление QA findings

Подтверждённые дефекты текущего scope исправляет `implementer`.

После исправления:

1. повторить failed/affected проверки;
2. для существенного дефекта повторить соответствующий QA scenario;
3. не закрывать task при непроверенном blocker.

## 9. Финальная проверка и Git

Только после implementation/review/QA, если они применимы:

1. Запустить финальный минимально необходимый набор профильных checks.
2. Не заявлять checks, которые фактически не запускались.
3. Проверить итоговый `git diff`.
4. Убедиться, что нет изменений вне scope и случайных generated/secrets artifacts.
5. Проверить migrations/config/dependency changes.
6. Добавить или обновить каждый новый/изменённый `MEDIUM/LOW` в корневом
   `NON_BLOCKING_FINDINGS.md`, включая исправленные в этой task; закрытые записи не удалять.
7. Создать один логический commit только после успешного lifecycle, если есть tracked changes.
8. Для read-only/no-code/defer/No-Go outcome без findings и tracked artifacts commit не создавать;
   новый registry entry сам является tracked artifact и должен быть commit-нут.
9. Не выполнять merge/deploy/production/external owner actions без явного разрешения.
10. Не переходить к следующей task.

## 10. Финальный отчёт

Финальный отчёт должен кратко содержать:

- основную роль и фактически использованные subagent roles;
- что реализовано/исследовано/проверено;
- reused architecture;
- ключевые изменённые файлы;
- migrations/config/external-service changes;
- exact checks и их результат;
- reviewer findings и статус исправления;
- QA findings и статус перепроверки;
- что не удалось проверить;
- owner/manual checks, если нужны;
- оставшиеся риски/blockers/follow-ups;
- затронутые `NON_BLOCKING_FINDINGS.md` IDs и statuses;
- commit hash либо явный `no commit`.

Нельзя утверждать, что independent review, QA, real-user check, real Telegram check, provider verification или production validation выполнены, если они фактически не выполнялись.

## 11. Stop conditions

Остановить именно текущую task и не переходить дальше, если:

- нужен явный owner checkpoint/approval;
- отсутствует обязательный Trigger/evidence;
- нужен секрет/credential или внешнее действие владельца;
- есть противоречие требований, которое нельзя безопасно разрешить по source of truth;
- остаётся blocker, который невозможно исправить в scope task.

В этом случае вернуть точный blocker и уже выполненную часть lifecycle.
