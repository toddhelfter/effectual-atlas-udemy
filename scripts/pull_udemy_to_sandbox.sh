#!/usr/bin/env bash
set -euo pipefail

SOURCE_URI="${1:-s3://effectual-atlas-landing-staging/udemy/user-course-activity/}"
TARGET_DIR="${2:-sandbox/udemy/user-course-activity}"

mkdir -p "$TARGET_DIR"
aws s3 sync "$SOURCE_URI" "$TARGET_DIR" --exclude '*' --include '*.parquet'

echo "Pulled Udemy parquet files to $TARGET_DIR"
