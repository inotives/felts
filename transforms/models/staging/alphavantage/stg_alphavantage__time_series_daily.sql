select
    payload ->> 'symbol' as symbol,
    (payload ->> 'trading_date')::date as trading_date,
    (payload ->> '1. open')::numeric as open_price,
    (payload ->> '2. high')::numeric as high_price,
    (payload ->> '3. low')::numeric as low_price,
    (payload ->> '4. close')::numeric as close_price,
    (payload ->> '5. volume')::bigint as volume,
    id as raw_record_id,
    source_record_id,
    extracted_at,
    observed_at,
    loaded_at,
    batch_id,
    payload as raw_payload
from {{ source('alphavantage', 'raw_time_series_daily') }}
where is_valid
