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
py scripts/check_deployment.py https://your-domain.example
```

For direct HTTPS use the `direct-https` profile; for Cloudflare Tunnel use the
`cloudflare` profile. Do not enable both accidentally:

```console
docker compose --profile direct-https up -d
docker compose --profile cloudflare up -d
```

After deployment, inspect backend, worker and bot errors and confirm that due
notifications leave the queue. Keep the pre-deploy backup and previous image for
the retention period defined by the service owner.

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
   py scripts/check_deployment.py https://your-domain.example
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
