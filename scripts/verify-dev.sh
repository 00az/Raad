#!/usr/bin/env bash
set -euo pipefail

raad_workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
raad_service="$raad_workspace/../money-service"
raad_mobile="$raad_workspace/../mobile"

for executable in uv flutter docker; do
  command -v "$executable" >/dev/null || { echo "Missing required tool: $executable" >&2; exit 1; }
done
: "${RAAD_IOS_DEVICE_ID:?Set the actual iOS simulator ID}"
: "${RAAD_ANDROID_DEVICE_ID:?Set the actual Android emulator ID}"
: "${TEST_USERS_SECRET_ARN:?Set the dev runtime fixture secret ARN}"
: "${USER_POOL_ID:?Set the dev user pool}"
: "${USER_POOL_CLIENT_ID:?Set the dev mobile client}"
: "${MONEY_API_BASE_URL:?Set the real dev public API URL}"
test -f "$raad_mobile/config/dev.json" || { echo "Mobile dev configuration is not ready" >&2; exit 1; }
test -f "$raad_mobile/integration_test/walking_skeleton_test.dart" || { echo "Co-engineer mobile integration test is not ready" >&2; exit 1; }

# Every invocation creates new isolated API/iOS/Android pairs through supported setup.
# Passwords stay in Secrets Manager; neither arguments nor this script print them.
uv run --project "$raad_service" python "$raad_service/scripts/setup_dev_users.py"
RAAD_FIXTURE_PHASE=api uv run --project "$raad_service" python "$raad_service/scripts/verify_dev.py"

cd "$raad_mobile"
RAAD_FIXTURE_PHASE=ios flutter test integration_test/walking_skeleton_test.dart -d "$RAAD_IOS_DEVICE_ID" --dart-define-from-file=config/dev.json
RAAD_FIXTURE_PHASE=android flutter test integration_test/walking_skeleton_test.dart -d "$RAAD_ANDROID_DEVICE_ID" --dart-define-from-file=config/dev.json
