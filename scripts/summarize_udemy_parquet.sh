#!/usr/bin/env bash
set -euo pipefail

INPUT_ROOT="${1:-data/raw/staging/atlas-staging-raw}"
JSON_OUTPUT="${2:-data/interim/udemy/raw_parquet_summary.json}"
CSV_OUTPUT="${3:-data/interim/udemy/raw_parquet_summary.csv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

PYTHONPATH="${PYTHONPATH:-}:src" "$PYTHON_BIN" -m atlas_data.summarize_udemy_parquet \
  --input-root "$INPUT_ROOT" \
  --json-output "$JSON_OUTPUT" \
  --csv-output "$CSV_OUTPUT"
