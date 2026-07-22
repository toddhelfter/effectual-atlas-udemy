# Lambda Curation Implementation Plan

## Goal

Build an AWS Lambda based pipeline that ingests raw Udemy user-course-activity parquet files and publishes curated, analytics-ready datasets for downstream projects.

## Scope

- Source: `s3://effectual-atlas-landing-staging/udemy/user-course-activity/`
- Input partitioning: `activity_year=YYYY/activity_month=MM/activity_day=DD/`
- Current observed raw shape: small parquet part-files per day partition.

## Phase 1: Contract and Discovery (Current)

1. Pull raw data to local sandbox.
2. Generate field inventory and value profiling outputs.
3. Draft and version a baseline data dictionary.
4. Identify required curated fields, optional fields, and quality checks.

Deliverables:

- `sandbox/analysis/udemy_data_dictionary.json`
- `sandbox/analysis/udemy_data_dictionary.md`
- Updated docs under `docs/`

## Phase 2: Curated Schema Design

1. Define canonical schema with explicit types:
   - learner identifiers
   - course metadata
   - activity/completion metrics
   - event timestamps
   - source lineage metadata
2. Normalize timestamps to UTC `timestamp` type.
3. Enforce column naming standards (snake_case).
4. Define partition strategy for curated output:
   - recommended: `event_year`, `event_month`, `event_day`

Deliverables:

- `docs/udemy_curated_schema.md`
- Versioned schema file (JSON or YAML)

## Phase 3: Lambda Processing Service

1. Trigger model:
   - Option A: EventBridge scheduled run over day partitions
   - Option B: S3 event notifications (with batching safeguards)
2. Lambda responsibilities:
   - discover new raw files for target partition
   - read and union parquet parts
   - validate schema/required fields
   - apply type coercion and normalization
   - write curated parquet partition
   - emit run metrics and manifest
3. Idempotency:
   - derive deterministic output path per partition
   - maintain processed marker (DynamoDB or manifest object)

Deliverables:

- Lambda code package
- IaC stack (Terraform or SAM)
- Unit tests and integration test harness

## Phase 4: Data Quality and Observability

1. Data quality checks:
   - required fields non-null thresholds
   - valid completion ratio range
   - timestamp parse success rates
2. Observability:
   - CloudWatch metrics: rows_in, rows_out, files_in, rejects
   - structured logs with partition context
   - alarm on failures and quality threshold breaches

Deliverables:

- Quality policy document
- CloudWatch dashboards and alarms

## Phase 5: Publish and Consumption

1. Register curated table in Glue Data Catalog.
2. Expose Athena views for common analytics use cases.
3. Define data retention and lifecycle policies.
4. Publish consumer documentation and sample queries.

Deliverables:

- Glue table definition
- Athena sample query pack
- Consumer onboarding notes

## Milestones

- M1: Discovery and baseline dictionary complete
- M2: Curated schema approved
- M3: Lambda MVP in staging
- M4: Quality gates and monitoring enabled
- M5: Curated dataset published for consumers

## Risks and Mitigations

- Risk: Schema drift in raw extracts
  - Mitigation: schema version checks + alerting + quarantine path
- Risk: Tiny-file explosion increases processing overhead
  - Mitigation: compaction/consolidation per day partition
- Risk: Missing daily extracts
  - Mitigation: design pipeline as sparse-partition tolerant
