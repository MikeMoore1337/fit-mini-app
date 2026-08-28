#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_ROOT="/root/fit-mini-app"
readonly TARGET_SHA="${1:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly BASE_URL="${2:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly PUBLIC_BASE_URL="${3:-https://your-fitness-coach.ru}"

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

require_digest_ref() {
  local key="$1"
  local value
  value="$(sed -n "s/^${key}=//p" .env | tail -n 1)"
  if [[ ! "$value" =~ @sha256:[0-9a-f]{64}$ ]]; then
    echo "$key must be an immutable image reference ending in @sha256:<64 hex>" >&2
    exit 1
  fi
}

require_digest_ref POSTGRES_IMAGE
require_digest_ref CADDY_IMAGE
require_digest_ref CLOUDFLARED_IMAGE

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
docker compose pull backend bot edge
echo "Application images pulled in $((SECONDS - stage_started))s"

echo "Validating fail-closed production runtime configuration"
docker compose run --rm --no-deps backend \
  python -c "from fitminiapp_api.core.config import settings; assert settings.app_env == 'prod'; print('Backend production config is valid')"
docker compose run --rm --no-deps bot \
  python -c "from fitminiapp_bot.config import settings; assert settings.app_env == 'prod'; print('Bot production config is valid')"

stage_started=$SECONDS
echo "Creating a pre-deploy database backup"
python3 scripts/db_maintenance.py backup
echo "Database backup completed in $((SECONDS - stage_started))s"

stage_started=$SECONDS
echo "Starting application services"
# Target application services explicitly so the currently selected HTTPS/tunnel
# profile stays selected while its active gateway receives the new edge route.
gateway_services=(edge)
if docker compose ps --services --status running | grep -qx caddy; then
  gateway_services+=(caddy)
fi
if docker compose ps --services --status running | grep -qx cloudflared; then
  gateway_services+=(cloudflared)
fi
docker compose up \
  -d \
  --no-build \
  --remove-orphans \
  --wait \
  --wait-timeout 180 \
  backend worker bot "${gateway_services[@]}"
echo "Application services became ready in $((SECONDS - stage_started))s"

docker compose ps

stage_started=$SECONDS
echo "Running the external deployment smoke check"
python3 scripts/check_deployment.py "$BASE_URL" --expected-environment prod
python3 scripts/check_seo_surface.py "$PUBLIC_BASE_URL"
echo "External smoke check completed in $((SECONDS - stage_started))s"

install -d -m 700 .artifacts/deployments
printf '%s\n' "$TARGET_SHA" > .artifacts/deployments/last-successful-revision
echo "Production deployment completed: $TARGET_SHA"
