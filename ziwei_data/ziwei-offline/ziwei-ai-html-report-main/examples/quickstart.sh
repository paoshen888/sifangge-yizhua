#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 "$ROOT_DIR/tools/ziwei_offline.py" \
  --solar 1996-01-06 \
  --time 11:30 \
  --gender female \
  --birthplace "广东省佛山市顺德区" \
  --geocode-mode offline \
  --target-year 2026 \
  --format json
