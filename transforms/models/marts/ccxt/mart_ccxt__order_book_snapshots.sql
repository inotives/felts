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
    case
        when best_bid is not null and best_ask is not null
        then best_ask - best_bid
        else null
    end as spread,
    case
        when best_bid is not null and best_ask is not null
        then (best_bid + best_ask) / 2
        else null
    end as mid_price,
    bids,
    asks,
    observed_at,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from {{ ref('stg_ccxt__order_books') }}
