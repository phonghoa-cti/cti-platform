import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "deploy" / "demo" / "validate_compose_config.py"
ADMIN_TOKEN = "11111111-1111-4111-8111-111111111111"
ENCRYPTION_KEY = base64.b64encode(b"x" * 32).decode()


def core_config() -> dict:
    return {
        "services": {
            "redis": {},
            "elasticsearch": {},
            "minio": {
                "environment": {
                    "MINIO_ROOT_USER": "validate-only",
                    "MINIO_ROOT_PASSWORD": "validate-only",
                }
            },
            "rabbitmq": {
                "environment": {
                    "RABBITMQ_DEFAULT_USER": "validate-only",
                    "RABBITMQ_DEFAULT_PASS": "validate-only",
                }
            },
            "opencti": {
                "environment": {
                    "APP__ADMIN__EMAIL": "demo@example.invalid",
                    "APP__ADMIN__PASSWORD": "validate-only",
                    "APP__ADMIN__TOKEN": ADMIN_TOKEN,
                    "APP__ENCRYPTION_KEY": ENCRYPTION_KEY,
                    "APP__HEALTH_ACCESS_KEY": "validate-only",
                    "MINIO__ACCESS_KEY": "validate-only",
                    "MINIO__SECRET_KEY": "validate-only",
                    "RABBITMQ__USERNAME": "validate-only",
                    "RABBITMQ__PASSWORD": "validate-only",
                }
            },
            "worker": {
                "environment": {
                    "OPENCTI_URL": "http://opencti:8080",
                    "OPENCTI_TOKEN": ADMIN_TOKEN,
                }
            },
        }
    }


def run_preflight(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )


def test_accepts_valid_core_without_connectors() -> None:
    result = run_preflight(json.dumps(core_config()))

    assert result.returncode == 0
    assert "PASS" in result.stdout


@pytest.mark.parametrize(
    ("service_name", "connector_id"),
    [
        ("connector-mitre", "22222222-2222-4222-8222-222222222222"),
        ("connector-import-file-stix", "33333333-3333-4333-8333-333333333333"),
    ],
)
def test_accepts_non_uuid_api_token_for_valid_connector(service_name: str, connector_id: str) -> None:
    config = core_config()
    config["services"][service_name] = {
        "environment": {
            "CONNECTOR_ID": connector_id,
            "OPENCTI_TOKEN": "opencti-v7-token-not-required-to-be-a-uuid",
        }
    }

    result = run_preflight(json.dumps(config))

    assert result.returncode == 0


def test_rejects_invalid_admin_uuid_without_leaking_input() -> None:
    marker = "SENTINEL_PASSWORD_MUST_NOT_LEAK"
    config = core_config()
    config["services"]["opencti"]["environment"]["APP__ADMIN__PASSWORD"] = marker
    config["services"]["opencti"]["environment"]["APP__ADMIN__TOKEN"] = "not-a-uuid"

    result = run_preflight(json.dumps(config))

    assert result.returncode != 0
    assert "APP__ADMIN__TOKEN" in result.stderr
    assert marker not in result.stdout
    assert marker not in result.stderr


@pytest.mark.parametrize("encryption_key", ["not-base64", base64.b64encode(b"short").decode()])
def test_rejects_invalid_or_short_encryption_key(encryption_key: str) -> None:
    config = core_config()
    config["services"]["opencti"]["environment"]["APP__ENCRYPTION_KEY"] = encryption_key

    result = run_preflight(json.dumps(config))

    assert result.returncode != 0
    assert "APP__ENCRYPTION_KEY" in result.stderr


@pytest.mark.parametrize(
    ("connector_id", "connector_token", "expected_field"),
    [
        ("not-a-uuid", "connector-token", "CONNECTOR_ID"),
        ("22222222-2222-4222-8222-222222222222", ADMIN_TOKEN, "OPENCTI_TOKEN"),
    ],
)
def test_rejects_invalid_connector_identity_or_reused_admin_token(
    connector_id: str, connector_token: str, expected_field: str
) -> None:
    config = core_config()
    config["services"]["connector-mitre"] = {
        "environment": {"CONNECTOR_ID": connector_id, "OPENCTI_TOKEN": connector_token}
    }

    result = run_preflight(json.dumps(config))

    assert result.returncode != 0
    assert expected_field in result.stderr


@pytest.mark.parametrize("payload", ["", "{not-json", "[]", "{}"])
def test_rejects_empty_malformed_or_missing_structure(payload: str) -> None:
    result = run_preflight(payload)

    assert result.returncode != 0
    assert "preflight:" in result.stderr
    assert "Traceback" not in result.stderr


def test_rejects_missing_core_service() -> None:
    config = core_config()
    del config["services"]["rabbitmq"]

    result = run_preflight(json.dumps(config))

    assert result.returncode != 0
    assert "service.rabbitmq" in result.stderr
