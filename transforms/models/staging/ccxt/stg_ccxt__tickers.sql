with source as (
    select *
    from {{ source('ccxt', 'raw_ticker') }}
    where is_valid
),

ranked as (
    select
        payload ->> 'exchange_id' as exchange_id,
        payload ->> 'symbol' as symbol,
        payload ->> 'base_asset' as base_asset,
        payload ->> 'quote_asset' as quote_asset,
        nullif(payload ->> 'timestamp', '')::bigint as timestamp_ms,
        nullif(payload ->> 'datetime', '')::timestamptz as provider_datetime,
        nullif(payload ->> 'bid', '')::numeric as bid,
        nullif(payload ->> 'ask', '')::numeric as ask,
        nullif(payload ->> 'last', '')::numeric as last_price,
        nullif(payload ->> 'open', '')::numeric as open_price,
        nullif(payload ->> 'high', '')::numeric as high_price,
        nullif(payload ->> 'low', '')::numeric as low_price,
        nullif(payload ->> 'close', '')::numeric as close_price,
        nullif(payload ->> 'base_volume', '')::numeric as base_volume,
        nullif(payload ->> 'quote_volume', '')::numeric as quote_volume,
        nullif(payload ->> 'vwap', '')::numeric as vwap,
        nullif(payload ->> 'percentage', '')::numeric as percentage,
        observed_at,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        source_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by
                payload ->> 'exchange_id',
                payload ->> 'symbol',
                observed_at
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

select
    exchange_id,
    symbol,
    base_asset,
    quote_asset,
    timestamp_ms,
    provider_datetime,
    bid,
    ask,
    last_price,
    open_price,
    high_price,
    low_price,
    close_price,
    base_volume,
    quote_volume,
    vwap,
    percentage,
    observed_at,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
