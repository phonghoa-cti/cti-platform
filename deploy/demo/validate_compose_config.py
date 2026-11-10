"""Kiểm tra cấu hình Compose đã render mà không in dữ liệu đầu vào."""

from __future__ import annotations

import base64
import binascii
import json
import sys
import uuid
from typing import Any

CORE_SERVICES = ("redis", "elasticsearch", "minio", "rabbitmq", "opencti", "worker")
REQUIRED_ENV = {
    "minio": ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"),
    "rabbitmq": ("RABBITMQ_DEFAULT_USER", "RABBITMQ_DEFAULT_PASS"),
    "opencti": (
        "APP__ADMIN__EMAIL",
        "APP__ADMIN__PASSWORD",
        "APP__ADMIN__TOKEN",
        "APP__ENCRYPTION_KEY",
        "APP__HEALTH_ACCESS_KEY",
        "MINIO__ACCESS_KEY",
        "MINIO__SECRET_KEY",
        "RABBITMQ__USERNAME",
        "RABBITMQ__PASSWORD",
    ),
    "worker": ("OPENCTI_URL", "OPENCTI_TOKEN"),
}
CONNECTOR_SERVICES = ("connector-mitre", "connector-import-file-stix")


def is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_uuid4(value: Any) -> bool:
    if not is_nonempty_text(value):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and parsed.variant == uuid.RFC_4122


def is_base64_key(value: Any) -> bool:
    if not is_nonempty_text(value):
        return False
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return False
    return len(decoded) >= 32


def environment_for(service: Any) -> dict[str, Any] | None:
    if not isinstance(service, dict):
        return None
    environment = service.get("environment")
    return environment if isinstance(environment, dict) else None


def validate(config: Any) -> tuple[list[tuple[str, str]], int]:
    errors: list[tuple[str, str]] = []
    if not isinstance(config, dict) or not isinstance(config.get("services"), dict):
        return [("input.services", "object-required")], 0

    services = config["services"]
    for name in CORE_SERVICES:
        if not isinstance(services.get(name), dict):
            errors.append((f"service.{name}", "object-required"))

    for service_name, fields in REQUIRED_ENV.items():
        environment = environment_for(services.get(service_name))
        if environment is None:
            errors.append((f"service.{service_name}.environment", "object-required"))
            continue
        for field in fields:
            if not is_nonempty_text(environment.get(field)):
                errors.append((f"{service_name}.{field}", "nonempty-text-required"))

    opencti_environment = environment_for(services.get("opencti")) or {}
    admin_token = opencti_environment.get("APP__ADMIN__TOKEN")
    if not is_uuid4(admin_token):
        errors.append(("APP__ADMIN__TOKEN", "uuid-v4-required"))
    if not is_base64_key(opencti_environment.get("APP__ENCRYPTION_KEY")):
        errors.append(("APP__ENCRYPTION_KEY", "base64-decoded-minimum-32-bytes"))

    worker_environment = environment_for(services.get("worker")) or {}
    worker_token = worker_environment.get("OPENCTI_TOKEN")
    if is_nonempty_text(admin_token) and worker_token != admin_token:
        errors.append(("worker.OPENCTI_TOKEN", "must-match-admin-token"))

    connector_count = 0
    for service_name in CONNECTOR_SERVICES:
        if service_name not in services:
            continue
        connector_count += 1
        environment = environment_for(services.get(service_name))
        if environment is None:
            errors.append((f"service.{service_name}.environment", "object-required"))
            continue
        if not is_uuid4(environment.get("CONNECTOR_ID")):
            errors.append((f"{service_name}.CONNECTOR_ID", "uuid-v4-required"))
        connector_token = environment.get("OPENCTI_TOKEN")
        if not is_nonempty_text(connector_token):
            errors.append((f"{service_name}.OPENCTI_TOKEN", "nonempty-text-required"))
        elif connector_token == admin_token:
            errors.append((f"{service_name}.OPENCTI_TOKEN", "must-differ-from-admin-token"))

    return errors, connector_count


def main() -> int:
    try:
        raw_input = sys.stdin.buffer.read()
        if not raw_input.strip():
            raise ValueError
        config = json.loads(raw_input)
        errors, connector_count = validate(config)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError):
        print("preflight: FAIL field=input rule=valid-compose-json-required", file=sys.stderr)
        return 2
    except Exception:
        print("preflight: FAIL field=input rule=unsupported-structure", file=sys.stderr)
        return 2

    if errors:
        for field, rule in errors:
            print(f"preflight: FAIL field={field} rule={rule}", file=sys.stderr)
        return 1

    print(f"preflight: PASS core_services={len(CORE_SERVICES)} connectors={connector_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
