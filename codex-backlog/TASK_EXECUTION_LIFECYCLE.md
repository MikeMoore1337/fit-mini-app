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

`MEDIUM` не блокирует локальное завершение lifecycle и logical commit, но незакрытый `MEDIUM`
блокирует `AUTO_RELEASE_ELIGIBLE`: PR/merge/deploy откладываются до verified closure или отдельного
owner-controlled решения, которое прямо изменяет release scope. Severity нельзя понижать ради release.

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

Каждый `MEDIUM/LOW`, включая локально исправленный в текущей task, primary agent добавляет или
обновляет в `codex-backlog/bugs/FINDINGS.md` до commit. Reviewer передаёт ID, severity,
scenario/impact, source, minimal fix и verification; финальный ответ и `.artifacts/` не являются
заменой реестра.

Для finding, исправленного и проверенного в текущей task, отдельный bug-task не создавать.
Неисправленный finding не становится task автоматически: после triage и явного решения владельца
его можно маршрутизировать в `codex-backlog/bugs/pending/` по
`codex-backlog/bugs/README.md`. Такой bug-task не входит в основную последовательность product
tasks и не запускается без отдельного выбора владельца.

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
7. Синхронизировать все новые/изменённые `MEDIUM/LOW` в
   `codex-backlog/bugs/FINDINGS.md`; закрытые записи не удалять, а обновлять status/verification.
8. Создать один логический commit в lease-bound `task/<ID>-<slug>` branch/worktree при tracked
   changes, если task не задаёт другой stage strategy.
   Новый registry entry считается tracked change даже для read-only audit/review task.
9. Проверить `[Task <ID>]` provenance, push task branch, открыть только task PR в `dev`, дождаться
   exact-head `checks` и пройти `scripts/task_session.py` serial integration queue. Merge разрешён
   только queue head при current `origin/dev`; после merge дождаться terminal successful exact-SHA
   `dev` push-CI. Direct feature push в `dev` запрещён.
10. Классифицировать уже интегрированную task как `AUTO_RELEASE_ELIGIBLE` либо
    `AUTO_RELEASE_BLOCKED` по разделу 9A.
11. Выполнить разрешённый canonical release final либо остановиться на точном owner/blocker gate.
12. Не переходить к следующей task автоматически; после eligible release сначала подтвердить
    terminal deploy success и синхронизацию `dev`.
13. Если task не содержит явно обязательного owner checkpoint, human/device evidence, legal-counsel
    gate, destructive/external authorization или terminal blocker, не ждать отдельного сообщения
    владельца: автоматически продолжать следующий разрешённый lifecycle step после terminal success.

Если текущая task не объявляет `OWNER_CHECKPOINT`, `HUMAN_EVIDENCE`, `MANUAL_VISUAL_APPROVAL`,
`LEGAL_COUNSEL_REQUIRED`, `EXTERNAL_AUTHORIZATION`, `DESTRUCTIVE_ACTION` или terminal blocker,
controller/lifecycle после terminal success автоматически продолжает применимые review, QA,
commit, task PR, serial integration, `dev` CI и normal release без дополнительного owner prompt.
Тишина владельца не является gate. Следующая product task автоматически не запускается.

## 9A. Release eligibility и автоматический normal path

Task является `AUTO_RELEASE_ELIGIBLE`, только если одновременно:

1. созданы tracked releasable changes и один итоговый logical commit;
2. implementation, применимые review/QA и final verification завершены;
3. незакрытых `BLOCKER`, `HIGH` и `MEDIUM` ровно ноль, а исправленные blocking/release-blocking
   findings имеют required targeted recheck evidence;
4. `codex-backlog/bugs/FINDINGS.md` синхронизирован по действующей policy;
5. task не содержит незавершённый явно обязательный owner checkpoint/approve, human/device evidence,
   legal-counsel gate или manual visual gate;
6. нет unresolved production/recovery blocker;
7. task PR уже serially merged в `dev`, exact merge SHA имеет terminal successful push-CI,
   `origin/dev` содержит актуальный `origin/master`, а integration worktree чист от accidental
   scope, secrets и debug artifacts.

Иначе task получает `AUTO_RELEASE_BLOCKED` с точной причиной. `LOW`, `NIT` и `OUT_OF_SCOPE` сами по
себе release не блокируют. `no commit` не создаёт искусственный PR/deploy.

Для `AUTO_RELEASE_ELIGIBLE` task агент без дополнительного owner prompt обязан:

1. `git fetch --prune origin`, проверить, что `origin/master` является ancestor текущего
   `origin/dev`. Если deployed master ещё не synchronized, direct merge/push запрещён: дождаться
   узкого `sync-dev-after-deploy` либо остановиться на recovery blocker;
2. подтвердить, что task PR был merge ровно как queue head, а **push-triggered CI run exact merged
   `dev` SHA** имеет `status=completed` + `conclusion=success`. PR-triggered CI task branch не
   заменяет этот branch CI gate;
3. проверить отсутствие открытого release PR `head=dev`, `base=master` во время task integration.
   Если matching release PR уже открыт и новый task merge/update действительно нужен, controller
   блокирует `dev`; PR сначала закрывается, затем candidate заново проходит current-base checks;
4. только после успешного exact merged-dev push-CI создать соответствующий scope PR `dev -> master` либо
   переоткрыть ранее закрытый matching PR, если его base/scope остаются корректными. Если после
   открытия PR требуется ещё один code/config/docs commit или новый task merge, PR необходимо
   закрыть, вернуть change в task branch/worktree и повторить task PR + serial integration;
5. проверить expected PR head SHA и required check `checks`; required PR checks должны завершиться
   успешно именно для текущего PR head, а success более раннего branch CI их не подменяет;
6. включить GitHub auto-merge либо после green required PR checks выполнить эквивалентный обычный
   PR merge только для ожидаемого head SHA;
7. проверить post-merge CI exact merged `master` SHA и затем автоматически запущенный production
   deploy того же SHA до terminal success. Failure/rollback/manual-intervention verdict останавливает
   sequence fail-closed. Успешный deploy workflow со встроенными rollout/smoke gates является
   достаточным production release evidence; дополнительный live smoke выполнять только если task
   прямо требует его или deploy evidence неоднозначен;
8. после успешного production deploy узкий owner-approved GitHub App workflow выполняет только
   fast-forward/sync `dev` к **тому же exact successfully deployed current `origin/master` SHA**.
   Обычный user/PAT/admin direct push или manual merge запрещён; затем подтвердить равенство refs;
9. pure fast-forward sync `dev` на уже успешно проверенный и задеплоенный exact `master` SHA не
   создаёт нового release candidate. Если такой push автоматически запускает branch CI на `dev`,
   этот post-sync CI является **информационным, не release gate**: агент не ждёт его terminal result,
   не запускает повторный PR/deploy и не задерживает финализацию уже успешной task. Исключение - если
   sync неожиданно изменил tree/content вместо pure fast-forward; тогда считать это новым изменением,
   остановиться и разобраться до следующей task.
10. после подтверждения exact ref sync выполнить `git fetch --prune origin`, перейти в canonical
    `dev` worktree и запустить `scripts/task_session.py finish <ID>`. `finish` без отдельного owner
    prompt удаляет только exact matching clean task worktree и merged local branch. Dirty state,
    Git operation, unique commits, ambiguous/mismatched state или divergence refs останавливают
    closeout fail-closed без `--force` и без очистки сохранившихся данных;
11. после successful `finish` автоматически перенести canonical task-файл через
    `scripts/archive_backlog_task.py archive`, затем выполнить `scripts/archive_backlog_task.py
    check`. Ошибка archive/manifest check является terminal closeout blocker и не скрывается;
12. сформировать terminal final report только после successful finish, archive и manifest check.

Canonical sequencing для нового release candidate:

```text
task branch -> PR dev -> exact-head checks
  -> global integration lease + merge queue head
  -> WAIT exact merged dev push CI: success
  -> ensure NO open release PR dev -> master during integration
  -> create/reopen PR dev -> master
  -> WAIT exact PR required checks: success
  -> merge exact PR head
  -> WAIT post-merge master CI: success
  -> WAIT production deploy exact master SHA: success
  -> narrow GitHub App fast-forward/sync dev to same deployed SHA
  -> verify refs
  -> finish: clean worktree + merged local branch cleanup
  -> archive task + rebuild/check manifests
  -> DONE
```

Новый task PR merge/update в `dev` при открытом `dev -> master` PR запрещён. Если release PR уже
открыт и требуется новая task integration, сначала закрыть release PR; candidate обновляется от
current `dev`, повторяет checks и serial merge. Также запрещено считать автоматически запустившийся
post-sync `dev` CI новой стадией уже завершённого release.

Автоматизация никогда не делает direct push в `master`, не обходит ruleset/required checks,
PR provenance/exact-SHA guard и не запускает manual production command. Task с явно объявленным
human/owner gate останавливается перед указанным gate до фактического решения. Если такой gate не
объявлен, ожидание общего «подтверждения владельца» запрещено: lifecycle продолжает normal path
автоматически. Task-specific запрет release/deploy имеет приоритет.

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
- затронутые `codex-backlog/bugs/FINDINGS.md` IDs и их итоговые statuses;
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
