select
    asset_platform_id,
    asset_platform_name,
    extracted_at as last_seen_at,
    raw_record_id
from {{ ref('stg_coingecko__asset_platforms_list') }}
