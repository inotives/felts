with source as (
    select *
    from {{ source('coingecko', 'raw_global_defi') }}
    where is_valid
),

ranked as (
    select
        source_record_id,
        nullif(payload ->> 'defi_market_cap', '')::numeric as defi_market_cap,
        nullif(payload ->> 'eth_market_cap', '')::numeric as eth_market_cap,
        nullif(payload ->> 'defi_to_eth_ratio', '')::numeric as defi_to_eth_ratio,
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
    defi_market_cap,
    eth_market_cap,
    defi_to_eth_ratio,
    extracted_at,
    loaded_at,
    raw_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
