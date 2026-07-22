#!/usr/bin/env bash
set -euo pipefail

INPUT_ROOT="${1:-sandbox/udemy/user-course-activity}"
OUTPUT_ROOT="${2:-sandbox/analysis}"
EMAIL_ADDRESS="${3:-}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -n "$EMAIL_ADDRESS" ]]; then
  PYTHONPATH="${PYTHONPATH:-}:src" "$PYTHON_BIN" -m atlas_data.report_trainings_by_email \
    --input-root "$INPUT_ROOT" \
    --output-root "$OUTPUT_ROOT" \
    --email-address "$EMAIL_ADDRESS"
else
  PYTHONPATH="${PYTHONPATH:-}:src" "$PYTHON_BIN" -m atlas_data.report_trainings_by_email \
    --input-root "$INPUT_ROOT" \
    --output-root "$OUTPUT_ROOT"
fi
