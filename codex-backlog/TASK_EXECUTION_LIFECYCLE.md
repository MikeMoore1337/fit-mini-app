# TASK_EXECUTION_LIFECYCLE v2 - resource-aware

Этот файл определяет полный lifecycle одной backlog task. Цель - сохранять production-качество без автоматического подключения всех ролей, skills и повторных аудитов.

Фраза владельца `полный task lifecycle` означает: пройти только те стадии и роли, которые явно применимы к текущей task, и остановиться после неё.

## 0. Контракты task имеют приоритет

Перед работой:

1. Прочитать корневой `AGENTS.md`.
2. Прочитать `GLOBAL_RULES.md` текущего backlog.
3. Прочитать только текущую task.
4. Прочитать файл `Основная роль` из `.agents/roles/`.
5. Открыть только `Рекомендуемые skills` текущей task.
6. `Условные skills` не открывать заранее. Подключать их только после проверки кода, если фактическая реализация действительно затронула указанный trigger.
7. Выполнять только `Дополнительные роли lifecycle`, явно указанные в task. Не строить автоматически цепочку `researcher -> reviewer -> QA` только потому, что такие роли существуют.
8. Проверить текущую ветку/worktree, существующий код, tests, migrations и релевантные docs.

Если task является resume незавершённой работы, сначала сохранить и классифицировать существующий незакоммиченный diff. Не reset/revert чужие или неидентифицированные изменения.

Фраза `Все предыдущие tasks считаются выполненными` означает только sequencing prerequisite. Она не проходит owner checkpoint, не создаёт Trigger/evidence, не даёт credentials и не разрешает production/external action.

## 1. Бюджет ролей и контекста

Для обычной task:

- один primary writer;
- один full independent review максимум, если он указан task;
- один QA pass максимум, если он указан task;
- researcher только при реальной неизвестности или если это основная/явно дополнительная роль;
- новые роли после review не подключаются ради `medium/low` finding;
- не перечитывать неизменившиеся skills/roles после каждого прохода;
- subagent получает task, релевантный diff/files, результаты checks и конкретный вопрос, а не весь backlog и рабочий журнал.

Для review/QA обычной feature-task использовать базовый skill роли и не более 1-2 дополнительных профильных skills за pass. Исключение - audit/release task, где task явно делит работу на независимые streams. В таком случае skills загружаются последовательно по stream, а не все сразу.

## 2. Предварительное исследование

Researcher нужен только если есть отдельная неизвестность, которую выгодно закрыть read-only:

- неясная архитектурная граница;
- неизвестный data/API/auth contract;
- внешний platform contract;
- неизвестное фактическое состояние реализации.

Не создавать researcher для чтения файлов, которые implementer и так должен открыть.

Researcher возвращает компактные факты, файлы, зависимости и риски. Production-код не меняет.

## 3. Выполнение основной task

### `implementer`

- сделать минимальное законченное изменение в scope;
- переиспользовать существующие contracts/components/services;
- не проводить побочный refactor;
- не добавлять новый architecture/data/API/security scope без требования task;
- добавить только необходимые tests;
- обновить docs, если долговечное поведение реально изменилось;
- выполнить mobile/error/recovery/a11y состояния, которые прямо относятся к изменённому flow.

### `researcher`

- production-код не менять;
- вернуть evidence/brief/decision input, требуемый task;
- не превращать discovery в скрытую реализацию.

### `orchestrator`

- делить работу только по естественным независимым границам;
- назначать минимальное число subagents и skills;
- write-работу передавать `implementer` только если task это требует;
- не создавать agent на каждый skill;
- собирать краткие результаты, а не весь журнал subagents.

### `independent-reviewer`

- выполнять независимую проверку, а не новую реализацию;
- production-код не менять;
- owner decision не подменять.

### `qa-verifier`

- проверять фактическое поведение и риски;
- production-код не менять;
- не запускать полный suite без требования task или доказанного риска.

### `integration-release`

- закрывать integration/operations/release scope;
- не добавлять feature scope;
- исправлять только настоящие integration/release blockers.

## 4. Самопроверка primary agent

Если task изменила tracked artifacts:

1. Сопоставить результат со всеми acceptance/done-when пунктами.
2. Запустить минимальный targeted набор checks по изменённой поверхности.
3. Для UI проверить фактический render и основной affected flow на нужных viewport/states, а не устраивать полный UI audit каждого экрана.
4. Проверить provisional `git diff` на лишний scope, secrets, migrations/config/dependencies.
5. Исправить очевидные дефекты до передачи следующей роли.

Full repository suite, полный visual audit и полный security audit по умолчанию не нужны.

Для dedicated `audit + remediation` task, где полный audit прямо является scope, primary pass сначала формирует и **замораживает один finding set** до массовых fixes. После этого remediation, independent review и QA работают от этого набора и regressions текущего diff; они не запускают второй product-wide audit ради новых non-blocking наблюдений.

## 5. Independent review - только если он указан

Отдельный `independent-reviewer` выполняется только если:

- он указан в `Дополнительные роли lifecycle`; или
- он является `Основная роль` текущей task.

Первый review является единственным **full review pass**. Reviewer проверяет:

- acceptance criteria текущей task;
- regressions, внесённые текущим diff;
- correctness/data integrity/security/privacy только по реально затронутой поверхности;
- необходимые critical tests;
- существенный UX/a11y/performance regression только там, где текущий diff мог его создать.

Reviewer не должен:

- проводить новый полный аудит продукта;
- расширять task соседним техническим долгом;
- требовать исправить pre-existing проблему, не вызванную текущим diff;
- добавлять новый product requirement;
- подключать новые write-роли ради non-blocking finding.

### Severity и blocking policy

Использовать только эти значения:

- `BLOCKER` - task нельзя безопасно завершить: data loss/cross-user access/security break/сломанный обязательный core flow или невозможность выполнить task.
- `HIGH` - acceptance criterion не выполнен либо текущий diff создаёт вероятный серьёзный production defect. Блокирует завершение.
- `MEDIUM` - реальный дефект/quality issue текущего scope, но acceptance criteria выполнены и безопасное завершение возможно. **Не блокирует task.**
- `LOW`/`NIT` - polish/maintainability/style без существенного production impact. Не блокирует task.
- `OUT_OF_SCOPE` - реальная соседняя проблема или улучшение вне текущей task. Не блокирует task.

Запрещён результат вида `MEDIUM, но коммитить нельзя`. Если finding действительно делает результат неприемлемым, reviewer обязан классифицировать его как `HIGH`/`BLOCKER` и воспроизводимо объяснить почему.

Первый review возвращает закрытый набор findings с ID и verdict:

- `APPROVED`;
- `APPROVED_WITH_NON_BLOCKING_FINDINGS`;
- `BLOCKED`.

## 6. Исправление review findings и повторный review

Автоматически исправляются только `BLOCKER/HIGH` текущего scope.

`MEDIUM` можно исправить в этой task только если fix одновременно:

- локальный и очевидный;
- не создаёт migration/schema/public API/new permission model/dependency/architecture change;
- не требует новой роли или нового профильного skill;
- не расширяет touched subsystem.

Иначе `MEDIUM` фиксируется как follow-up и task продолжается к финализации.

`LOW/NIT/OUT_OF_SCOPE` после review автоматически не исправлять.

После исправления `BLOCKER/HIGH` выполнить **targeted recheck**, а не новый full review:

- проверить только ранее зафиксированные blocking finding IDs;
- проверить regressions, которые могли быть внесены этими fixes;
- не начинать новый поиск `MEDIUM/LOW/NIT` по всему diff.

Новый `BLOCKER/HIGH` на recheck допустим только если он непосредственно создан fix или является очевидным критическим defect текущего diff, пропущенным в первом pass. Он должен быть явно обоснован.

### Ограничение циклов review

- обычная task: максимум 2 review passes - full review + targeted recheck;
- high-risk/audit/release task: третий targeted pass допустим только если fix после второго pass сам создал новый `BLOCKER/HIGH`;
- после лимита не запускать очередной review автоматически. Вернуть точный blocker/status владельцу.

## 7. QA verification - только если она указана

`qa-verifier` выполняется только если указан в `Дополнительные роли lifecycle` или является основной ролью.

QA выбирает минимальный набор сценариев с максимальной уверенностью. Проверять только применимые риски:

- happy/negative/boundary;
- auth/ownership;
- duplicate/retry/idempotency;
- concurrency, timezone, external failure - только если flow это реально затрагивает;
- loading/error/recovery;
- mobile/TMA states для client-facing change;
- accessibility для изменённых interaction paths;
- migration/rollback - если есть migration.

Не прогонять одну и ту же матрицу на каждом layer и не повторять все viewport, если task изменяет один локальный state.

QA findings используют ту же blocking policy: только `BLOCKER/HIGH` блокируют. `MEDIUM/LOW` не должны запускать новый feature cycle.

После исправления blocking QA defect повторить failed/affected scenario. Не выполнять полный QA заново.

Нормальный лимит - один QA pass + один targeted recheck при blocking defect.

## 8. Запрет review-driven scope creep

Review/QA не могут сами по себе быть основанием для нового крупного scope.

Без прямого требования task или `BLOCKER/HIGH`, доказывающего нарушение текущего contract, после review запрещено добавлять:

- migrations/columns/indexes/constraints;
- новый API/public contract;
- новый auth/RBAC/permission model;
- новый scheduler/queue/storage layer;
- новую Telegram/deep-link architecture;
- новую dependency;
- новый product flow.

Такой finding становится follow-up/owner decision.

## 9. Финальная проверка и Git

После применимых stages:

1. Запустить финальный минимальный набор affected checks.
2. Проверить итоговый `git diff`.
3. Убедиться, что нет случайных files/secrets/generated artifacts и review-driven scope creep.
4. Проверить migrations/config/dependencies только если они реально изменились.
5. Убедиться, что все `BLOCKER/HIGH` закрыты либо task остановлена с точным blocker.
6. `MEDIUM/LOW/OUT_OF_SCOPE` перечислить кратко как non-blocking follow-ups; они не мешают commit.
7. Создать один логический commit при tracked changes, если task не задаёт другой stage strategy.
8. Не merge/deploy/push/production action без разрешения.
9. Не переходить к следующей task.

## 10. Финальный отчёт

Кратко указать:

- primary role и только фактически использованные дополнительные роли;
- фактически загруженные core/conditional skills;
- что изменено/переиспользовано;
- ключевые файлы;
- migrations/config/dependencies;
- exact checks и результат;
- review verdict и blocking findings status;
- QA status, если QA была предусмотрена;
- non-blocking findings/follow-ups без длинного повторного аудита;
- что не проверено;
- owner/manual actions;
- commit hash или `no commit`.

Нельзя утверждать independent review, QA, real-user, real Telegram, provider или production validation, если этого фактически не было.

## 11. Stop conditions

Остановить текущую task и не переходить дальше, если:

- нужен owner checkpoint/approval;
- отсутствует обязательный Trigger/evidence;
- нужен secret/credential/external action;
- требования противоречат source of truth;
- остаётся `BLOCKER/HIGH`, который нельзя безопасно исправить в scope;
- fixing blocker требует нового крупного scope, не разрешённого task;
- достигнут лимит review/QA recheck и blocking defect остаётся.

Вернуть точный blocker и уже выполненную часть lifecycle.
