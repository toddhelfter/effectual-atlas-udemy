from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

YEAR_PARTITION_PATTERN = re.compile(r"activity_year=(\d{4})")
MONTH_PARTITION_PATTERN = re.compile(r"activity_month=(\d{2})")
DAY_PARTITION_PATTERN = re.compile(r"activity_day=(\d{2})")


@dataclass(frozen=True)
class FileSummary:
    file_path: str
    file_size_bytes: int
    rows: int
    columns: int
    extract_year: str
    extract_month: str
    extract_day: str


def infer_partitions(path: Path) -> tuple[str, str, str]:
    joined = str(path)
    year_match = YEAR_PARTITION_PATTERN.search(joined)
    month_match = MONTH_PARTITION_PATTERN.search(joined)
    day_match = DAY_PARTITION_PATTERN.search(joined)

    year = year_match.group(1) if year_match else "unknown"
    month = month_match.group(1) if month_match else "unknown"
    day = day_match.group(1) if day_match else "unknown"
    return year, month, day


def summarize_file(path: Path) -> FileSummary:
    df = pd.read_parquet(path)
    year, month, day = infer_partitions(path)
    return FileSummary(
        file_path=str(path),
        file_size_bytes=path.stat().st_size,
        rows=len(df),
        columns=len(df.columns),
        extract_year=year,
        extract_month=month,
        extract_day=day,
    )


def summarize_directory(input_root: Path) -> list[FileSummary]:
    parquet_files = sorted(input_root.rglob("*.parquet"))
    return [summarize_file(path) for path in parquet_files]


def write_outputs(results: list[FileSummary], json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [item.__dict__ for item in results]

    payload = {
        "files_count": len(results),
        "rows_total": sum(item.rows for item in results),
        "size_total_bytes": sum(item.file_size_bytes for item in results),
        "details": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    pd.DataFrame(rows).to_csv(csv_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Udemy raw parquet extracts by day partitions.")
    parser.add_argument(
        "--input-root",
        default="data/raw/staging/atlas-staging-raw",
        help="Path to raw Udemy parquet files.",
    )
    parser.add_argument(
        "--json-output",
        default="data/interim/udemy/raw_parquet_summary.json",
        help="Path to write JSON summary.",
    )
    parser.add_argument(
        "--csv-output",
        default="data/interim/udemy/raw_parquet_summary.csv",
        help="Path to write CSV summary.",
    )
    args = parser.parse_args()

    input_root = Path(args.input_root)
    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")

    results = summarize_directory(input_root)
    if not results:
        print(f"No parquet files found under {input_root}")
        return

    write_outputs(results, Path(args.json_output), Path(args.csv_output))
    print(
        f"Summarized {len(results)} parquet files, "
        f"{sum(item.rows for item in results)} rows total, "
        f"{sum(item.file_size_bytes for item in results)} bytes total."
    )


if __name__ == "__main__":
    main()
