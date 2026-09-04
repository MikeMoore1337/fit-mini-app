# Жизненный цикл `.artifacts/`

Этот документ — долгосрочное правило для локальных task worktrees и CI tooling. `.artifacts/`
остаётся ignored-каталогом: его содержимое не является заменой tracked-коду, backlog, Git history
или owner decision.

## Каноническая структура

```text
.artifacts/
  worktrees/                 # только controller-managed Git worktrees
  tasks/
    <TASK_ID>/
      temporary/             # воспроизводимые данные до terminal closeout
      evidence/              # отобранные proof, отчёты и human-gate материалы
      deliverables/          # явно предназначенные владельцу файлы
      logs/                  # task-local диагностические логи с ограниченным retention
      manifest.json          # classification, provenance и retention
  runtime/
    cache/                   # кэши tooling, не source of truth
    tmp/                     # process-local temporary data
    tests/                   # test DB, coverage и generated test output
  shared/                    # только явно reusable local assets
  operations/
    backups/                 # PostgreSQL и иные rollback backups
    deployments/             # deployment state и release evidence
    recovery/                # controller/recovery anchors и cleanup markers
```

Новые task-specific файлы сначала получают путь через `scripts/artifact_manager.py`. Менеджер
проверяет Task ID и containment, не проходит symlink/junction/reparse point и записывает в
`manifest.json` назначение, owner, command context, created time и retention. `evidence` и
`deliverables` не следует создавать в общей плоской папке.

## Классификация и retention

| Класс | Правило |
| --- | --- |
| `temporary` | Воспроизводимые промежуточные файлы. Для task удаляются после terminal success; shared runtime очищается только bounded policy. |
| `evidence` | Отобранный результат, нужный для review, QA, human gate, release proof или расследования. По умолчанию сохраняется. |
| `deliverables` | Owner materials. Generic cleanup их не удаляет; нужен отдельный exact target decision. |
| `logs` | Диагностические логи с ограниченным retention; чувствительное содержимое не копируется в итоговые отчёты. |
| operations | Backups, deployment и recovery evidence. Защищены от generic cleanup и имеют собственный lifecycle. |

`worktrees/`, active task data, dirty/interrupted/unique-commit worktrees, controller state,
recovery anchors, backups и deployment evidence нельзя удалять обычной файловой операцией.
Новые top-level каталоги `.artifacts/` запрещены: legacy `cache/`, `tmp/`, `tests/`, `backups/`,
`deployments/`, `recovery/` и старые task-specific evidence paths являются только migration inputs.
Их нельзя пополнять и нельзя переименовывать массово без проверки durable references.

## Команды

Проверка source references и manifest:

```powershell
python scripts/artifact_manager.py --root .artifacts --repo-root . validate
```

Read-only inventory и exact plan:

```powershell
python scripts/artifact_manager.py --root .artifacts --repo-root . audit
python scripts/artifact_manager.py --root .artifacts --repo-root . dry-run `
  --output tasks/133/evidence/cleanup-plan.json --json
```

`dry-run` обязан фиксировать абсолютный root, относительный path каждого target, category,
reason, size и disposition (`DELETE`, `MOVE`, `KEEP`, `REVIEW`). `REVIEW` никогда не становится
target generic cleanup автоматически. Первый массовый `DELETE`/`MOVE` — `DESTRUCTIVE_ACTION`:
после формирования plan работа останавливается на owner checkpoint.

После exact owner approval применяется только неизменившийся plan и его SHA256:

```powershell
python scripts/artifact_manager.py --root .artifacts --repo-root . apply-plan `
  .artifacts/tasks/133/evidence/cleanup-plan.json `
  --approved-plan-sha256 <EXACT_PLAN_SHA256> --json
```

Менеджер повторно проверяет plan hash, root, fingerprints, controller leases и worktrees. При
любом drift, несовместимом lease, незавершённой Task 132, unsafe path или ошибке удаления он
останавливается fail-closed. Повтор того же успешно применённого SHA идемпотентен; новый набор
targets требует нового dry-run и нового owner decision.

Очистка одной успешно завершённой task ограничена её exact `tasks/<TASK_ID>/temporary`:

```powershell
python scripts/artifact_manager.py --root .artifacts --repo-root . cleanup-task 133 `
  --terminal-state finished --json
```

`task_session.py finish` выполняет эту операцию внутри terminal closeout и сохраняет компактный
результат в controller history. `run_task_delivery.py` сначала дожидается закрытия worker log и
успешного `_verify_closeout`, переносит необходимый `final.md` в task evidence, затем удаляет
только свою `temporary/delivery` subtree. Waiting/ready worktrees, delivery owner другой task и
shared coordination state не входят в cleanup scope. Ошибка cleanup останавливает closeout, а не
маскируется.

Shared runtime можно чистить только bounded policy и с отдельным exact SHA:

```powershell
python scripts/artifact_manager.py --root .artifacts --repo-root . cleanup-runtime `
  --ttl 7d --max-entries 1000 --max-bytes 536870912 `
  --output runtime/tasks-runtime-cleanup-plan.json --json
python scripts/artifact_manager.py --root .artifacts --repo-root . cleanup-runtime `
  --plan .artifacts/runtime/tasks-runtime-cleanup-plan.json --apply `
  --approved-plan-sha256 <EXACT_PLAN_SHA256> --json
```

По умолчанию эта команда только формирует plan. `--apply` допустим после owner approval exact
SHA; active process consumers, controller lease и protected directories блокируют операцию.

## Миграция legacy paths

1. Сначала запустить `validate` и `audit`, сохранить machine-readable output в Task evidence.
2. Проверить producer и все durable consumers: ссылки в тестах, CI artifacts, human review locks,
   deployment/recovery runbooks и owner deliverables.
3. Перевести producer на canonical path. Исторический файл не перемещать, если это ломает
   reproducibility или durable reference.
4. Для однозначно воспроизводимого temporary использовать exact `DELETE`; нужный evidence или
   deliverable — exact `MOVE` с destination и manifest; неоднозначный legacy — `REVIEW`.
5. После owner approval применить только frozen plan. При изменении inventory повторить весь
   цикл с новым plan SHA.

## Итоговый отчёт и troubleshooting

Каждый cleanup report обязан показывать: absolute root, plan SHA (если применим), counts/bytes по
`DELETE/MOVE/KEEP/REVIEW`, `before_bytes`, `after_bytes`, `freed_bytes`, список preserved paths и
точные cleanup errors/refusals. В отчёт не попадают secrets, tokens, PII и полное содержимое логов.

Если cleanup заблокирован, сначала исправляется причина, а не обходится safety check:

- active/incompatible lease или unfinished Task 132 — дождаться terminal state и повторить audit;
- dirty/interrupted/unique/recovery worktree — сохранить его и разруливать через controller/Git;
- reparse/symlink/inaccessible path — exact owner review, без follow и без broad glob;
- manifest/source validation error — зарегистрировать путь или вернуть producer в canonical class;
- plan drift — не подставлять новый target: сформировать новый dry-run и получить новый approval.

Production backups и production host этим локальным manager не очищаются.
