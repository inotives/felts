select
    symbol,
    trading_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    raw_record_id,
    source_record_id,
    extracted_at,
    observed_at,
    loaded_at,
    batch_id,
    raw_payload
from {{ ref('stg_alphavantage__time_series_daily') }}
