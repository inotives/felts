select
    internal_asset_id,
    asset_name,
    asset_symbol,
    asset_type
from {{ ref('internal_assets') }}
