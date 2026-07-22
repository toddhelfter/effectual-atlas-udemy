#!/usr/bin/env bash
set -euo pipefail

INPUT_ROOT="${1:-data/raw/staging/atlas-staging-raw}"
OUTPUT_ROOT="${2:-data/processed/udemy}"
REPORT_PATH="${3:-data/processed/udemy/process_report.json}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

PYTHONPATH="${PYTHONPATH:-}:src" "$PYTHON_BIN" -m atlas_data.process_udemy_extracts \
  --input-root "$INPUT_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --report-path "$REPORT_PATH"
