from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".parquet", ".xlsx", ".xls", ".json", ".jsonl"}
MONTH_PATTERN = re.compile(r"(20\d{2})[-_]?([01]\d)")
YEAR_PARTITION_PATTERN = re.compile(r"activity_year=(\d{4})")
MONTH_PARTITION_PATTERN = re.compile(r"activity_month=(\d{2})")
DAY_PARTITION_PATTERN = re.compile(r"activity_day=(\d{2})")


@dataclass(frozen=True)
class ProcessResult:
    input_files: int
    output_file: str
    rows: int
    columns: int
    extract_year: str
    extract_month: str
    extract_day: str


def discover_files(input_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in input_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def read_by_extension(path: Path) -> pd.DataFrame:
    readers: dict[str, Callable[[Path], pd.DataFrame]] = {
        ".csv": lambda p: pd.read_csv(p),
        ".parquet": lambda p: pd.read_parquet(p),
        ".xlsx": lambda p: pd.read_excel(p),
        ".xls": lambda p: pd.read_excel(p),
        ".json": lambda p: pd.read_json(p),
        ".jsonl": lambda p: pd.read_json(p, lines=True),
    }
    return readers[path.suffix.lower()](path)


def infer_extract_month(path: Path) -> str:
    candidates = [path.name, str(path.parent)]
    for candidate in candidates:
        match = MONTH_PATTERN.search(candidate)
        if not match:
            continue
        year, month = match.groups()
        if 1 <= int(month) <= 12:
            return f"{year}-{month}"
    return "unknown"


def infer_extract_partitions(path: Path) -> tuple[str, str, str]:
    joined = str(path)

    year_match = YEAR_PARTITION_PATTERN.search(joined)
    month_match = MONTH_PARTITION_PATTERN.search(joined)
    day_match = DAY_PARTITION_PATTERN.search(joined)

    year = year_match.group(1) if year_match else "unknown"
    month = month_match.group(1) if month_match else "unknown"
    day = day_match.group(1) if day_match else "unknown"

    if month != "unknown" and not (1 <= int(month) <= 12):
        month = "unknown"
    if day != "unknown" and not (1 <= int(day) <= 31):
        day = "unknown"

    if year == "unknown" or month == "unknown":
        fallback_month = infer_extract_month(path)
        if fallback_month != "unknown":
            year, month = fallback_month.split("-")

    return year, month, day


def normalize_dataframe(
    df: pd.DataFrame,
    source_file: Path,
    extract_year: str,
    extract_month: str,
    extract_day: str,
) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(col).strip().lower().replace(" ", "_") for col in normalized.columns]

    normalized["source_file"] = str(source_file)
    normalized["extract_year"] = extract_year
    normalized["extract_month"] = extract_month
    normalized["extract_day"] = extract_day
    normalized["ingested_at_utc"] = pd.Timestamp.utcnow()
    return normalized


def process_partitions(input_files: list[Path], output_root: Path) -> list[ProcessResult]:
    partition_frames: dict[tuple[str, str, str], list[pd.DataFrame]] = {}
    partition_sources: dict[tuple[str, str, str], list[str]] = {}

    for input_file in input_files:
        extract_year, extract_month, extract_day = infer_extract_partitions(input_file)
        key = (extract_year, extract_month, extract_day)

        df = read_by_extension(input_file)
        normalized = normalize_dataframe(df, input_file, extract_year, extract_month, extract_day)
        partition_frames.setdefault(key, []).append(normalized)
        partition_sources.setdefault(key, []).append(str(input_file))

    results: list[ProcessResult] = []
    for key in sorted(partition_frames):
        extract_year, extract_month, extract_day = key
        frames = partition_frames[key]

        combined = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]

        output_dir = (
            output_root
            / f"extract_year={extract_year}"
            / f"extract_month={extract_month}"
            / f"extract_day={extract_day}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "udemy_user_course_activity.parquet"
        combined.to_parquet(output_file, index=False)

        results.append(
            ProcessResult(
                input_files=len(partition_sources[key]),
                output_file=str(output_file),
                rows=len(combined),
                columns=len(combined.columns),
                extract_year=extract_year,
                extract_month=extract_month,
                extract_day=extract_day,
            )
        )

    return results


def write_report(report_path: Path, results: list[ProcessResult]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "partitions_processed": len(results),
        "rows_processed": sum(item.rows for item in results),
        "details": [item.__dict__ for item in results],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Process Udemy monthly extracts from raw landing files.")
    parser.add_argument(
        "--input-root",
        default="data/raw/staging/atlas-staging-raw",
        help="Path to raw Udemy extract files.",
    )
    parser.add_argument(
        "--output-root",
        default="data/processed/udemy",
        help="Path for processed parquet outputs.",
    )
    parser.add_argument(
        "--report-path",
        default="data/processed/udemy/process_report.json",
        help="Path to write processing report JSON.",
    )
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)
    report_path = Path(args.report_path)

    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")

    files = discover_files(input_root)
    if not files:
        print(f"No supported files found under {input_root}")
        write_report(report_path, [])
        return

    results = process_partitions(files, output_root)
    for result in results:
        print(
            f"Consolidated {result.input_files} files -> {result.output_file} "
            f"({result.rows} rows, {result.columns} columns, "
            f"year={result.extract_year}, month={result.extract_month}, day={result.extract_day})"
        )

    write_report(report_path, results)
    print(
        f"Completed processing {len(files)} files into {len(results)} partitions with "
        f"{sum(item.rows for item in results)} rows total."
    )


if __name__ == "__main__":
    main()
