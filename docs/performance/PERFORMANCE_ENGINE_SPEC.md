# BioMed Performance Engine — Specification (Epic 2A)

## Purpose

Measure BioMed actuation → indicator change → observed result → limitations → technical conclusion.

**Shadow mode only** in this phase: no UI, no public endpoints, no production writes.

## Feature flag

`ENABLE_BIOMED_PERFORMANCE_ENGINE=false` (default).

## Package

`backend/performance/` — baseline, effectiveness, productivity, ROI, recommendations, score, privacy.

## Metric dependency

Reuses canonical metric **concepts** from PR #5 (`MetricService`). This phase accepts aggregated `MetricSnapshot` fixtures/adapters — **does not duplicate formulas** in the frontend. Unavailable indicators return explicit quality labels.

## Non-goals

Dashboard, generative AI, clinical record, migrations, deploy, merge.
