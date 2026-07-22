# Udemy Raw Extract Initial Findings

## Snapshot

Analysis date: 2026-07-22

- Files analyzed: 12 parquet files
- Rows observed: 16
- Columns observed: 21
- Partition coverage observed:
  - 2026-06-26
  - 2026-06-29
  - 2026-07-09
  - 2026-07-18
  - 2026-07-20

## Field Inventory

1. assigned_by
2. completion_ratio
3. course_category
4. course_completion_date
5. course_duration
6. course_enroll_date
7. course_first_completion_date
8. course_id
9. course_start_date
10. course_title
11. env
12. ingestion_timestamp
13. is_assigned
14. last_activity_date
15. lms_user_id
16. num_video_consumed_minutes
17. user_email
18. user_external_id
19. user_name
20. user_role
21. user_surname

## Observations

- `assigned_by` and `lms_user_id` are fully null in the current sample.
- `course_completion_date` and `course_first_completion_date` are sparse, which is expected for in-progress courses.
- `user_email` contains direct identifiers, so curated outputs should account for privacy requirements.
- `course_category` includes comma-delimited multi-category values that may need splitting for analytics.
- `env` is constant (`staging`) in current extracts.

## Artifacts

- Full dictionary JSON: `sandbox/analysis/udemy_data_dictionary.json`
- Full dictionary markdown: `sandbox/analysis/udemy_data_dictionary.md`
