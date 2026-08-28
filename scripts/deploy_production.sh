#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_ROOT="/root/fit-mini-app"
readonly TARGET_SHA="${1:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly BASE_URL="${2:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly PUBLIC_BASE_URL="${3:-https://your-fitness-coach.ru}"
readonly BACKEND_IMAGE="${BACKEND_IMAGE:?BACKEND_IMAGE must reference the tested backend image}"
readonly BOT_IMAGE="${BOT_IMAGE:?BOT_IMAGE must reference the tested bot image}"

verify_image_revision() {
  local image_ref="$1"
  local actual_revision

  actual_revision="$(
    docker image inspect \
      --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' \
      "$image_ref"
  )"
  if [[ "$actual_revision" != "$TARGET_SHA" ]]; then
    echo "Image $image_ref revision $actual_revision does not match $TARGET_SHA" >&2
    exit 1
  fi
}

profile_report_has_api_error() {
  python3 -c '
import json
import sys

report = json.load(sys.stdin)
identity_status = report.get("identity", {}).get("status")
field_statuses = {
    field.get("status")
    for field in report.get("fields", {}).values()
    if isinstance(field, dict)
}
raise SystemExit(0 if identity_status == "API_ERROR" or "API_ERROR" in field_statuses else 1)
'
}

cd "$EXPECTED_ROOT"

if [[ ! "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "TARGET_SHA must be a full lowercase Git commit SHA" >&2
  exit 1
fi

if [[ "$BACKEND_IMAGE" != *:"$TARGET_SHA" || "$BOT_IMAGE" != *:"$TARGET_SHA" ]]; then
  echo "Application image tags must end with the tested revision $TARGET_SHA" >&2
  exit 1
fi

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
verify_image_revision "$BACKEND_IMAGE"
verify_image_revision "$BOT_IMAGE"
echo "Application images pulled in $((SECONDS - stage_started))s"

echo "Validating fail-closed production runtime configuration"
docker run --rm --network none --env-file .env "$BACKEND_IMAGE" \
  python -c "from fitminiapp_api.core.config import settings; assert settings.app_env == 'prod'; print('Backend production config is valid')"
docker run --rm --network none --env-file .env "$BOT_IMAGE" \
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
# A failed rollout can leave the selected public gateway stopped after its
# backend dependency was recreated. Preserve that selection during recovery.
if docker compose ps --services --all | grep -qx caddy; then
  gateway_services+=(caddy)
fi
if docker compose ps --services --all | grep -qx cloudflared; then
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

echo "Checking the public Telegram bot profile"
set +e
profile_check_output="$(
  docker compose run --rm --no-deps bot \
    python -m fitminiapp_bot.profile_sync check
)"
profile_check_status=$?
set -e
printf '%s\n' "$profile_check_output"
profile_sync_result="pending"

case "$profile_check_status" in
  0)
    echo "Public Telegram bot profile already matches the canonical contract"
    profile_sync_result="matched"
    ;;
  1)
    echo "Applying the bounded public Telegram bot profile diff"
    set +e
    profile_apply_output="$(
      docker compose run --rm --no-deps bot \
        python -m fitminiapp_bot.profile_sync apply
    )"
    profile_apply_status=$?
    set -e
    printf '%s\n' "$profile_apply_output"
    if [[ "$profile_apply_status" -eq 0 ]]; then
      echo "Public Telegram Bot API fields were applied and read back"
      profile_sync_result="applied"
    elif printf '%s\n' "$profile_apply_output" | profile_report_has_api_error; then
      echo "Telegram Bot API is unavailable; metadata remains pending" >&2
    else
      echo "Public Telegram bot profile apply failed safely" >&2
      exit "$profile_apply_status"
    fi
    ;;
  *)
    if printf '%s\n' "$profile_check_output" | profile_report_has_api_error; then
      echo "Telegram Bot API is unavailable; metadata remains pending" >&2
    else
      echo "Public Telegram bot profile check failed safely" >&2
      exit "$profile_check_status"
    fi
    ;;
esac
echo "Public Telegram bot profile sync result: $profile_sync_result"
echo "Review owner actions in the profile reports when Telegram Bot API is reachable"

install -d -m 700 .artifacts/deployments
printf '%s\n' "$TARGET_SHA" > .artifacts/deployments/last-successful-revision
echo "Production deployment completed: $TARGET_SHA"
