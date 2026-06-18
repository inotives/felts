with source as (
    select *
    from {{ source('coingecko', 'raw_global') }}
    where is_valid
),

ranked as (
    select
        source_record_id,
        nullif(payload ->> 'active_cryptocurrencies', '')::integer as active_cryptocurrencies,
        nullif(payload ->> 'markets', '')::integer as markets,
        nullif(payload -> 'total_market_cap' ->> 'usd', '')::numeric as total_market_cap_usd,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by source_record_id, extracted_at
            order by loaded_at desc
        ) as row_number
    from source
)

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
from ranked
where row_number = 1
