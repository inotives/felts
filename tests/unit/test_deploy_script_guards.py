from pathlib import Path


def _script(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _allowlisted_views() -> list[str]:
    allowlist = Path("settings/felts-prod-data-views.txt")
    return [
        line.strip()
        for line in allowlist.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_deploy_bootstrap_check_uses_boolean_and_not_integer_concat() -> None:
    script = _script("scripts/deploy-linux-mint.sh")

    assert "AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prefect')" in script
    assert "::int ||" not in script


def test_deploy_does_not_reconcile_ai_access() -> None:
    script = _script("scripts/deploy-linux-mint.sh")

    assert "felts_ai" not in script
    assert "ROTATE_AI_PASSWORD=" not in script


def test_update_access_does_not_restart_or_rebuild_postgres() -> None:
    script = _script("scripts/update-prod-data-access.sh")

    assert "felts_ai" in script
    assert "docker compose up" not in script
    assert "--build" not in script
    assert "systemctl" not in script


def test_update_access_reads_committed_allowlist_instead_of_inline_views() -> None:
    script = _script("scripts/update-prod-data-access.sh")

    assert "settings/felts-prod-data-views.txt" in script
    assert "ALLOWED_VIEWS" in script
    for view_name in _allowlisted_views():
        assert view_name not in script


def test_update_access_grants_schema_and_relation_identifiers() -> None:
    script = _script("scripts/update-prod-data-access.sh")

    assert "-v ON_ERROR_STOP=1" in script
    assert "SELECT DISTINCT split_part(allowed.view_ref, '.', 1)" in script
    assert "SELECT 1 FROM pg_namespace WHERE nspname = view_schema" in script
    assert "GRANT USAGE ON SCHEMA %I TO felts_ai" in script
    assert "GRANT SELECT ON TABLE %I.%I TO felts_ai" in script
    assert "split_part(view_ref, '.', 1)" in script
    assert "split_part(view_ref, '.', 2)" in script


def test_update_access_rejects_malformed_allowlist_entries_before_psql() -> None:
    script = _script("scripts/update-prod-data-access.sh")

    assert "Malformed allowlist entry" in script
    assert script.index("Malformed allowlist entry") < script.index(
        "docker compose exec -T postgres psql"
    )


def test_update_access_does_not_delete_or_update_prod_data() -> None:
    script = _script("scripts/update-prod-data-access.sh").upper()

    for forbidden in ("DROP ", "TRUNCATE ", "DELETE "):
        assert forbidden not in script
    assert "UPDATE " not in script.replace("UPDATED FELTS_AI", "")
