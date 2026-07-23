---
id: task-0012
title: "Phase 11: dbt verification and docs close-out"
type: task
status: ready
assigned_to: worker
created_by: human
created_on: 2026-07-24
updated_on: 2026-07-24
priority: normal
parent: ""
depends_on:
  - task-0011
---



# Task

## Context

Tasks 0009 through 0011 implement the Phase 11 internal mapping marts and
source-owned mart completion. This task proves the full dbt path and updates docs
for close-out.

Source of truth:

- `docs/phases/phase_11_analytical_marts_and_internal_assets.md`

## Goal

Run final Phase 11 verification and update docs to reflect the implemented mart and
internal asset mapping surface.

## Scope

- Run fast checks:
  - `make lint`
  - `make format-check`
  - `make typecheck`
  - `make test`
- Run DB-backed dbt checks:
  - `make dbt-debug`
  - `uv run dbt seed --project-dir transforms --profiles-dir transforms`
  - `uv run dbt run --project-dir transforms --profiles-dir transforms --select marts`
  - `uv run dbt test --project-dir transforms --profiles-dir transforms --select marts`
- Update implemented-state docs after checks pass.
- Record exact command evidence in `## Notes`.
- Do not mark Phase 11 implemented if DB-backed dbt verification is skipped.
- Do not move the Phase 11 phase doc to `docs/_archived/` in this task unless the
  human explicitly asks for archive close-out after merge.

## Planner Notes

The key close-out evidence is dbt seed/run/test against local Postgres. Static file
checks alone are not enough for this phase.

## Implementation Plan

1. Confirm task dependencies are done or ready for review.
2. Run fast checks.
3. Run dbt seed, mart run, and mart tests against local Postgres.
4. Update docs that describe implemented mart/internal mapping state.
5. Record exact commands and outcomes in this task's notes.

## Acceptance Criteria

- [ ] Fast checks pass.
- [ ] `make dbt-debug` passes.
- [ ] `dbt seed` passes.
- [ ] `dbt run --select marts` passes.
- [ ] `dbt test --select marts` passes.
- [ ] Docs describe Phase 11's implemented source-owned marts and `felts` internal
  mapping marts.
- [ ] Task notes contain exact verification commands and results.
- [ ] Phase 11 is not marked implemented without DB-backed dbt evidence.

## Notes

