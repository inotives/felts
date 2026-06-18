# YAML-driven CSV Import Contracts

Felts defines CSV import dataset contracts in `src/felts/sources/csv_import/contracts.yaml` instead of hard-coding each CSV shape in extractor code.

The CSV extractor owns generic mechanics: opening local paths and `file://` URIs, parsing CSV rows with configured delimiter and encoding, validating headers, deriving supported identity strategies, building raw record identity, and emitting source-shaped records. The YAML contracts own dataset-specific behavior: source, entity, default path, filename pattern, delimiter, encoding, required headers, column type hints, identity strategy, source record identity fields, observed timestamp/date column, and dbt selector.

This lets Felts add another CSV import when it matches supported mechanics by adding a YAML contract rather than changing extractor code. It also keeps CSV import behavior reviewable in one source-feature registry.

The trade-off is that CSV contracts now need validation and clear error messages, because incorrect YAML can break imports at runtime. Felts accepts that cost because CSV files vary mostly by contract parameters, not by extraction algorithm.

New extractor code is still required when a CSV dataset needs unsupported behavior such as a new identity strategy, object-store input, compressed file handling, multi-file imports, or non-tabular parsing.
