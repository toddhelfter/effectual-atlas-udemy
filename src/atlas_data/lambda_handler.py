from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import boto3

from atlas_data.curate_udemy import CurateResult, curate_partition


def _download_partition(
    s3_client: Any,
    bucket: str,
    base_prefix: str,
    year: str,
    month: str,
    day: str,
    local_root: Path,
) -> Path:
    local_root.mkdir(parents=True, exist_ok=True)
    partition_prefix = (
        f"{base_prefix.rstrip('/')}/activity_year={year}/activity_month={month}/activity_day={day}/"
    )

    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=partition_prefix)

    downloaded = 0
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".parquet"):
                continue

            rel = key[len(base_prefix.rstrip("/")) + 1 :]
            local_path = local_root / rel
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3_client.download_file(bucket, key, str(local_path))
            downloaded += 1

    if downloaded == 0:
        raise FileNotFoundError(f"No parquet files found for s3://{bucket}/{partition_prefix}")

    return local_root


def _upload_curated_output(
    s3_client: Any,
    output_file: Path,
    output_bucket: str,
    output_prefix: str,
    year: str,
    month: str,
    day: str,
) -> str:
    key = (
        f"{output_prefix.rstrip('/')}/event_year={year}/event_month={month}/event_day={day}/"
        "udemy_user_course_activity_curated.parquet"
    )
    s3_client.upload_file(str(output_file), output_bucket, key)
    return f"s3://{output_bucket}/{key}"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bucket = event["bucket"]
    prefix = event.get("prefix", "udemy/user-course-activity")
    year = event["year"]
    month = event["month"]
    day = event["day"]

    output_bucket = event.get("output_bucket", bucket)
    output_prefix = event.get("output_prefix", "udemy-curated/user-course-activity")
    hash_salt = event.get("hash_salt", "udemy-default-salt")

    s3 = boto3.client("s3")

    local_download_root = Path("/tmp/udemy_raw")
    local_output_root = Path("/tmp/udemy_curated")

    if local_download_root.exists():
        shutil.rmtree(local_download_root)
    if local_output_root.exists():
        shutil.rmtree(local_output_root)

    download_root = _download_partition(
        s3_client=s3,
        bucket=bucket,
        base_prefix=prefix,
        year=year,
        month=month,
        day=day,
        local_root=local_download_root,
    )

    result: CurateResult = curate_partition(
        input_root=download_root,
        output_root=local_output_root,
        year=year,
        month=month,
        day=day,
        hash_salt=hash_salt,
    )

    destination_uri = _upload_curated_output(
        s3_client=s3,
        output_file=Path(result.output_file),
        output_bucket=output_bucket,
        output_prefix=output_prefix,
        year=year,
        month=month,
        day=day,
    )

    return {
        "status": "ok",
        "rows_in": result.rows_in,
        "rows_out": result.rows_out,
        "output_s3_uri": destination_uri,
        "partition": {"year": year, "month": month, "day": day},
    }


if __name__ == "__main__":
    sample_event = {
        "bucket": "effectual-atlas-landing-staging",
        "prefix": "udemy/user-course-activity",
        "year": "2026",
        "month": "07",
        "day": "20",
        "output_bucket": "effectual-atlas-landing-staging",
        "output_prefix": "udemy-curated/user-course-activity",
    }
    print(json.dumps(handler(sample_event, None), indent=2))
