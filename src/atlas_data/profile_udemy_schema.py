from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FileStats:
    file_path: str
    rows: int
    columns: int


def find_parquet_files(input_root: Path) -> list[Path]:
    return sorted(input_root.rglob("*.parquet"))


def read_dataset(files: list[Path]) -> tuple[pd.DataFrame, list[FileStats]]:
    frames: list[pd.DataFrame] = []
    stats: list[FileStats] = []

    for file_path in files:
        df = pd.read_parquet(file_path)
        frames.append(df)
        stats.append(FileStats(file_path=str(file_path), rows=len(df), columns=len(df.columns)))

    dataset = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
    return dataset, stats


def value_samples(series: pd.Series, limit: int = 10) -> list[str]:
    if series.dropna().empty:
        return []

    unique_values = series.dropna().astype(str).drop_duplicates().head(limit)
    return unique_values.tolist()


def build_field_dictionary(df: pd.DataFrame) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    row_count = len(df)

    for column in sorted(df.columns):
        series = df[column]
        non_null = int(series.notna().sum())
        null_count = int(series.isna().sum())

        distinct_count = int(series.astype(str).nunique(dropna=True)) if non_null > 0 else 0
        samples = value_samples(series, limit=10)

        results.append(
            {
                "field_name": column,
                "dtype": str(series.dtype),
                "rows": row_count,
                "non_null_count": non_null,
                "null_count": null_count,
                "null_pct": round((null_count / row_count) * 100, 2) if row_count else 0.0,
                "distinct_count": distinct_count,
                "sample_values": samples,
            }
        )

    return results


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Udemy Raw Data Dictionary (Initial Pass)")
    lines.append("")
    lines.append("## Dataset Summary")
    lines.append("")
    lines.append(f"- Files analyzed: {payload['dataset']['files_analyzed']}")
    lines.append(f"- Total rows: {payload['dataset']['total_rows']}")
    lines.append(f"- Total columns: {payload['dataset']['total_columns']}")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("| File | Rows | Columns |")
    lines.append("| --- | ---: | ---: |")

    for item in payload["files"]:
        lines.append(f"| {item['file_path']} | {item['rows']} | {item['columns']} |")

    lines.append("")
    lines.append("## Fields")
    lines.append("")
    lines.append("| Field | Type | Non-Null | Null | Null % | Distinct | Sample Values |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- |")

    for field in payload["fields"]:
        samples = ", ".join(field["sample_values"]) if field["sample_values"] else ""
        lines.append(
            f"| {field['field_name']} | {field['dtype']} | {field['non_null_count']} | "
            f"{field['null_count']} | {field['null_pct']} | {field['distinct_count']} | {samples} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile raw Udemy parquet files and generate data dictionary outputs.")
    parser.add_argument(
        "--input-root",
        default="sandbox/udemy/user-course-activity",
        help="Root directory containing downloaded raw parquet files.",
    )
    parser.add_argument(
        "--json-output",
        default="sandbox/analysis/udemy_data_dictionary.json",
        help="JSON output path.",
    )
    parser.add_argument(
        "--markdown-output",
        default="sandbox/analysis/udemy_data_dictionary.md",
        help="Markdown output path.",
    )
    args = parser.parse_args()

    input_root = Path(args.input_root)
    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")

    files = find_parquet_files(input_root)
    if not files:
        raise FileNotFoundError(f"No parquet files found under: {input_root}")

    df, file_stats = read_dataset(files)
    fields = build_field_dictionary(df)

    payload = {
        "dataset": {
            "files_analyzed": len(file_stats),
            "total_rows": len(df),
            "total_columns": len(df.columns),
        },
        "files": [item.__dict__ for item in file_stats],
        "fields": fields,
    }

    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(markdown_output, payload)

    print(
        f"Profiled {len(file_stats)} files, {len(df)} rows, {len(df.columns)} columns. "
        f"Wrote outputs to {json_output} and {markdown_output}."
    )


if __name__ == "__main__":
    main()
