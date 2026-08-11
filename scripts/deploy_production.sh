#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_ROOT="/root/fit-mini-app"
readonly TARGET_SHA="${1:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly BASE_URL="${2:?usage: deploy_production.sh TARGET_SHA BASE_URL}"

cd "$EXPECTED_ROOT"

if [[ "$(pwd -P)" != "$EXPECTED_ROOT" ]]; then
  echo "Refusing to deploy outside $EXPECTED_ROOT" >&2
  exit 1
fi

if [[ ! -d .git ]]; then
  echo "$EXPECTED_ROOT is not a Git checkout" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "$EXPECTED_ROOT/.env is missing" >&2
  exit 1
fi

readonly CURRENT_SHA="$(git rev-parse HEAD)"
if [[ "$CURRENT_SHA" != "$TARGET_SHA" ]]; then
  echo "Checked-out revision $CURRENT_SHA does not match requested revision $TARGET_SHA" >&2
  exit 1
fi

echo "Enabling browser OAuth and keeping email registration disabled"
python3 scripts/configure_production_auth.py .env

echo "Validating Compose configuration for $TARGET_SHA"
docker compose config --quiet

stage_started=$SECONDS
echo "Pulling tested application images"
docker compose pull backend bot
echo "Application images pulled in $((SECONDS - stage_started))s"

stage_started=$SECONDS
echo "Creating a pre-deploy database backup"
python3 scripts/db_maintenance.py backup
echo "Database backup completed in $((SECONDS - stage_started))s"

stage_started=$SECONDS
echo "Starting application services"
# Target application services explicitly so the currently selected HTTPS/tunnel
# profile keeps running unchanged.
docker compose up \
  -d \
  --no-build \
  --wait \
  --wait-timeout 180 \
  backend worker bot support-bot
echo "Application services became ready in $((SECONDS - stage_started))s"

docker compose ps

stage_started=$SECONDS
echo "Running the external deployment smoke check"
python3 scripts/check_deployment.py "$BASE_URL"
echo "External smoke check completed in $((SECONDS - stage_started))s"

install -d -m 700 .artifacts/deployments
printf '%s\n' "$TARGET_SHA" > .artifacts/deployments/last-successful-revision
echo "Production deployment completed: $TARGET_SHA"
