select
    internal_asset_platform_id,
    asset_platform_name
from {{ ref('internal_asset_platforms') }}
