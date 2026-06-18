# Felts Context

Felts is a financial ELT system for landing source data, preserving raw evidence, and transforming it into analytical models. This glossary defines the project language shared across extraction, loading, orchestration, and transformation work.

## Language

**Source**:
A named external or local origin that provides financial data.
_Avoid_: provider, connector

**Entity**:
A named kind of data emitted by a **Source**.
_Avoid_: table, endpoint

**ExtractedRecord**:
A source-shaped record emitted by an extractor before validation and raw wrapping.
_Avoid_: raw row, payload

**RawRecord**:
A loadable record that wraps an **ExtractedRecord** with ingestion identity, timestamps, validation state, and batch metadata.
_Avoid_: staging row, transformed record

**Batch**:
A traceable group of records processed together during one write operation.
_Avoid_: run, job

**Writer**:
The boundary that validates **ExtractedRecords** and converts them into **RawRecords**.
_Avoid_: loader, extractor

**Loader**:
The boundary that persists **RawRecords** into a warehouse target.
_Avoid_: writer, importer

**Schema Registry**:
The lookup that maps a **Source** and **Entity** to the current validation schema when one exists.
_Avoid_: catalog, dbt sources

**Source Run**:
One invocation that extracts and writes selected **Entities** for a **Source**, producing a source-level outcome summary.
_Avoid_: job, flow, task

**Source Schema**:
A database namespace owned by one **Source** for source-specific raw and transformed models.
_Avoid_: provider schema, raw schema

**Raw Entity Table**:
A persistence table for **RawRecords** belonging to one **Source** and **Entity**.
_Avoid_: staging table, mart table

**Staging Model**:
A transformed model that unpacks, types, filters, and deduplicates raw source data into a declared analytical shape.
_Avoid_: raw view, mart

**Mart Model**:
A consumer-facing analytical model built from staging or intermediate models.
_Avoid_: staging model, raw table

**Declared Grain**:
The exact uniqueness contract for rows in a transformed model.
_Avoid_: primary key, dedup key

## Relationships

- A **Source** emits one or more **Entities**.
- An **Extractor** emits **ExtractedRecords** for one **Source** and **Entity**.
- A **Writer** converts many **ExtractedRecords** into many **RawRecords**.
- A **Loader** persists **RawRecords**.
- A **Batch** groups the **RawRecords** produced by one write operation.
- A **Schema Registry** may validate **ExtractedRecords** before they become **RawRecords**.
- A **Source Run** processes selected **Entities** for one **Source**.
- A **Source Schema** contains **Raw Entity Tables** and source-specific transformed models for one **Source**.
- A **Raw Entity Table** persists **RawRecords** for one **Entity**.
- A **Staging Model** derives from raw source data and has one **Declared Grain**.
- A **Mart Model** derives from transformed models and has one **Declared Grain**.

## Example dialogue

> **Dev:** "Should the CoinGecko extractor create RawRecords directly?"
> **Domain expert:** "No. It should emit ExtractedRecords for a Source and Entity. The Writer uses the Schema Registry, assigns a Batch, and produces RawRecords for the Loader."

## Flagged ambiguities

- "raw" can mean source payload or database landing row; resolved: **ExtractedRecord** is source-shaped, while **RawRecord** is loadable and includes ingestion metadata.
- "loader" can mean validation plus persistence; resolved: **Writer** handles validation and wrapping, while **Loader** handles persistence only.
