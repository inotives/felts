select
    internal_asset_id,
    provider_source,
    provider_asset_id
from {{ ref('asset_provider_mappings') }}
