with source as (
    select *
    from {{ source('csv_import', 'raw_ohlcv') }}
    where is_valid
),

ranked as (
    select
        payload #>> '{_felts,identity,asset_slug}' as asset_slug,
        payload ->> 'name' as source_asset_id,
        nullif(payload ->> 'timeOpen', '')::timestamptz as time_open,
        nullif(payload ->> 'timeClose', '')::timestamptz as time_close,
        nullif(payload ->> 'timeHigh', '')::timestamptz as time_high,
        nullif(payload ->> 'timeLow', '')::timestamptz as time_low,
        nullif(payload ->> 'timestamp', '')::timestamptz as observed_at,
        nullif(payload ->> 'open', '')::numeric as open,
        nullif(payload ->> 'high', '')::numeric as high,
        nullif(payload ->> 'low', '')::numeric as low,
        nullif(payload ->> 'close', '')::numeric as close,
        nullif(payload ->> 'volume', '')::numeric as volume,
        nullif(payload ->> 'marketCap', '')::numeric as market_cap,
        nullif(payload ->> 'circulatingSupply', '')::numeric as circulating_supply,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        source_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by payload #>> '{_felts,identity,asset_slug}', payload ->> 'timestamp'
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

select
    asset_slug,
    source_asset_id,
    time_open,
    time_close,
    time_high,
    time_low,
    observed_at,
    open,
    high,
    low,
    close,
    volume,
    market_cap,
    circulating_supply,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
