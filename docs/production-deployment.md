# Бесшовное развёртывание production

Production использует blue/green rollout на одном Docker Compose host. Контракт означает zero
observed user-facing downtime во время управляемого релиза, но не high availability при отказе
VPS, PostgreSQL, Cloudflare или сети.

## Топология и источник состояния

- `caddy` или `cloudflared` остаётся публичным transport и всегда направляет запросы в стабильный
  service `edge`.
- `edge` не перезапускается при обычном application rollout. Caddy сначала выполняет `validate`,
  ждёт bounded точки без in-flight upstream requests, затем применяет config через graceful
  `reload`; autosave хранится в volume `edge_config`. Если такой точки нет, switch не выполняется.
- Application revision работает в `backend-blue` или `backend-green`. У slot нет fixed IP,
  опубликованного порта или общего mutable filesystem.
- Единственный worker и Telegram poller принадлежат активному slot: `worker-blue/green` и
  `bot-blue/green`. Общий `bot_polling_lock` остаётся дополнительной защитой от двух poller.
- PostgreSQL, `edge_config`, `caddy_data`, `caddy_config` и `bot_polling_lock` не принадлежат slot и
  не удаляются cleanup-командами rollout.
- Canonical source of truth — `.artifacts/deployments/state.json` на production host. Он хранит
  active/rollback slot, revision и immutable image digest без secrets. Caddy admin config
  проверяется против этого состояния перед каждым rollout.

Frontend входит в backend image. После switch Caddy направляет новый HTML/API только в candidate,
а запрос `/assets/*`, отсутствующий в candidate, повторяет только в прежний backend. Это сохраняет
старые hashed chunks на весь `DEPLOY_OBSERVATION_SECONDS`; после окна fallback удаляется. Обычные
`POST/PATCH/DELETE` имеют один upstream и не повторяются proxy на другом slot.

## Порядок rollout

`scripts/deploy_production.sh` проверяет exact Git SHA, immutable infrastructure image references и
production config, после чего передаёт управление `scripts/zero_downtime_deploy.py`:

1. host lock, state/config drift, capacity и public active smoke;
2. pull candidate image, проверка OCI revision и разрешение exact repository digest;
3. непрерывный public probe существующей revision;
4. PostgreSQL backup;
5. online-migration gate и один запуск `setup`;
6. start/readiness candidate backend и internal candidate smoke;
7. Caddy validate + reload, внешний application/SEO smoke;
8. последовательный handoff worker и bot: worker обязан записать `worker_stopped` после завершения
   текущего cycle, а новый bot — в логах только текущего запуска получить file lock и начать polling;
9. continuous probe и current-container health/ownership checks в bounded observation window;
10. commit active state, drain old backend и удаление asset fallback.

Любой сбой до switch оставляет прежний route. Сбой после switch до commit state выполняет reload на
старый живой backend, проверяет public smoke и возвращает прежних worker/bot. Interrupted retry
сериализован host lock; повтор уже активного SHA является проверенным no-op. Deployment evidence
пишется в `.artifacts/deployments/<deployment-id>/summary.json` и содержит stages, durations,
capacity, probe counters/latency, handoff и verdict без env values/cookies/request bodies.

## Миграции

Old code работает до конца observation/rollback window, поэтому новая Alembic migration обязана
быть additive и явно объявлять contract:

```python
online_rollout_phase = "expand"
```

Каждая новая migration также содержит непустые `online_rollout_notes` с lock/data bounds. Для
bounded идемпотентного backfill используется phase `backfill`. Gate
отклоняет изменение/удаление исторической migration, `drop_*`, `alter_column`, `rename_table` и
contract migration. Удаление старой схемы выполняется отдельным последующим release после удаления
old readers/writers и истечения rollback window. Application rollback никогда не запускает
`alembic downgrade` и не восстанавливает backup поверх новых данных автоматически.

## Capacity и конфигурация

Перед parallel start проверяются `MemAvailable`, свободное место и число CPU. Пороговые переменные
`DEPLOY_MIN_CPU_COUNT`, `DEPLOY_MIN_AVAILABLE_MEMORY_MB` и
`DEPLOY_MIN_AVAILABLE_DISK_MB` являются fail-closed minimum, а не доказательством capacity. Owner
фиксирует фактические CPU/RAM/disk, текущую нагрузку и DB connection headroom перед production
approval. Timeout/readiness/drain/observation параметры перечислены в `.env.example`; менять их без
измерения только для прохождения gate запрещено.

`DEPLOY_WORKER_DRAIN_SECONDS` одновременно задаёт Compose grace period и timeout команды stop.
Значение должно быть больше измеренного worst-case времени одного worker cycle. Если после SIGTERM
нет текущего `worker_stopped`, rollout считается имеющим неопределённое состояние consumer, новый
worker не получает ownership, а оператор использует evidence для ручного разбора. Старые строки
логов переиспользованного slot не принимаются: boundary берётся из `StartedAt` текущего container.

Online migration gate анализирует только `upgrade()`. Для `expand` автоматически допускается лишь
`op.add_column` со статически проверяемым `nullable=True` без default/index/unique; обычные index и
constraint операции fail-closed. `backfill` допускает только один literal bounded `UPDATE ... WHERE`
и требует `online_rollout_batch_size` от 1 до 10000, `online_rollout_idempotent = True` и явное
описание bounds/idempotency. Остальные изменения требуют отдельного проверенного rollout плана, а
не обхода gate.

Оба slot используют один production `.env`, поэтому cookie/JWT secrets и server-owned auth state не
меняются при switch. Candidate smoke проверяет liveness, readiness/DB, document, matching hashed
asset, anonymous `401` auth boundary, public config и TMA-safe shell без credentials или записей.

## Bootstrap и production boundary

Существующий single-slot host не получает state/`edge_config` автоматически: первый bootstrap
требует отдельного owner-approved окна и может пересоздать только `edge`. Команда и preflight
зафиксированы в private operator runbook. Обычный deploy fail-closed, пока bootstrap не завершён.

Локально разрешены static/unit checks, Compose render, Caddy validation и production-like drill без
production credentials. Push/force-push remote `master`, bootstrap production, workflow rerun,
реальная migration, DNS/Cloudflare/secret action и public continuous probe требуют отдельного
owner approval. Локальные tests не доказывают production zero downtime, real Telegram client или
фактический host headroom.
