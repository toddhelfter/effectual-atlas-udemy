from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def load_raw_dataset(input_root: Path) -> pd.DataFrame:
    files = sorted(input_root.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found under {input_root}")

    frames = [pd.read_parquet(path) for path in files]
    return pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]


def normalize_email_column(df: pd.DataFrame) -> pd.DataFrame:
    if "user_email" not in df.columns:
        raise KeyError("Expected field 'user_email' was not found in dataset")

    normalized = df.copy()
    normalized["email_address"] = normalized["user_email"].astype(str).str.strip().str.lower()
    return normalized


def build_detail_report(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "email_address",
        "course_title",
        "course_category",
        "completion_ratio",
        "num_video_consumed_minutes",
        "course_enroll_date",
        "course_start_date",
        "course_completion_date",
        "course_first_completion_date",
        "last_activity_date",
        "ingestion_timestamp",
    ]
    available = [column for column in columns if column in df.columns]
    details = df[available].copy()
    return details.sort_values(["email_address", "last_activity_date", "course_title"], na_position="last")


def build_summary_report(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("email_address", dropna=False)
        .agg(
            activity_rows=("email_address", "size"),
            distinct_courses=("course_title", "nunique"),
            avg_completion_ratio=("completion_ratio", "mean"),
            min_completion_ratio=("completion_ratio", "min"),
            max_completion_ratio=("completion_ratio", "max"),
            total_video_minutes=("num_video_consumed_minutes", "sum"),
            first_seen_activity=("last_activity_date", "min"),
            last_seen_activity=("last_activity_date", "max"),
        )
        .reset_index()
        .sort_values(["activity_rows", "email_address"], ascending=[False, True])
    )

    return grouped


def write_outputs(summary_df: pd.DataFrame, detail_df: pd.DataFrame, output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)

    summary_csv = output_root / "training_by_email_summary.csv"
    detail_csv = output_root / "training_by_email_details.csv"
    summary_json = output_root / "training_by_email_summary.json"

    summary_df.to_csv(summary_csv, index=False)
    detail_df.to_csv(detail_csv, index=False)

    payload = {
        "emails_count": int(summary_df["email_address"].nunique(dropna=True)),
        "rows_count": int(detail_df.shape[0]),
        "summary": summary_df.to_dict(orient="records"),
    }
    summary_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report Udemy training activity grouped by email address from raw parquet extracts."
    )
    parser.add_argument(
        "--input-root",
        default="sandbox/udemy/user-course-activity",
        help="Path containing raw parquet files.",
    )
    parser.add_argument(
        "--output-root",
        default="sandbox/analysis",
        help="Directory to write reporting outputs.",
    )
    parser.add_argument(
        "--email-address",
        default=None,
        help="Optional specific email address to filter for one employee.",
    )
    args = parser.parse_args()

    df = load_raw_dataset(Path(args.input_root))
    df = normalize_email_column(df)

    if args.email_address:
        target = args.email_address.strip().lower()
        df = df[df["email_address"] == target]

    if df.empty:
        raise ValueError("No records available for the selected scope")

    summary_df = build_summary_report(df)
    detail_df = build_detail_report(df)
    write_outputs(summary_df, detail_df, Path(args.output_root))

    print(
        f"Generated reports for {summary_df.shape[0]} email(s) and {detail_df.shape[0]} activity row(s). "
        f"Outputs in {args.output_root}."
    )


if __name__ == "__main__":
    main()
