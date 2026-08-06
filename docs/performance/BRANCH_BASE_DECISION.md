# Epic 2A — Branch base decision

## Chosen base

`feat/a02a-data-quality-shadow` @ `9cd04147134581d5a7cde768b166cf8ed0e91b25` (PR #6 HEAD)

Contains PR #5 (MetricService) + PR #6 (IQB / DataQualityService).

## PR #8 (intelligent ingestion)

**Not required** as base for Epic 2A.

Rationale:

- Performance Engine consumes **canonical aggregated metrics** and synthetic BioMed productivity/action inputs.
- It does not depend on the ingestion pipeline, RAW storage, or preview/import APIs.
- Stacking on PR #8 would widen the review surface without adding capability for shadow effectiveness.

PR #4 (auth/tenant) is **not** cherry-picked; shadow script and services are offline/read-only with explicit `client_id` (no HTTP endpoints in this phase).
