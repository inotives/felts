from felts.sources.coingecko.deployments import build_source_deployment_specs


def test_build_source_deployment_specs_registers_all_entities() -> None:
    specs = build_source_deployment_specs()

    assert [spec.entity for spec in specs] == [
        "coins_list",
        "asset_platforms_list",
        "global",
        "global_defi",
        "coins_markets",
    ]
    assert specs[0].name == "coingecko-coins-list-source"
    assert specs[-1].name == "coingecko-coins-markets-source"


def test_coins_markets_deployment_has_no_schedule() -> None:
    specs = {spec.entity: spec for spec in build_source_deployment_specs()}

    assert specs["coins_markets"].schedules is None
    assert specs["global"].schedules is not None
