#!/usr/bin/env bash
set -euo pipefail

INPUT_ROOT="${1:-sandbox/udemy/user-course-activity}"
JSON_OUTPUT="${2:-sandbox/analysis/udemy_data_dictionary.json}"
MARKDOWN_OUTPUT="${3:-sandbox/analysis/udemy_data_dictionary.md}"

PYTHONPATH="${PYTHONPATH:-}:src" /usr/local/bin/python3 -m atlas_data.profile_udemy_schema \
  --input-root "$INPUT_ROOT" \
  --json-output "$JSON_OUTPUT" \
  --markdown-output "$MARKDOWN_OUTPUT"
