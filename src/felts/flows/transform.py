"""Shared dbt transform flow."""

import subprocess

from prefect import flow, task

from felts.config import Settings, get_settings


@task
def run_dbt_command(command: str, selector: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    args = [
        "uv",
        "run",
        settings.dbt_command,
        command,
        "--project-dir",
        str(settings.dbt_project_dir),
        "--profiles-dir",
        str(settings.dbt_profiles_dir),
        "--select",
        selector,
    ]
    subprocess.run(args, check=True)


@flow(name="dbt-transform", retries=1, retry_delay_seconds=30)
def transform_flow(selector: str, run_tests: bool = True) -> None:
    run_dbt_command("run", selector)
    if run_tests:
        run_dbt_command("test", selector)
