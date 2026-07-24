select
    source_record_id,
    active_cryptocurrencies,
    markets,
    total_market_cap_usd,
    extracted_at,
    loaded_at,
    raw_record_id,
    batch_id,
    raw_payload
from {{ ref('stg_coingecko__global') }}
