select
    coin_id,
    vs_currency,
    days,
    interval,
    timestamp_ms,
    price,
    market_cap,
    total_volume,
    observed_at,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from {{ ref('stg_coingecko__coins_market_chart') }}
