from felts.sources.coingecko.deployments import build_source_deployment_specs


def test_build_source_deployment_specs_registers_all_entities() -> None:
    specs = build_source_deployment_specs()

    assert [spec.entity for spec in specs] == [
        "coins_list",
        "asset_platforms_list",
        "global",
        "global_defi",
        "coins_markets",
        "coins_ohlc",
        "coins_market_chart",
    ]
    assert specs[0].name == "coingecko-coins-list-source"
    assert specs[-1].name == "coingecko-coins-market-chart-source"


def test_phase_14_coingecko_deployment_schedules_match_spec() -> None:
    specs = {spec.entity: spec for spec in build_source_deployment_specs()}

    assert specs["coins_ohlc"].schedules is not None
    assert specs["coins_ohlc"].schedules[0].cron == "0 3 * * *"
    assert specs["coins_market_chart"].schedules is not None
    assert specs["coins_market_chart"].schedules[0].cron == "15 3 * * *"
    assert specs["coins_markets"].schedules is not None
    assert specs["coins_markets"].schedules[0].cron == "30 3 * * *"
    assert specs["global"].schedules is not None
