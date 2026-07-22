# Udemy Curated Schema v1

## Purpose

This schema is the analytics-ready contract for curated Udemy user-course-activity data.

## Grain

One row per learner-course activity record in a day partition.

## Key Model

- Learner identifier key: `learner_email_sha256`
- Activity record key: `activity_record_key_sha256`

`activity_record_key_sha256` is derived from `lower(user_email) + course_id + last_activity_date` and is intended to provide stable record uniqueness for analytics use cases.

## Partitioning

Curated output is partitioned by:

- `event_year`
- `event_month`
- `event_day`

## Fields

| Field | Type | Description |
| --- | --- | --- |
| learner_email_sha256 | string | SHA256 hash of lowercased learner email using configured salt. |
| activity_record_key_sha256 | string(nullable) | SHA256 hash of `lower(user_email)|course_id|last_activity_date` using configured salt. |
| learner_given_name | string | Learner given name from source. |
| learner_surname | string | Learner surname from source. |
| learner_role | string | Learner role (for example student/admin). |
| course_id | int64(nullable) | Udemy course identifier. |
| course_title | string | Course title. |
| course_category | string | Raw category string from source. |
| course_primary_category | string | First category token from `course_category`. |
| course_category_count | int64(nullable) | Number of comma-delimited category tokens. |
| course_duration_minutes | float64 | Total course duration in minutes. |
| video_consumed_minutes | float64 | Consumed video minutes for learner. |
| completion_ratio_pct | float64 | Completion ratio percentage. |
| is_assigned | boolean(nullable) | Assignment indicator. |
| enrolled_at | timestamp(UTC) | Enrollment timestamp. |
| started_at | timestamp(UTC) | Course start timestamp. |
| completed_at | timestamp(UTC) | Course completion timestamp. |
| first_completed_at | timestamp(UTC) | First completion timestamp if present. |
| source_ingested_at | timestamp(UTC) | Raw pipeline ingestion timestamp from source. |
| last_activity_date | date | Date of latest learner activity for the row. |
| source_environment | string | Source environment tag from raw data (for example staging). |
| event_year | string | Partition year. |
| event_month | string | Partition month. |
| event_day | string | Partition day. |
| record_loaded_at | timestamp(UTC) | Timestamp when curated record was produced. |

## PII Handling

- Raw `user_email` is not published in curated output.
- Curated output includes `learner_email_sha256` only.
- Salt value should be provided from a secure runtime source (for example AWS Secrets Manager).

## Quality Expectations

- `completion_ratio_pct` should typically be between 0 and 100.
- `course_id` should be present for nearly all rows.
- `event_year/event_month/event_day` must match processed partition context.
