select
    ohlc.coin_id,
    ohlc.vs_currency,
    ohlc.observed_at,
    ohlc.open,
    ohlc.high,
    ohlc.low,
    ohlc.close,
    metrics.total_volume as volume,
    metrics.market_cap,
    metrics.price,
    ohlc.extracted_at,
    ohlc.loaded_at,
    ohlc.raw_record_id,
    ohlc.source_record_id,
    ohlc.batch_id,
    ohlc.raw_payload
from {{ ref('int_coingecko__coin_ohlc_daily_rollups') }} as ohlc
inner join {{ ref('stg_coingecko__coins_market_chart') }} as metrics
    on ohlc.coin_id = metrics.coin_id
    and ohlc.vs_currency = metrics.vs_currency
    and ohlc.observed_at = metrics.observed_at
