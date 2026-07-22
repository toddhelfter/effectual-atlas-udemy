# Atlas Data Science Project

Data science workspace focused on ingesting raw files uploaded to S3, organizing them locally, and producing a reproducible file manifest.

First active dataset: monthly employee training activity extracts from Udemy.

## AWS Accounts

| Account Name | Account ID | Email | Console URL |
| --- | --- | --- | --- |
| atlas-production | 757706350067 | atlas-production@effectual.com | https://effectual-sandbox.awsapps.com/start/#/console?account_id=757706350067&referrer=accessPortal |
| atlas-staging | 637616607776 | atlas-staging@effectual.com | https://effectual-sandbox.awsapps.com/start/#/console?account_id=637616607776&referrer=accessPortal |

## Project Structure

- `config/accounts.yaml`: account metadata.
- `config/s3_sources.yaml`: S3 raw source definitions by environment.
- `config/curated_schema_udemy_v1.json`: versioned curated schema contract.
- `src/atlas_data/ingest_s3.py`: raw file sync + manifest generation.
- `src/atlas_data/process_udemy_extracts.py`: normalization and parquet output for Udemy extracts.
- `src/atlas_data/summarize_udemy_parquet.py`: profile raw parquet part-files by day partition.
- `src/atlas_data/profile_udemy_schema.py`: infer field-level dictionary from raw sandbox files.
- `src/atlas_data/curate_udemy.py`: curated transform module for one day partition.
- `src/atlas_data/lambda_handler.py`: Lambda-ready handler for S3 partition curation.
- `scripts/pull_udemy_to_sandbox.sh`: pull Udemy raw parquet files to local sandbox.
- `scripts/sync_raw_from_s3.sh`: convenience runner.
- `scripts/process_udemy_extracts.sh`: convenience runner for Udemy processing.
- `scripts/summarize_udemy_parquet.sh`: summarize raw parquet file/row counts.
- `scripts/profile_udemy_schema.sh`: generate field-level dictionary artifacts from sandbox parquet files.
- `scripts/curate_udemy_partition.sh`: run curated transform for a specific day partition.
- `docs/udemy_dataset.md`: dataset-specific notes and assumptions.
- `docs/udemy_initial_findings.md`: initial inventory from the first sandbox sample.
- `docs/udemy_curated_schema.md`: curated analytics schema definition.
- `docs/lambda_curation_implementation_plan.md`: long-term Lambda curation roadmap.
- `data/raw/`: local raw file landing area (gitignored).

## Setup

1. Create a virtual environment and install dependencies:

	```bash
	python -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt
	```

2. Confirm `config/s3_sources.yaml` has the correct source:
	- staging bucket: `effectual-atlas-landing-staging`
	- staging prefix: `udemy/user-course-activity/`

3. Export AWS credentials for the account/profile you want to access.

## Script Operations Reference

All scripts are in `scripts/` and can be run with:

```bash
bash scripts/<script_name>.sh [args...]
```

Python-based scripts support an optional interpreter override:

```bash
PYTHON_BIN=/Users/toddhelfter/Atlas/.venv/bin/python bash scripts/<script_name>.sh
```

### scripts/sync_raw_from_s3.sh

Purpose:

- Sync raw files from configured S3 sources in `config/s3_sources.yaml`.

Arguments:

- arg1: config path (default `config/s3_sources.yaml`)
- arg2: environment (`production`, `staging`, or `all`; default `all`)

Examples:

```bash
bash scripts/sync_raw_from_s3.sh
bash scripts/sync_raw_from_s3.sh config/s3_sources.yaml staging
```

Outputs:

- Raw files in `data/raw/<environment>/<source_name>/...`
- Manifest in `data/raw/manifest.json`

### scripts/pull_udemy_to_sandbox.sh

Purpose:

- Pull Udemy parquet raw files directly to local sandbox for quick analysis.

Arguments:

- arg1: source S3 URI (default `s3://effectual-atlas-landing-staging/udemy/user-course-activity/`)
- arg2: local target directory (default `sandbox/udemy/user-course-activity`)

Examples:

```bash
bash scripts/pull_udemy_to_sandbox.sh
bash scripts/pull_udemy_to_sandbox.sh s3://effectual-atlas-landing-staging/udemy/user-course-activity/ sandbox/udemy/user-course-activity
```

Outputs:

- Downloaded parquet files under `sandbox/udemy/user-course-activity/...`

### scripts/profile_udemy_schema.sh

Purpose:

- Build initial field-level data dictionary from sandbox parquet files.

Arguments:

- arg1: input root (default `sandbox/udemy/user-course-activity`)
- arg2: JSON output (default `sandbox/analysis/udemy_data_dictionary.json`)
- arg3: markdown output (default `sandbox/analysis/udemy_data_dictionary.md`)

Examples:

```bash
bash scripts/profile_udemy_schema.sh
bash scripts/profile_udemy_schema.sh sandbox/udemy/user-course-activity sandbox/analysis/udemy_data_dictionary.json sandbox/analysis/udemy_data_dictionary.md
```

Outputs:

- `sandbox/analysis/udemy_data_dictionary.json`
- `sandbox/analysis/udemy_data_dictionary.md`

### scripts/summarize_udemy_parquet.sh

Purpose:

- Summarize raw parquet file counts, row counts, and sizes by observed partitions.

Arguments:

- arg1: input root (default `data/raw/staging/atlas-staging-raw`)
- arg2: JSON output (default `data/interim/udemy/raw_parquet_summary.json`)
- arg3: CSV output (default `data/interim/udemy/raw_parquet_summary.csv`)

Examples:

```bash
bash scripts/summarize_udemy_parquet.sh
bash scripts/summarize_udemy_parquet.sh sandbox/udemy/user-course-activity sandbox/analysis/raw_parquet_summary.json sandbox/analysis/raw_parquet_summary.csv
```

Outputs:

- JSON summary and CSV summary at specified output paths

### scripts/report_trainings_by_email.sh

Purpose:

- Report training activity grouped by `email_address` from raw parquet extracts.

Arguments:

- arg1: input root (default `sandbox/udemy/user-course-activity`)
- arg2: output root (default `sandbox/analysis`)
- arg3: optional specific email filter

Examples:

```bash
bash scripts/report_trainings_by_email.sh
bash scripts/report_trainings_by_email.sh sandbox/udemy/user-course-activity sandbox/analysis martins.onyejiaka@effectual.com
```

Outputs:

- `sandbox/analysis/training_by_email_summary.csv`
- `sandbox/analysis/training_by_email_details.csv`
- `sandbox/analysis/training_by_email_summary.json`

### scripts/process_udemy_extracts.sh

Purpose:

- Consolidate raw source part-files into one processed parquet per day partition.

Arguments:

- arg1: input root (default `data/raw/staging/atlas-staging-raw`)
- arg2: output root (default `data/processed/udemy`)
- arg3: process report path (default `data/processed/udemy/process_report.json`)

Examples:

```bash
bash scripts/process_udemy_extracts.sh
bash scripts/process_udemy_extracts.sh sandbox/udemy/user-course-activity data/processed/udemy data/processed/udemy/process_report.json
```

Outputs:

- Partitioned processed files under `data/processed/udemy/extract_year=.../extract_month=.../extract_day=.../`
- Process report JSON

### scripts/curate_udemy_partition.sh

Purpose:

- Transform one day partition into the curated analytics schema.

Arguments:

- arg1: input root (default `sandbox/udemy/user-course-activity`)
- arg2: output root (default `data/curated/udemy_user_course_activity`)
- arg3: partition year (default `2026`)
- arg4: partition month (default `07`)
- arg5: partition day (default `20`)
- arg6: hash salt (default `udemy-default-salt`)
- arg7: report path (default `data/curated/udemy_user_course_activity/last_run_report.json`)

Examples:

```bash
bash scripts/curate_udemy_partition.sh
bash scripts/curate_udemy_partition.sh sandbox/udemy/user-course-activity data/curated/udemy_user_course_activity 2026 07 20 your-salt-value
```

Outputs:

- Curated parquet under `data/curated/udemy_user_course_activity/event_year=.../event_month=.../event_day=.../`
- Curated run report JSON

## End-to-End Command Sequence

```bash
bash scripts/pull_udemy_to_sandbox.sh
bash scripts/profile_udemy_schema.sh
bash scripts/report_trainings_by_email.sh
bash scripts/summarize_udemy_parquet.sh sandbox/udemy/user-course-activity sandbox/analysis/raw_parquet_summary.json sandbox/analysis/raw_parquet_summary.csv
bash scripts/process_udemy_extracts.sh sandbox/udemy/user-course-activity data/processed/udemy data/processed/udemy/process_report.json
bash scripts/curate_udemy_partition.sh sandbox/udemy/user-course-activity data/curated/udemy_user_course_activity 2026 07 20 your-salt-value
```

## Sync Raw S3 Data

Run both environments:

```bash
bash scripts/sync_raw_from_s3.sh
```

Run a single environment:

```bash
bash scripts/sync_raw_from_s3.sh config/s3_sources.yaml production
bash scripts/sync_raw_from_s3.sh config/s3_sources.yaml staging
```

Outputs:

- Downloaded files under `data/raw/<environment>/<source_name>/...`
- Manifest at `data/raw/manifest.json`

## Udemy Workflow

### Task 1: Pull to Sandbox and Analyze Fields

Pull raw parquet files to the local sandbox folder:

```bash
bash scripts/pull_udemy_to_sandbox.sh
```

Build initial data dictionary artifacts from local parquet files:

```bash
bash scripts/profile_udemy_schema.sh
```

Dictionary outputs:

- `sandbox/analysis/udemy_data_dictionary.json`
- `sandbox/analysis/udemy_data_dictionary.md`

Generate training reports grouped by `email_address`:

```bash
bash scripts/report_trainings_by_email.sh
```

Generate report for one employee:

```bash
bash scripts/report_trainings_by_email.sh sandbox/udemy/user-course-activity sandbox/analysis martins.onyejiaka@effectual.com
```

Email report outputs:

- `sandbox/analysis/training_by_email_summary.csv`
- `sandbox/analysis/training_by_email_details.csv`
- `sandbox/analysis/training_by_email_summary.json`

Current sample summary:

- 12 parquet files
- 16 rows
- 21 columns

See:

- `docs/udemy_initial_findings.md`
- `docs/lambda_curation_implementation_plan.md`
- `docs/udemy_curated_schema.md`

Raw Udemy extracts are parquet part-files (for example `run-...-snappy.parquet`) partitioned by year/month/day.

Summarize raw parquet first:

```bash
bash scripts/summarize_udemy_parquet.sh
```

Summary outputs:

- `data/interim/udemy/raw_parquet_summary.json`
- `data/interim/udemy/raw_parquet_summary.csv`

After syncing raw files, process them into normalized parquet. The processor consolidates small part-files into one parquet per day partition:

```bash
bash scripts/process_udemy_extracts.sh
```

Optional custom paths:

```bash
bash scripts/process_udemy_extracts.sh data/raw/staging/atlas-staging-raw data/processed/udemy data/processed/udemy/process_report.json
```

Outputs:

- One consolidated parquet per day under `data/processed/udemy/extract_year=<YYYY or unknown>/extract_month=<MM or unknown>/extract_day=<DD or unknown>/`
- Processing report at `data/processed/udemy/process_report.json`

## Curated Output (Phase 2)

Run curated transform for a specific partition:

```bash
bash scripts/curate_udemy_partition.sh sandbox/udemy/user-course-activity data/curated/udemy_user_course_activity 2026 07 20 your-salt-value
```

Outputs:

- Curated partition parquet at `data/curated/udemy_user_course_activity/event_year=YYYY/event_month=MM/event_day=DD/`
- Run report at `data/curated/udemy_user_course_activity/last_run_report.json`

Key strategy in curated output:

- `learner_email_sha256` is the learner identifier.
- `activity_record_key_sha256` is the activity-level composite key (`email + course_id + last_activity_date`, hashed).

Long-term deployment target:

- Lambda handler in `src/atlas_data/lambda_handler.py`
