select
    coin_id,
    coin_symbol,
    upper(coin_symbol) as coin_symbol_upper,
    coin_name,
    extracted_at as last_seen_at,
    raw_record_id
from {{ ref('stg_coingecko__coins_list') }}
