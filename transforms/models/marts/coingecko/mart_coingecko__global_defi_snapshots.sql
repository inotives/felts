select
    source_record_id,
    defi_market_cap,
    eth_market_cap,
    defi_to_eth_ratio,
    extracted_at,
    loaded_at,
    raw_record_id,
    batch_id,
    raw_payload
from {{ ref('stg_coingecko__global_defi') }}
