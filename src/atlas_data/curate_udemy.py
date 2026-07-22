from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_RAW_FIELDS = [
    "course_id",
    "course_title",
    "course_category",
    "course_duration",
    "completion_ratio",
    "num_video_consumed_minutes",
    "course_enroll_date",
    "course_start_date",
    "course_completion_date",
    "course_first_completion_date",
    "last_activity_date",
    "user_email",
    "user_name",
    "user_surname",
    "user_role",
    "is_assigned",
    "ingestion_timestamp",
    "env",
]


@dataclass(frozen=True)
class CurateResult:
    output_file: str
    rows_in: int
    rows_out: int
    partition_year: str
    partition_month: str
    partition_day: str


def _ensure_fields(df: pd.DataFrame) -> pd.DataFrame:
    patched = df.copy()
    for field in REQUIRED_RAW_FIELDS:
        if field not in patched.columns:
            patched[field] = pd.NA
    return patched


def _parse_ts(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors="coerce")


def _hash_email(series: pd.Series, salt: str) -> pd.Series:
    def hasher(value: Any) -> str | None:
        if pd.isna(value):
            return None
        normalized = str(value).strip().lower()
        digest = hashlib.sha256(f"{salt}|{normalized}".encode("utf-8")).hexdigest()
        return digest

    return series.apply(hasher)


def _primary_category(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .apply(lambda raw: raw.split(",")[0].strip() if raw.strip() else None)
    )


def _category_count(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .apply(lambda raw: len([item for item in raw.split(",") if item.strip()]) if raw.strip() else 0)
    )


def curate_dataframe(
    raw_df: pd.DataFrame,
    partition_year: str,
    partition_month: str,
    partition_day: str,
    hash_salt: str,
) -> pd.DataFrame:
    df = _ensure_fields(raw_df)

    curated = pd.DataFrame()
    curated["learner_email_sha256"] = _hash_email(df["user_email"], hash_salt)
    curated["learner_given_name"] = df["user_name"].astype("string")
    curated["learner_surname"] = df["user_surname"].astype("string")
    curated["learner_role"] = df["user_role"].astype("string")

    curated["course_id"] = pd.to_numeric(df["course_id"], errors="coerce").astype("Int64")
    curated["course_title"] = df["course_title"].astype("string")
    curated["course_category"] = df["course_category"].astype("string")
    curated["course_primary_category"] = _primary_category(df["course_category"]).astype("string")
    curated["course_category_count"] = _category_count(df["course_category"]).astype("Int64")

    curated["course_duration_minutes"] = pd.to_numeric(df["course_duration"], errors="coerce")
    curated["video_consumed_minutes"] = pd.to_numeric(df["num_video_consumed_minutes"], errors="coerce")
    curated["completion_ratio_pct"] = pd.to_numeric(df["completion_ratio"], errors="coerce")
    curated["is_assigned"] = df["is_assigned"].astype("boolean")

    curated["enrolled_at"] = _parse_ts(df["course_enroll_date"])
    curated["started_at"] = _parse_ts(df["course_start_date"])
    curated["completed_at"] = _parse_ts(df["course_completion_date"])
    curated["first_completed_at"] = _parse_ts(df["course_first_completion_date"])
    curated["source_ingested_at"] = _parse_ts(df["ingestion_timestamp"])
    curated["last_activity_date"] = pd.to_datetime(df["last_activity_date"], errors="coerce").dt.date

    curated["source_environment"] = df["env"].astype("string")
    curated["event_year"] = partition_year
    curated["event_month"] = partition_month
    curated["event_day"] = partition_day
    curated["record_loaded_at"] = pd.Timestamp.now("UTC")

    return curated


def _partition_files(input_root: Path, year: str, month: str, day: str) -> list[Path]:
    pattern = (
        input_root
        / f"activity_year={year}"
        / f"activity_month={month}"
        / f"activity_day={day}"
    )
    if not pattern.exists():
        return []
    return sorted(pattern.rglob("*.parquet"))


def curate_partition(
    input_root: Path,
    output_root: Path,
    year: str,
    month: str,
    day: str,
    hash_salt: str,
) -> CurateResult:
    files = _partition_files(input_root, year, month, day)
    if not files:
        raise FileNotFoundError(
            f"No parquet files found for partition activity_year={year}/activity_month={month}/activity_day={day}"
        )

    frames = [pd.read_parquet(path) for path in files]
    raw_df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    curated = curate_dataframe(raw_df, year, month, day, hash_salt)

    output_dir = output_root / f"event_year={year}" / f"event_month={month}" / f"event_day={day}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "udemy_user_course_activity_curated.parquet"
    curated.to_parquet(output_file, index=False)

    return CurateResult(
        output_file=str(output_file),
        rows_in=len(raw_df),
        rows_out=len(curated),
        partition_year=year,
        partition_month=month,
        partition_day=day,
    )


def write_report(path: Path, result: CurateResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.__dict__, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate Udemy raw parquet partition into analytics-ready schema.")
    parser.add_argument("--input-root", default="sandbox/udemy/user-course-activity")
    parser.add_argument("--output-root", default="data/curated/udemy_user_course_activity")
    parser.add_argument("--year", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--day", required=True)
    parser.add_argument("--hash-salt", default="udemy-default-salt")
    parser.add_argument("--report-path", default="data/curated/udemy_user_course_activity/last_run_report.json")
    args = parser.parse_args()

    result = curate_partition(
        input_root=Path(args.input_root),
        output_root=Path(args.output_root),
        year=args.year,
        month=args.month,
        day=args.day,
        hash_salt=args.hash_salt,
    )

    write_report(Path(args.report_path), result)
    print(
        f"Curated partition {args.year}-{args.month}-{args.day}: "
        f"rows_in={result.rows_in}, rows_out={result.rows_out}, output={result.output_file}"
    )


if __name__ == "__main__":
    main()
