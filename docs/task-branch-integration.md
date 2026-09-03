# Task-ветки, worktree и прямой PR-flow в `master`

Статус ADR: **принято и действует в repository contract и live GitHub enforcement**.

## Контракт

Нормальный delivery-flow намеренно короткий:

```text
1 executable task
  = 1 task ID
  = 1 branch task/<ID>-<slug>
  = 1 отдельный worktree
  = 1 writer lease
  = 1 task PR в master

task branch -> current origin/master -> local PRE_PUSH_CI_PASS
  -> PR master -> exact-head checks -> merge master
  -> post-merge provenance/image publication
  -> immutable bundle deploy -> smoke/observation
  -> controller finish -> archive/check
```

`master` — защищённая release-ветка и единственный normal release base. Task branch создаётся
только от exact `origin/master`; stacked branches по умолчанию запрещены. Canonical controller
worktree используется для координации и closeout, но не для feature implementation. Legacy `dev`
refs могут оставаться в repository для recovery/inventory, но не являются частью normal delivery.

GitHub Ruleset для `master` обязан быть active и требовать pull request, deletion protection,
non-fast-forward protection, strict current-base required checks и aggregate check `checks`.
Direct/force push и удаление ветки запрещены. Merge PR — release authorization; отдельный generic
approval между merge и normal deploy не создаётся.

## Shared gate

`scripts/ci_contract.py` — единственный registry команд CI. Он содержит детерминированные профили:
`frontend`, `backend`, `cross-stack`, `workflow-platform`, `documentation`. GitHub workflow и
локальный `scripts/pre_push_gate.py` вызывают одни и те же group IDs; profile выбирается по
изменённым путям консервативно, а отсутствующий prerequisite даёт `PRE_PUSH_CI_BLOCKED`.

`pre-push` gate выполняет metadata preflight, проверяет lease, task branch, current
`origin/master`, clean worktree и ancestry, затем записывает evidence в
`.artifacts/tasks/<ID>/evidence/pre-push/gate.json`. Evidence содержит HEAD, base, branch, task,
target base, scope/profile, группы, timestamps, contract version/digest, clean-worktree marker и
самопроверяемый evidence digest. `PRE_PUSH_CI_PASS` действителен только для exact HEAD и exact
base; изменение кода, CI contract, base или рабочей директории инвалидирует его.

`scripts/task_session.py mark-ready` не принимает произвольное утверждение о gate: он заново
проверяет clean task worktree, current `origin/master`, commit provenance, exact evidence digest,
все applicable successful groups и approved review/QA. Поэтому readiness невозможен без текущего
`PRE_PUSH_CI_PASS`, а failed candidate требует нового exact HEAD.

## Leases и безопасный closeout

Controller хранит machine-local coordination state в shared Git common dir:

```text
<git-common-dir>/codex-task-sessions-v1/
├── contract.json
├── state.lock
├── leases/task-<ID>.json
└── history/task-<ID>.json
```

State не коммитится. Create использует `O_EXCL`, update — temporary file + atomic replace под
`state.lock`. Corrupted JSON, оставшийся lock, duplicate branch/worktree, dirty/interrupted state
и неизвестная lease являются blocker; controller не удаляет их автоматически.

Task lease содержит task ID/path, branch, абсолютный worktree, exact `base_origin_master_sha`,
target base, mode, timestamps, lifecycle state и session label без secrets. `finish` запускается
из canonical controller worktree только после exact merged master SHA и terminal production success.
Он удаляет только matching clean task worktree и локальную task branch без `--force`; unique
commits, divergence refs, changed head и artifact cleanup error останавливают closeout с
сохранением данных.

`recover` — read-only диагностика. Он сохраняет dirty files, unique commits и interrupted Git
operations для owner-safe решения. Ни `recover`, ни `finish` не выполняют `reset --hard`, force
delete или несанкционированное восстановление.

## Один пользовательский запуск

```powershell
.\.venv\Scripts\python.exe scripts\run_task_delivery.py <ID>
```

Явный выбор task владельцем или эта команда являются standing authorization для normal delivery
этой task: отдельный worktree, implementation/review/QA, commit, task PR в `master`, CI, immutable
bundle deploy и safe closeout. Launcher останавливается только на точном terminal blocker либо
явно объявленном human/legal/external/destructive/task-specific gate. Следующая product task
автоматически не запускается.

Низкоуровневые команды:

```powershell
python scripts/task_session.py doctor
python scripts/task_session.py validate-metadata
python scripts/task_session.py start 135 --owner-launch --session-label codex-135
python scripts/task_session.py adopt-current 135 --owner-launch --session-label codex-135-resume
python scripts/task_session.py status
python scripts/task_session.py recover 135
python scripts/task_session.py mark-ready 135 --head-sha <sha> --review-verdict APPROVED --qa-verdict PASS
python scripts/task_session.py complete-production 135 --pr <number> --merge-sha <sha> --deployed-sha <sha>
python scripts/task_session.py finish 135
```

Task-файл не копируется в worktree: owner-local canonical path остаётся единственным источником
backlog metadata. `validate-metadata` проверяет dependencies, `executable`, concurrency, owner gate
и integration policy. Неполные или unknown значения остаются fail-closed.

## CI и production provenance

PR в `master` обязан быть same-repository task branch с `[Task <ID>]` в title и commit messages,
его base SHA должен быть current, а `checks` — successful на exact PR head. PR-triggered CI выполняет
полный применимый профиль. После merge push-CI не повторяет full regression suite: он подтверждает
merged task PR provenance и публикует immutable backend/bot images через
`scripts/deployment_contract.py`.

`deploy.yml` принимает только successful `master` workflow run, ещё раз проверяет association с
merged task PR и current master, checkout выполняется только на GitHub runner. Runner создаёт
bundle из exact commit и migration manifest. Production host получает bundle по SSH, распаковывает
его в release directory, проверяет `.deployment-sha`, запускает `deploy_production.sh` с
immutable image refs и persistent state, а затем сохраняет release `.env`. На production host нет
шага `git fetch`, `git reset`, `git rev-parse` или зависимости от Git checkout.

Post-merge CI и deployment используют exact SHA; rollback/skip/manual-intervention verdict не
маскируется успешным job. Smoke, migration gate, image revision/digest, slot ownership, worker/bot
handoff и host lock остаются в deployment evidence под persistent `.artifacts/operations`.

Любая exceptional операция — history rewrite, direct/force push, manual production command,
bootstrap, infrastructure recovery или deployment SHA вне current merged `master` — требует
отдельного owner authorization, backup и operator preflight.
