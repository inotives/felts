# Felts Implementation Phases

This breaks the Felts project specification into implementation phases ordered by core functionality and dependency flow. Each phase should be grilled and finalized before implementation starts.

## Phase Order

0. [Phase 00 - Project Scaffolding](./_archived/phase_00_project_scaffolding.md)
1. [Phase 01 - Core Contracts and Local Foundation](./_archived/phase_01_core_contracts.md)
2. [Phase 02 - First Source Vertical Slice](./_archived/phase_02_first_source_vertical_slice.md)
3. [Phase 03 - dbt Transform Foundation](./_archived/phase_03_dbt_transform_foundation.md)
4. [Phase 04 - Prefect Flow and Scheduling Foundation](./_archived/phase_04_prefect_orchestration.md)
5. [Phase 05 - Additional Source Patterns](./_archived/phase_05_additional_source_patterns.md)
6. [Phase 06 - Operational Hardening](./_archived/phase_06_operational_hardening.md)
7. [Phase 07 - Advanced and Deferred Capabilities](./_archived/phase_07_advanced_capabilities.md)
8. [Phase 08 - Source and Entity Scaffolding](./_archived/phase_08_source_scaffolding.md)
9. [Phase 09 - Production Data Agent Access](./phases/phase_09_production_data_agent_access.md)

## Dependency Shape

Phase 00 creates the repository and tooling skeleton. Phase 01 creates the shared contracts. Phase 02 proves one complete extract-load path. Phase 03 turns raw loaded data into usable models. Phase 04 wires the working path into Prefect schedules and event chains. Phase 05 expands source variety only after the first path works. Phase 06 makes the system reliable enough to operate. Phase 07 records deferred capabilities in the project specification until a concrete requirement justifies a dedicated implementation phase. Phase 08 reduces repetitive source and entity setup while preserving explicit provider-specific logic. Phase 09 gives AI agents constrained query access to production analytical data without exposing PostgreSQL publicly.
