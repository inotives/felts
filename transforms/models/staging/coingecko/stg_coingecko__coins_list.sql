with source as (
    select *
    from {{ source('coingecko', 'raw_coins_list') }}
    where is_valid
),

ranked as (
    select
        payload ->> 'id' as coin_id,
        payload ->> 'symbol' as coin_symbol,
        payload ->> 'name' as coin_name,
        id as raw_record_id,
        source_record_id,
        extracted_at,
        loaded_at,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by payload ->> 'id'
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

select
    coin_id,
    coin_symbol,
    coin_name,
    raw_record_id,
    source_record_id,
    extracted_at,
    loaded_at,
    batch_id,
    raw_payload
from ranked
where row_number = 1
