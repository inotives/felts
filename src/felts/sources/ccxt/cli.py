"""CCXT CLI entrypoints."""

import argparse
from collections.abc import Sequence
from typing import Any

from felts.sources.ccxt.constants import SUPPORTED_ENTITIES
from felts.sources.ccxt.runner import run_ccxt_source


def main(argv: Sequence[str] | None = None) -> int:
    from felts.cli import main as felts_main

    return felts_main(argv)


def register_cli(subparsers: Any) -> None:
    ccxt = subparsers.add_parser("ccxt")
    ccxt_subparsers = ccxt.add_subparsers(dest="ccxt_command")
    run = ccxt_subparsers.add_parser("run")
    run.add_argument(
        "--entities",
        nargs="+",
        choices=SUPPORTED_ENTITIES,
        default=None,
        help="CCXT entities to run; defaults to all supported entities.",
    )
    run.set_defaults(handler=_run)


def _run(args: argparse.Namespace) -> int:
    summary = run_ccxt_source(entities=args.entities)
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
    return 1 if summary.failed_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
