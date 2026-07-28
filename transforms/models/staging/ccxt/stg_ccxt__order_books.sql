with source as (
    select *
    from {{ source('ccxt', 'raw_order_book') }}
    where is_valid
),

ranked as (
    select
        payload ->> 'exchange_id' as exchange_id,
        payload ->> 'symbol' as symbol,
        payload ->> 'base_asset' as base_asset,
        payload ->> 'quote_asset' as quote_asset,
        nullif(payload ->> 'limit', '')::integer as order_book_limit,
        nullif(payload ->> 'timestamp', '')::bigint as timestamp_ms,
        nullif(payload ->> 'datetime', '')::timestamptz as provider_datetime,
        nullif(payload ->> 'nonce', '')::text as nonce,
        nullif(payload ->> 'best_bid', '')::numeric as best_bid,
        nullif(payload ->> 'best_ask', '')::numeric as best_ask,
        payload -> 'bids' as bids,
        payload -> 'asks' as asks,
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
    order_book_limit,
    timestamp_ms,
    provider_datetime,
    nonce,
    best_bid,
    best_ask,
    bids,
    asks,
    observed_at,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
