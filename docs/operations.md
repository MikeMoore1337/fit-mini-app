# Operations runbook

This document describes the repository-managed part of deployment and recovery.
Provider-specific DNS, tunnel, object-storage and secret-management procedures
must live in the private infrastructure documentation.

## Safety rules

- Never commit `.env` or database dumps. Repository scripts only accept dump paths
  below `.artifacts/`, which is gitignored and excluded from Docker build contexts.
- Run backup, restore and migration commands from the repository root.
- Never use a production database for integration tests.
- Keep the previous application image/revision available until post-deploy checks
  and the observation window have completed.
- Prefer a forward fix. Do not run `alembic downgrade` automatically: application
  rollback is safe only while migrations remain backward compatible.

## Pre-deploy

1. Review the migration diff and identify destructive or long-locking operations.
2. Validate configuration without printing resolved secrets:

   ```console
   docker compose config --quiet
   ```

3. Build the exact revision that will be deployed:

   ```console
   docker compose build backend setup worker bot
   ```

4. Create a database backup. The command reads database credentials only inside
   the running `db` container:

   ```console
   py scripts/db_maintenance.py backup
   ```

5. Copy the resulting `.artifacts/backups/*.dump` to encrypted external storage.
   A local named volume and a local dump are not independent backups.

## Deploy and verify

The current Compose topology runs the one-shot `setup` service before backend;
`setup` applies Alembic migrations under a PostgreSQL advisory lock and then runs
the idempotent seed command.

```console
docker compose up -d --build
docker compose ps
py scripts/check_deployment.py https://app.your-fitness-coach.ru
```

For direct HTTPS use the `direct-https` profile; for Cloudflare Tunnel use the
`cloudflare` profile. Do not enable both accidentally:

```console
docker compose --profile direct-https up -d
docker compose --profile cloudflare up -d
```

### Public website and web application domains

The intended production layout uses two hostnames backed by the same API and
database:

- `https://your-fitness-coach.ru` — public landing page;
- `https://app.your-fitness-coach.ru/app` — authenticated web application and
  Telegram Mini App;
- `https://app.your-fitness-coach.ru/join/<token>` — universal coach invitation.

Set the following non-secret values in the production `.env`:

```dotenv
APP_DOMAIN=app.your-fitness-coach.ru
LANDING_DOMAIN=your-fitness-coach.ru
FRONTEND_BASE_URL=https://app.your-fitness-coach.ru
```

`LANDING_DOMAIN` is optional so an existing single-host deployment remains valid.
For direct HTTPS, point the apex and `app` DNS records to the server and recreate
the Caddy service once to apply the additional host:

```console
docker compose --profile direct-https up -d --force-recreate caddy
```

For the remotely managed Cloudflare Tunnel, add both public hostnames and route
both to `http://backend:8000` on the Compose network. Do not expose PostgreSQL or
the backend container port publicly. Keep the Telegram Mini App URL and all OAuth
callback URLs on the `app` hostname; the exact callbacks are listed in
[`web-auth.md`](web-auth.md).

Before changing DNS, verify the landing and application hosts locally or through
a temporary protected hostname. After the change, smoke-test `/`, `/app`,
`/health/ready`, one Telegram login and one browser login. DNS and proxy changes
are operational actions and are not performed by the repository deployment
script.

After deployment, inspect backend, worker and bot errors and confirm that due
notifications leave the queue. Keep the pre-deploy backup and previous image for
the retention period defined by the service owner.

## Automated production deployment

GitHub Actions workflow `Deploy production` автоматически разворачивает успешные
push в `master`. Триггер остаётся автоматическим, но deployment выполняется только
для актуального `origin/master`: queued run для уже заменённого SHA завершается без
изменения production.

CI собирает backend и bot один раз, сканирует образы и публикует их в GHCR с тегом
точного commit SHA и OCI-меткой `org.opencontainers.image.revision`. Production
сначала скачивает оба образа и проверяет, что их тег и revision label совпадают с
SHA, прошедшим CI. Несовпадение блокирует deployment до миграций и перезапуска
сервисов.

Server checkout предназначен только для deployment: каждый запуск сбрасывает
tracked application code до проверенного commit. Не редактируйте tracked files на
сервере. Игнорируемое runtime state (`.env`, `.artifacts/` и Docker volumes) при
reset не удаляется.

Перед запуском новой версии pipeline валидирует Compose configuration, создаёт
PostgreSQL custom-format backup и проверяет его читаемость через
`pg_restore --list`. Затем Compose применяет setup/migrations, запускает backend,
worker и bot и ждёт readiness. Внешний smoke check проверяет `/health/ready`,
`/api/v1/public/config` и `/app`, включая `app_env=prod` и безопасные production
auth flags. Только после этих проверок SHA записывается как
`.artifacts/deployments/last-successful-revision`.

Активный Caddy или Cloudflare profile не переключается. Frontend уже включён в
проверенный backend image; backend image также используется worker, а bot получает
собственный проверенный image.

Создайте GitHub environment `production` и добавьте environment secrets:

- `PROD_SSH_KEY`: приватная часть отдельного ключа для SSH-доступа к production;
- `PROD_SSH_KNOWN_HOSTS`: проверенная запись `known_hosts` для
  `app.your-fitness-coach.ru`.

Соответствующий публичный SSH key должен находиться в
`/root/.ssh/authorized_keys`. Для private repository серверу также нужны отдельные
read-only GitHub credentials (предпочтительно repository deploy key), чтобы
`git fetch origin master` работал non-interactively. Не используйте production
server host key как client key.

Перед включением workflow один раз проверьте на сервере:

```console
cd /root/fit-mini-app
test -d .git && test -f .env
git fetch origin master
docker compose config --quiet
```

Ручной production run доступен через `workflow_dispatch`. Deployments выполняются
последовательно и не прерываются новым push посередине; устаревший queued SHA при
этом безопасно пропускается до изменения application state.

## Application rollback

1. Stop only the application writers, leaving PostgreSQL running:

   ```console
   docker compose stop backend worker bot
   ```

2. Deploy the previous immutable image/revision.
3. If its schema is compatible, start it and run the read-only smoke check. Do not
   downgrade the database merely because application code was rolled back.
4. If the migration is incompatible, keep writers stopped and follow database
   restore below. Record the incident and data-loss window before proceeding.

## Database restore

Restore is destructive: `pg_restore --clean --if-exists` replaces objects in the
configured database. The helper requires an exact database-name confirmation and
automatically creates a fresh safety dump before changing anything.

1. Place the selected custom-format dump below `.artifacts/`.
2. Stop all writers:

   ```console
   docker compose stop backend worker bot
   ```

3. Read the target database name without exposing credentials:

   ```console
   docker compose exec -T db sh -ec 'printf "%s\n" "$POSTGRES_DB"'
   ```

4. Restore with an exact confirmation:

   ```console
   py scripts/db_maintenance.py restore .artifacts/backups/fitminiapp-TIMESTAMP.dump --confirm-database fitminiapp
   ```

5. Run the current setup/migrations, start services and smoke-test:

   ```console
   docker compose run --rm setup
   docker compose up -d backend worker bot
   py scripts/check_deployment.py https://app.your-fitness-coach.ru
   ```

If restore fails, keep writers stopped. The script prints the path of the automatic
pre-restore safety backup.

## Backup policy and restore drills

Define explicit RPO/RTO, encrypted off-host storage, retention and access control.
At minimum, automate daily dumps and test a restore into an isolated PostgreSQL
instance regularly. A backup is not considered valid until the migrated-stack
smoke test succeeds against its restored copy.

## Incident evidence

Preserve the deployment revision, timestamps, structured API/worker logs, request
ID supplied to the affected user, migration output and health-check results. Never
attach `.env`, database dumps or authentication tokens to a public issue.
