# Task-ветки, worktree и сериализованная интеграция в `dev`

Статус ADR: **принято для repository contract; live enforcement ожидает owner checkpoint**.

## Контекст и решение

До Task `127` основной worktree одновременно использовался для реализации и интеграции. Несколько
writer-сессий могли разделить branch, index и незакоммиченные файлы, а Ruleset `dev` запрещал только
удаление и non-fast-forward. Обычный fast-forward push в `dev` оставался технически возможен.

Принято следующее решение:

```text
1 executable task
  = 1 task ID
  = 1 branch task/<ID>-<slug>
  = 1 отдельный worktree
  = 1 writer lease
  = 1 PR в dev

dev = clean integration-only worktree + строго один merge candidate
master = production source + только canonical checked release PR
```

Task branch создаётся только от exact `origin/dev`. Stacked branches по умолчанию запрещены.
Research-only сессии могут сосуществовать только с отдельными `research-readonly` leases; они не
получают право merge. `integration` и `release` leases глобально эксклюзивны.

Remote serialization использует поддерживаемые GitHub primitives без отдельного сервиса:

- PR-only Ruleset для `dev`;
- strict required check `checks`, поэтому merge первого PR делает все остальные candidates stale;
- task provenance job в `.github/workflows/ci.yml`;
- один локальный integration lease/queue head до merge;
- `auto-merge` для task PR не используется.

Git ref update на GitHub атомарен. Поэтому два PR, проверенные относительно одного `dev`, не могут
оба сохранить current-base eligibility после merge первого: второй обязан обновиться от нового
`dev` и пройти checks заново.

### Рассмотренные альтернативы

- Реализация прямо в permanent `dev` отклонена: общий index/worktree не изолирует writer-сессии.
- Stacked task branches отклонены по умолчанию: provenance и dependency становятся неявными.
- Отдельный orchestration service/queue отклонён: для текущего масштаба достаточно atomic local
  leases и strict GitHub current-base enforcement.
- PR-based `master -> dev` sync отклонён: merge PR создаёт новый commit и не сохраняет равенство
  exact успешно задеплоенному `master` SHA.
- Broad PAT/admin bypass отклонён. Выбран узкий GitHub App actor только для exact deployed sync.

## Runtime state и atomic leases

Controller `scripts/task_session.py` хранит состояние в shared Git common dir:

```text
<git-common-dir>/codex-task-sessions-v1/
├── contract.json
├── state.lock
├── integration-queue.json
├── leases/
│   ├── task-<ID>.json
│   ├── integration.json
│   └── release.json
└── history/task-<ID>.json
```

Путь machine-local и содержимое leases не коммитятся. Create использует `O_EXCL`, update — temporary
file + atomic replace под глобальным `state.lock`. Повреждённый JSON, оставшийся lock или отсутствующее
обязательное состояние являются blocker; controller не удаляет их автоматически.

Task lease содержит task ID/path, branch, абсолютный worktree path, base SHA, mode, timestamps,
lifecycle state и session label без secrets. `finish` никогда не удаляет branch/worktree: он только
завершает lease после exact merge SHA и terminal successful `dev` push-CI. Cleanup выполняется лишь
после отдельного owner confirmation и повторной проверки dirty/unique state.

## Машинно проверяемые task metadata

Команда `validate-metadata` строит единственное представление непосредственно из owner-local task
files; отдельной ручной очереди нет. Для legacy task безопасные defaults: `exclusive-write`,
`explicit-launch`, `task-pr-to-dev`; dependencies извлекаются из поля `Зависимости`. Для новой task
рекомендуется точный block:

```text
<!-- task-session
dependencies: 120D, 90B
executable: true
concurrency: exclusive-write
owner_gate: explicit-launch
integration: task-pr-to-dev
-->
```

Umbrella IDs и `executable: false` не запускаются. Start всегда требует явный `--owner-launch`;
approval другой task не наследуется.

## Команды controller

Все команды запускаются из canonical repository или любого его worktree.

```powershell
python scripts/task_session.py doctor
python scripts/task_session.py validate-metadata
python scripts/task_session.py start 119 --owner-launch --session-label codex-119
python scripts/task_session.py adopt-current 127 --owner-launch --session-label codex-127-resume
python scripts/task_session.py status
python scripts/task_session.py recover 119
python scripts/task_session.py mark-ready 119 --head-sha <sha> --review-verdict APPROVED --qa-verdict PASS
python scripts/task_session.py enqueue-integration 119 --pr 123
python scripts/task_session.py prepare-integration 119
python scripts/task_session.py complete-integration 119 --merge-sha <exact-dev-merge-sha>
python scripts/task_session.py finish 119
```

`start` печатает абсолютный worktree, branch/base SHA, canonical task path, metadata, запреты и
recovery command. Task-файл не копируется в worktree: owner-local canonical file остаётся единственным
источником backlog state.

### Нормальный task lifecycle

1. `doctor` подтверждает clean/current main `dev`, отсутствие Git operation, release freeze и
   несовместимого lease.
2. `start` создаёт reservation lease, branch и отдельный worktree от exact `origin/dev`.
3. Writer завершает implementation/review/QA и один logical commit с `[Task <ID>]`.
4. `mark-ready` на clean exact HEAD фиксирует успешные review/QA verdicts; research lease эту стадию
   пройти не может. Branch push и PR `[Task <ID>] ...` идут только в `dev`.
5. CI проверяет branch/title/commit IDs и aggregate `checks`.
6. `enqueue-integration` фиксирует immutable candidate evidence.
7. `prepare-integration` выдаёт eligibility только queue head при current `dev` и exact successful
   checks; создаёт global integration lease.
8. Merge выполняется ровно один. Controller ждёт exact merge SHA и successful push-CI `dev`.
9. `complete-integration` открывает следующего candidate. `finish` освобождает task lease без cleanup.

При release lease/open `dev -> master` PR task PR могут оставаться open/draft, но merge и branch
update в `dev` запрещены.

## CI provenance

Job `Task provenance` выполняется до aggregate `checks`:

- task PR обязан иметь base `dev`, same-repository branch `task/<ID>-<slug>`, title с `[Task <ID>]`
  и только commits того же Task ID;
- normal PR в `master` обязан идти из `dev`; exceptional recovery/hotfix остаётся отдельным
  owner-approved процессом;
- каждый push SHA в `dev` обязан быть merge result task PR, exact successfully deployed current
  `master` sync или SHA из owner-controlled `DEV_RECOVERY_APPROVED_SHA`;
- failure/cancel/timeout/stale check не даёт integration eligibility.

Task PR CI не публикует images и не запускает deployment: publish остаётся только для push в
`master`, deploy — только после successful post-merge master CI.

## Exact `master -> dev` sync

Выбран `.github/workflows/sync-dev-after-deploy.yml`. Он запускается только после terminal success
`Deploy production`, повторно проверяет, что workflow SHA равен current `master`, и допускает только
fast-forward текущего `dev` к этому exact SHA. Любая divergence блокирует sync.

Workflow по умолчанию выключен: `ENABLE_DEPLOYED_MASTER_DEV_SYNC != true`. Для включения нужен
owner-approved GitHub App, установленный только в этот repository с минимальным permission
`Contents: Read and write`. Его actor становится единственным bypass actor Ruleset `dev` в режиме
`always`. Secrets `DEV_SYNC_APP_ID` и `DEV_SYNC_APP_PRIVATE_KEY` хранятся в protected `production`
environment. Широкий PAT/admin bypass не используется.

## OWNER_CHECKPOINT: live GitHub enforcement

До owner decision запрещено менять Ruleset, bypass actors, variables, secrets и repository merge
settings. Для применения владелец подтверждает:

1. создание/установку узкого GitHub App и его actor ID;
2. добавление двух environment secrets без передачи значений в chat/log;
3. изменение Ruleset `permanent-development-dev`:
   `deletion`, `non_fast_forward`, `pull_request`, strict `required_status_checks: checks`;
4. единственный bypass actor — этот App; user/team/admin bypass отсутствует;
5. `allow_auto_merge=false` либо организационный запрет использовать auto-merge для task PR;
6. включение `ENABLE_DEPLOYED_MASTER_DEV_SYNC=true` только после successful dry read-back.

После apply выполнить API read-back и сохранить evidence без secret values:

```powershell
gh api repos/MikeMoore1337/fit-mini-app/rulesets/21801287
gh api repos/MikeMoore1337/fit-mini-app
gh api repos/MikeMoore1337/fit-mini-app/actions/variables/ENABLE_DEPLOYED_MASTER_DEV_SYNC
```

Проверяемые свойства: exact `refs/heads/dev` condition, active enforcement, PR-only, strict
`checks`, delete/non-FF protection, только expected App bypass, expected auto-merge setting.

### Rollback настроек

Fail-safe rollback сначала ставит variable в `false`, затем возвращает сохранённый pre-change
Ruleset snapshot `deletion + non_fast_forward` через точечный API update. Ruleset не удаляется,
master contract не меняется, branch history не переписывается. После rollback повторить read-back и
оставить integration blocked до разбора причины.

## Recovery

`recover <ID>` только классифицирует состояние. Он не выполняет reset, stash, worktree remove,
branch delete или force-push.

- dirty/index/Git operation → `DIRTY_NEEDS_OWNER`;
- unique commits → `RECOVERY_ANCHOR`;
- branch/worktree без lease или несколько совпадений → `RECOVERY_REQUIRED`;
- detached clean state без unique commits → потенциальный `SAFE_TO_REMOVE`, но удаление всё равно
  требует owner confirmation;
- corrupted/stale lease/lock → blocker с точным path.

Main `dev` ahead/behind/dirty блокирует `start`. Candidate после чужого merge становится stale и
обязан обновиться от нового `dev`, повторить affected review/QA при conflict resolution и весь CI.

## Глобальный auto-continue contract

Если текущая task не объявляет `OWNER_CHECKPOINT`, `HUMAN_EVIDENCE`, `MANUAL_VISUAL_APPROVAL`,
`LEGAL_COUNSEL_REQUIRED`, `EXTERNAL_AUTHORIZATION`, `DESTRUCTIVE_ACTION` или terminal blocker,
controller/lifecycle после terminal success автоматически продолжает применимые review, QA,
commit, task PR, serial integration, `dev` CI и normal release без дополнительного owner prompt.
Тишина владельца не является gate. Следующая product task автоматически не запускается.

Для Task `127` открытый owner checkpoint выше блокирует только live apply/activation. Локальные
изменения, tests, synthetic rehearsal и review/QA продолжаются автоматически до этого checkpoint.
