"""CoinGecko CLI entrypoints."""

import argparse
from collections.abc import Sequence
from typing import Any

from felts.sources.coingecko.constants import SUPPORTED_ENTITIES
from felts.sources.coingecko.runner import run_coingecko_source


def main(argv: Sequence[str] | None = None) -> int:
    from felts.cli import main as felts_main

    return felts_main(argv)


def register_cli(subparsers: Any) -> None:
    coingecko = subparsers.add_parser("coingecko")
    coingecko_subparsers = coingecko.add_subparsers(dest="coingecko_command")
    run = coingecko_subparsers.add_parser("run")
    run.add_argument(
        "--entities",
        nargs="+",
        choices=SUPPORTED_ENTITIES,
        default=None,
        help="CoinGecko entities to run; defaults to all Phase 02 entities.",
    )
    run.set_defaults(handler=_run)


def _run(args: argparse.Namespace) -> int:
    summary = run_coingecko_source(entities=args.entities)
    print(f"source={summary.source}")
    for entity in summary.entities:
        print(
            f"entity={entity.entity} "
            f"extracted={entity.extracted_count} "
            f"inserted={entity.inserted_count} "
            f"skipped_duplicate={entity.skipped_duplicate_count} "
            f"invalid={entity.invalid_count} "
            f"failed={entity.failed_count}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
