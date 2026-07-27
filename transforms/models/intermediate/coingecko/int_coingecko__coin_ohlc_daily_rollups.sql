with filtered as (
    select
        coin_id,
        vs_currency,
        days,
        interval,
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
        raw_payload,
        date_trunc('day', observed_at at time zone 'UTC') at time zone 'UTC' as rollup_observed_at
    from {{ ref('stg_coingecko__coins_ohlc') }}
    where days = 30
      and interval = '4h'
),

daily_extremes as (
    select
        coin_id,
        vs_currency,
        rollup_observed_at as observed_at,
        max(high) as high,
        min(low) as low
    from filtered
    group by 1, 2, 3
),

first_candles as (
    select distinct on (coin_id, vs_currency, rollup_observed_at)
        coin_id,
        vs_currency,
        rollup_observed_at as observed_at,
        open
    from filtered
    order by
        coin_id,
        vs_currency,
        rollup_observed_at,
        observed_at asc,
        extracted_at asc,
        loaded_at asc
),

last_candles as (
    select distinct on (coin_id, vs_currency, rollup_observed_at)
        coin_id,
        vs_currency,
        rollup_observed_at as observed_at,
        close,
        extracted_at,
        loaded_at,
        raw_record_id,
        source_record_id,
        batch_id,
        raw_payload
    from filtered
    order by
        coin_id,
        vs_currency,
        rollup_observed_at,
        observed_at desc,
        extracted_at desc,
        loaded_at desc
)

select
    daily_extremes.coin_id,
    daily_extremes.vs_currency,
    30 as days,
    'daily' as interval,
    cast(extract(epoch from daily_extremes.observed_at) * 1000 as bigint) as timestamp_ms,
    first_candles.open,
    daily_extremes.high,
    daily_extremes.low,
    last_candles.close,
    daily_extremes.observed_at,
    last_candles.extracted_at,
    last_candles.loaded_at,
    last_candles.raw_record_id,
    last_candles.source_record_id,
    last_candles.batch_id,
    last_candles.raw_payload
from daily_extremes
inner join first_candles
    on daily_extremes.coin_id = first_candles.coin_id
    and daily_extremes.vs_currency = first_candles.vs_currency
    and daily_extremes.observed_at = first_candles.observed_at
inner join last_candles
    on daily_extremes.coin_id = last_candles.coin_id
    and daily_extremes.vs_currency = last_candles.vs_currency
    and daily_extremes.observed_at = last_candles.observed_at
