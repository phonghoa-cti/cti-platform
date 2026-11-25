from __future__ import annotations

import json
from pathlib import Path

import pytest

from portal_api.settings import Settings, SettingsError
from tools.local_integration.local_settings import make_local_settings

ROLES = {"admin-sub": frozenset({"admin"})}


def test_local_origin_requires_owned_temp_db(tmp_path: Path) -> None:
    db_path = tmp_path / "owned.sqlite"

    settings = make_local_settings(db_path, tmp_path, 32123, ROLES)

    assert settings.portal_origin == "http://127.0.0.1:32123"
    assert settings.db_path == db_path
    assert not db_path.exists()

    existing = tmp_path / "existing.sqlite"
    existing.touch()
    with pytest.raises(SettingsError):
        make_local_settings(existing, tmp_path, 32123, ROLES)
    with pytest.raises(SettingsError):
        make_local_settings(tmp_path.parent / "outside.sqlite", tmp_path, 32123, ROLES)


@pytest.mark.parametrize("port", [None, True, False, 0, 65536, -1, "32123", [], {}])
def test_local_origin_rejects_noncanonical_address(tmp_path: Path, port: object) -> None:
    with pytest.raises(SettingsError):
        make_local_settings(tmp_path / "owned.sqlite", tmp_path, port, ROLES)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:32123",
        "http://192.168.1.4:32123",
        "http://[::1]:32123",
        "http://user@127.0.0.1:32123",
        "http://127.0.0.1:32123/path",
        "http://127.0.0.1:32123?query=1",
        "http://127.0.0.1:32123#fragment",
        "http://127.0.0.1:32123/",
    ],
)
def test_production_constructor_rejects_noncanonical_http(origin: str, tmp_path: Path) -> None:
    with pytest.raises(SettingsError):
        Settings(
            db_path=tmp_path / "db.sqlite",
            access_issuer="https://access.synthetic.test",
            access_audience="w05-local-integration",
            access_jwks_url="https://access.synthetic.test/certs",
            portal_origin=origin,
            roles_by_subject=ROLES,
        )


def test_production_settings_reject_http_despite_debug_env(tmp_path: Path) -> None:
    env = {
        "W05_DB_PATH": str(tmp_path / "db.sqlite"),
        "CF_ACCESS_ISSUER": "https://access.synthetic.test",
        "CF_ACCESS_AUD": "w05-local-integration",
        "CF_ACCESS_JWKS_URL": "https://access.synthetic.test/certs",
        "PORTAL_ORIGIN": "http://127.0.0.1:32123",
        "W05_ROLES_JSON": json.dumps({"admin-sub": ["admin"]}),
        "DEBUG": "1",
        "TEST": "1",
        "LOCAL": "1",
    }

    with pytest.raises(SettingsError):
        Settings.from_env(env)
