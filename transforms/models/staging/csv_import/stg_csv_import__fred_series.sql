with source as (
    select *
    from {{ source('csv_import', 'raw_fred_series') }}
    where is_valid
),

ranked as (
    select
        nullif(payload ->> 'observation_date', '')::date as observation_date,
        payload #>> '{_felts,identity,series_id}' as series_id,
        nullif(payload ->> (payload #>> '{_felts,identity,series_id}'), '')::numeric as value,
        extracted_at,
        loaded_at,
        id as raw_record_id,
        source_record_id,
        batch_id,
        payload as raw_payload,
        row_number() over (
            partition by payload #>> '{_felts,identity,series_id}', payload ->> 'observation_date'
            order by extracted_at desc, loaded_at desc
        ) as row_number
    from source
)

select
    observation_date,
    series_id,
    value,
    extracted_at,
    loaded_at,
    raw_record_id,
    source_record_id,
    batch_id,
    raw_payload
from ranked
where row_number = 1
