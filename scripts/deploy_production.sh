#!/usr/bin/env bash
set -Eeuo pipefail

readonly EXPECTED_ROOT="/root/fit-mini-app"
readonly TARGET_SHA="${1:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly BASE_URL="${2:?usage: deploy_production.sh TARGET_SHA BASE_URL}"
readonly PUBLIC_BASE_URL="${3:-https://your-fitness-coach.ru}"
readonly ROLLOUT_MODE="${4:-zero-downtime}"
readonly BACKEND_IMAGE="${BACKEND_IMAGE:?BACKEND_IMAGE must reference the tested backend image}"
readonly BOT_IMAGE="${BOT_IMAGE:?BOT_IMAGE must reference the tested bot image}"

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

case "$ROLLOUT_MODE" in
  zero-downtime)
    echo "Starting fail-closed blue/green rollout"
    python3 scripts/zero_downtime_deploy.py \
      deploy \
      "$TARGET_SHA" \
      "$BASE_URL" \
      "$PUBLIC_BASE_URL"
    ;;
  single-slot)
    echo "Starting explicitly authorized single-slot rollout with bounded downtime"
    python3 scripts/zero_downtime_deploy.py \
      single-slot \
      "$TARGET_SHA" \
      "$BASE_URL" \
      "$PUBLIC_BASE_URL"
    ;;
  *)
    echo "Unsupported rollout mode: $ROLLOUT_MODE" >&2
    exit 1
    ;;
esac

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

echo "Production deployment completed: $TARGET_SHA"
