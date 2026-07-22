# Udemy Training Activity Dataset

## Source

- Bucket: `effectual-atlas-landing-staging`
- Prefix: `udemy/user-course-activity/`
- Environment: staging
- Description: monthly extracts of employee training activity from the Udemy platform.

## First Task Workflow

1. Pull raw extracts to local sandbox:

```bash
bash scripts/pull_udemy_to_sandbox.sh
```

2. Analyze fields and sample data values:

```bash
bash scripts/profile_udemy_schema.sh
```

3. Review outputs:

- `sandbox/analysis/udemy_data_dictionary.json`
- `sandbox/analysis/udemy_data_dictionary.md`
- `docs/udemy_initial_findings.md`

## Expected Patterns

- Files are expected to arrive monthly.
- Extracts are partitioned by day inside month partitions.
- Not every day has an extract; missing days are expected.
- Current observed format: parquet part-files (for example `run-...-snappy.parquet`).
- Partition-style paths are supported directly:
   - `activity_year=YYYY/activity_month=MM/activity_day=DD/`

## Raw Parquet Profiling

Use this step to inventory row counts, file sizes, and partition coverage before transforms:

```bash
bash scripts/summarize_udemy_parquet.sh
```

Outputs:

- `data/interim/udemy/raw_parquet_summary.json`
- `data/interim/udemy/raw_parquet_summary.csv`

These files help confirm when upstream emits many small parquet parts (for example around 4-5 KB each).

## Processing Behavior

The processing stage:

1. Reads supported source files from `data/raw/staging/atlas-staging-raw`.
2. Normalizes column names to snake_case lowercase.
3. Appends metadata columns:
   - `source_file`
   - `extract_year`
   - `extract_month`
   - `extract_day`
   - `ingested_at_utc`
4. Writes partitioned parquet under:
   - `data/processed/udemy/extract_year=<value>/extract_month=<value>/extract_day=<value>/`
   - Small source part-files are consolidated into a single parquet per day partition.
5. Writes process report to `data/processed/udemy/process_report.json`.

## Notes

- If year/month/day cannot be inferred, unknown partitions are used.
- Keep raw files immutable; only transform data in `data/processed/`.
