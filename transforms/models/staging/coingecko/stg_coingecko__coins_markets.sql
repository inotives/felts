with source as (
    select *
    from {{ source('coingecko', 'raw_coins_markets') }}
    where is_valid
),

ranked as (
    select
        payload ->> 'id' as coin_id,
        payload ->> 'symbol' as coin_symbol,
        payload ->> 'name' as coin_name,
        nullif(payload ->> 'current_price', '')::numeric as current_price_usd,
        nullif(payload ->> 'market_cap', '')::numeric as market_cap_usd,
        nullif(payload ->> 'market_cap_rank', '')::integer as market_cap_rank,
        nullif(payload ->> 'total_volume', '')::numeric as total_volume_usd,
        nullif(payload ->> 'price_change_percentage_24h', '')::numeric
            as price_change_percentage_24h,
        nullif(payload ->> 'circulating_supply', '')::numeric as circulating_supply,
        nullif(payload ->> 'total_supply', '')::numeric as total_supply,
        observed_at,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        source_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by payload ->> 'id', observed_at
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

select
    coin_id,
    coin_symbol,
    coin_name,
    current_price_usd,
    market_cap_usd,
    market_cap_rank,
    total_volume_usd,
    price_change_percentage_24h,
    circulating_supply,
    total_supply,
    observed_at,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
