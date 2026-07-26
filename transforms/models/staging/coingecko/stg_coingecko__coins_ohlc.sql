with source as (
    select *
    from {{ source('coingecko', 'raw_coins_ohlc') }}
    where is_valid
),

ranked as (
    select
        payload ->> 'coin_id' as coin_id,
        payload ->> 'vs_currency' as vs_currency,
        nullif(payload ->> 'days', '')::integer as days,
        nullif(payload ->> 'timestamp_ms', '')::bigint as timestamp_ms,
        nullif(payload ->> 'open', '')::numeric as open,
        nullif(payload ->> 'high', '')::numeric as high,
        nullif(payload ->> 'low', '')::numeric as low,
        nullif(payload ->> 'close', '')::numeric as close,
        observed_at,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        source_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by payload ->> 'coin_id', payload ->> 'vs_currency', observed_at
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

select
    coin_id,
    vs_currency,
    days,
    timestamp_ms,
    open,
    high,
    low,
    close,
    observed_at,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
