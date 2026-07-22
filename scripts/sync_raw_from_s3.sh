#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-config/s3_sources.yaml}"
ENVIRONMENT="${2:-all}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

PYTHONPATH="${PYTHONPATH:-}:src" "$PYTHON_BIN" -m atlas_data.ingest_s3 --config "$CONFIG_PATH" --environment "$ENVIRONMENT"
