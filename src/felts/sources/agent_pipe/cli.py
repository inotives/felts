"""agent-pipe CLI entrypoints."""

import argparse
from typing import Any

from felts.sources.agent_pipe.runner import run_agent_pipe_import


def register_cli(subparsers: Any) -> None:
    agent_pipe_parser = subparsers.add_parser("agent-pipe")
    agent_pipe_subparsers = agent_pipe_parser.add_subparsers(dest="agent_pipe_command")
    import_parser = agent_pipe_subparsers.add_parser("import")
    import_parser.add_argument("--sqlite-path", required=True)
    import_parser.add_argument("--updated-since")
    import_parser.set_defaults(handler=_import)


def _import(args: argparse.Namespace) -> int:
    summary = run_agent_pipe_import(
        sqlite_path=args.sqlite_path,
        updated_since=args.updated_since,
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
