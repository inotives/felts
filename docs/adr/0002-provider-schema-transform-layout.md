# Provider Schema Transform Layout

Felts keeps source-specific raw, staging, intermediate, and mart models in the same source schema. For CoinGecko, that means objects such as `coingecko.raw_coins_list`, `coingecko.stg_coingecko__coins_list`, and `coingecko.mart_coingecko__coins` live together.

This layout keeps provider-specific lineage easy to inspect and avoids spreading one source across separate raw, staging, and mart schemas. Model name prefixes identify lifecycle layer inside the provider schema: `raw_`, `stg_`, `int_`, and `mart_`.

The trade-off is that schema names no longer identify model layer by themselves. Felts accepts that trade-off because source ownership is the stronger organizing boundary for early source development. Cross-source marts remain deferred and should use a separate shared analytics schema when introduced.
