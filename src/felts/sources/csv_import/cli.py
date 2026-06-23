"""CSV import CLI entrypoints."""

import argparse
from typing import Any

from felts.sources.csv_import.runner import run_csv_import


def register_cli(subparsers: Any) -> None:
    csv_parser = subparsers.add_parser("csv")
    csv_subparsers = csv_parser.add_subparsers(dest="csv_command")
    import_parser = csv_subparsers.add_parser("import")
    import_parser.add_argument("--contract", required=True)
    import_parser.add_argument("--input-uri", required=True)
    import_parser.add_argument("--start-date")
    import_parser.add_argument("--end-date")
    import_parser.set_defaults(handler=_import)


def _import(args: argparse.Namespace) -> int:
    summary = run_csv_import(
        contract_id=args.contract,
        input_uri=args.input_uri,
        start_date=args.start_date,
        end_date=args.end_date,
    )
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
