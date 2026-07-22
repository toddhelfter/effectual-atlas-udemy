#!/usr/bin/env bash
set -euo pipefail

INPUT_ROOT="${1:-sandbox/udemy/user-course-activity}"
OUTPUT_ROOT="${2:-data/curated/udemy_user_course_activity}"
YEAR="${3:-2026}"
MONTH="${4:-07}"
DAY="${5:-20}"
HASH_SALT="${6:-udemy-default-salt}"
REPORT_PATH="${7:-data/curated/udemy_user_course_activity/last_run_report.json}"

PYTHONPATH="${PYTHONPATH:-}:src" /usr/local/bin/python3 -m atlas_data.curate_udemy \
  --input-root "$INPUT_ROOT" \
  --output-root "$OUTPUT_ROOT" \
  --year "$YEAR" \
  --month "$MONTH" \
  --day "$DAY" \
  --hash-salt "$HASH_SALT" \
  --report-path "$REPORT_PATH"
