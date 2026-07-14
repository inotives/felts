"""Top-level Felts CLI router."""

# ruff: noqa: I001

import argparse
from collections.abc import Sequence

from felts.sources.coingecko.cli import register_cli as register_coingecko_cli
from felts.sources.csv_import.cli import register_cli as register_csv_cli
from felts.sources.agent_pipe.cli import register_cli as register_agent_pipe_cli

# scaffold: source-cli-imports:start
from felts.sources.alphavantage.cli import register_cli as register_alphavantage_cli
# scaffold: source-cli-imports:end


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return int(handler(args))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="felts")
    subparsers = parser.add_subparsers(dest="command")
    register_coingecko_cli(subparsers)
    register_csv_cli(subparsers)
    register_agent_pipe_cli(subparsers)
    # scaffold: source-cli-registrations:start
    register_alphavantage_cli(subparsers)
    # scaffold: source-cli-registrations:end
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
