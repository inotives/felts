select
    observation_date,
    series_id,
    value,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from {{ ref('stg_csv_import__fred_series') }}
