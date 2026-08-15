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

- `https://your-fitness-coach.ru` — canonical public landing page (`www` redirects here);
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
For direct HTTPS, point the apex, `www`, and `app` DNS records to the server and recreate
the Caddy service once to apply the additional hosts. `www` is served only to redirect to the
canonical apex landing URL:

```console
docker compose --profile direct-https up -d --force-recreate caddy
```

For the remotely managed Cloudflare Tunnel, add the apex, `www`, and application public
hostnames and route all of them to `http://backend:8000` on the Compose network. Do not expose PostgreSQL or
the backend container port publicly. Keep the Telegram Mini App URL and all OAuth
callback URLs on the `app` hostname; the exact callbacks are listed in
[`web-auth.md`](web-auth.md).

### Search indexation contract

- `https://your-fitness-coach.ru/` is the only current indexable URL. It is self-canonical,
  listed in `/sitemap.xml`, and `/robots.txt` publishes that sitemap.
- Application, invitation and technical-auth HTML routes return `X-Robots-Tag: noindex, nofollow`.
  They deliberately remain crawlable enough for search engines to read that directive; `robots.txt`
  only disallows the API surface.
- Do not add a URL to the sitemap until it has public, factual, crawler-visible content and a
  self-canonical response. Future public content routes require an explicit metadata entry and
  truthful structured data before publication.
- The current Vite SPA has a static, no-JavaScript fallback for the landing only. Before adding
  further indexable JS routes, introduce an appropriate prerender/SSR mechanism rather than relying
  on client-side rendering. Keep public media dimensions/aspect ratios explicit, avoid blocking
  SEO-only JavaScript, and re-check responsive layout and Core Web Vitals during the relevant
  performance task.

Before changing DNS, verify the landing and application hosts locally or through
a temporary protected hostname. After the change, smoke-test `/`, `/app`,
`/health/ready`, one Telegram login and one browser login. DNS and proxy changes
are operational actions and are not performed by the repository deployment
script.

After deployment, inspect backend, worker and bot errors and confirm that due
notifications leave the queue. Keep the pre-deploy backup and previous image for
the retention period defined by the service owner.

## Automated production deployment

The `Deploy production` GitHub Actions workflow deploys successful pushes to
`master`. It connects to the existing checkout at `/root/fit-mini-app`, checks out
the exact revision that passed CI, creates a database backup, rebuilds the
application containers and runs the external smoke check. The active Caddy or
Cloudflare profile is left unchanged.

The server checkout is deployment-only: each run resets tracked application code
to the tested commit. Do not edit tracked files there. Ignored runtime state such
as `.env`, `.artifacts/` and Docker volumes is not removed by the reset.

Compose evaluates the backend, worker and bot build targets on every deployment.
Docker layer caching avoids rebuilding unchanged layers, and Compose recreates a
running container only when its resulting image or service configuration changed.
Because the frontend is compiled into the backend image, frontend changes update
the backend automatically; backend changes also update the worker, while bot-only
changes update the bot image.

Create a GitHub environment named `production` and add these environment secrets:

- `PROD_SSH_KEY`: the private half of a dedicated key that may SSH to the
  production server;
- `PROD_SSH_KNOWN_HOSTS`: the verified `known_hosts` entry for
  `app.your-fitness-coach.ru`.

The matching public SSH key must be present in `/root/.ssh/authorized_keys` on the
server. For a private GitHub repository, the server also needs separate read-only
GitHub credentials (prefer a repository deploy key) so `git fetch origin master`
can run non-interactively. Never reuse the production server host key as either
client key.

Before enabling the workflow, verify once on the server:

```console
cd /root/fit-mini-app
test -d .git && test -f .env
git fetch origin master
docker compose config --quiet
```

Manual production runs are available through the workflow's `workflow_dispatch`
trigger. Deployments are serialized and are not cancelled midway by newer pushes.

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
