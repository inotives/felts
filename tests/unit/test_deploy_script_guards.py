from pathlib import Path


def _script(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


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


def test_update_access_does_not_delete_or_update_prod_data() -> None:
    script = _script("scripts/update-prod-data-access.sh").upper()

    for forbidden in ("DROP ", "TRUNCATE ", "DELETE "):
        assert forbidden not in script
    assert "UPDATE " not in script.replace("UPDATED FELTS_AI", "")
