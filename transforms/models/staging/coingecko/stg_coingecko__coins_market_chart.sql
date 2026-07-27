with source as (
    select *
    from {{ source('coingecko', 'raw_coins_market_chart') }}
    where is_valid
),

ranked as (
    select
        payload ->> 'coin_id' as coin_id,
        payload ->> 'vs_currency' as vs_currency,
        nullif(payload ->> 'days', '')::integer as days,
        payload ->> 'interval' as interval,
        nullif(payload ->> 'timestamp_ms', '')::bigint as timestamp_ms,
        nullif(payload ->> 'price', '')::numeric as price,
        nullif(payload ->> 'market_cap', '')::numeric as market_cap,
        nullif(payload ->> 'total_volume', '')::numeric as total_volume,
        observed_at,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        source_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by
                payload ->> 'coin_id',
                payload ->> 'vs_currency',
                payload ->> 'interval',
                observed_at
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

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
from ranked
where row_number = 1
