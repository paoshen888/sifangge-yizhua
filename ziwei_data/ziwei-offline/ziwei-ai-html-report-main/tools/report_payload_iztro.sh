#!/usr/bin/env bash
# 可选：iztro + 与 Python 相同的真太阳时口径（推荐）
# 需: Node + 本目录 npm install
#
# 默认 IZTRO_MODE=true-solar：先用 Python 算真太阳时，再传给 iztro 安星，再拼上下文。
# 环境变量：SOLAR TIME GENDER 必填；BIRTHPLACE 可选；TARGET_YEAR 默认 2026
#
# 仅钟表、不要真太阳（与 App 输入一致）：IZTRO_MODE=raw-clock ./tools/report_payload_iztro.sh -- --solar ... --time ... --gender ...
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
TARGET="${TARGET_YEAR:-2026}"
MODE="${IZTRO_MODE:-true-solar}"

if [[ "$MODE" == "true-solar" ]]; then
  : "${SOLAR:?}" "${TIME:?}" "${GENDER:?}"
  PY_ARGS=(--solar "$SOLAR" --time "$TIME" --gender "$GENDER" --target-year "$TARGET" --emit-iztro-birth-json)
  [[ -n "${BIRTHPLACE:-}" ]] && PY_ARGS+=(--birthplace "$BIRTHPLACE")
  [[ "${DISABLE_TRUE_SOLAR:-}" == "1" ]] && PY_ARGS+=(--disable-true-solar-time)
  python3 tools/ziwei_offline.py "${PY_ARGS[@]}" | node tools/chart_iztro.cjs --birth-json - | python3 tools/ziwei_offline.py --from-chart-json --target-year "$TARGET" --format json
else
  exec node tools/chart_iztro.cjs "$@" | python3 tools/ziwei_offline.py --from-chart-json --target-year "$TARGET" --format json
fi
