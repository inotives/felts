"""Generated Alphavantage CLI entrypoints."""

import argparse
from collections.abc import Sequence
from typing import Any

from felts.sources.alphavantage.constants import ENDPOINTS
from felts.sources.alphavantage.runner import run_alphavantage_source


def main(argv: Sequence[str] | None = None) -> int:
    from felts.cli import main as felts_main

    return felts_main(argv)


def register_cli(subparsers: Any) -> None:
    source = subparsers.add_parser("alphavantage")
    entities = source.add_subparsers(dest="alphavantage_entity")
    for entity, endpoint in ENDPOINTS.items():
        command = entities.add_parser(entity.replace("_", "-"))
        for name in endpoint.runtime_params:
            command.add_argument(f"--{name.replace('_', '-')}", action="append", required=True)
        command.set_defaults(handler=_run, entity=entity)


def _run(args: argparse.Namespace) -> int:
    endpoint = ENDPOINTS[args.entity]
    runtime_params = {name: getattr(args, name) for name in endpoint.runtime_params}
    summary = run_alphavantage_source(
        entities=[args.entity],
        runtime_params=runtime_params,
    )
    entity = summary.entities[0]
    print(
        f"source={summary.source} entity={entity.entity} "
        f"extracted={entity.extracted_count} inserted={entity.inserted_count} "
        f"skipped_duplicate={entity.skipped_duplicate_count} "
        f"invalid={entity.invalid_count} failed={entity.failed_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
