"""Cấu hình fail-closed cho W05 API."""

from __future__ import annotations

import json
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from urllib.parse import urlsplit


class SettingsError(ValueError):
    """Cấu hình runtime thiếu hoặc không an toàn."""


def _https_origin(value: str, label: str) -> tuple[str, str]:
    if not isinstance(value, str) or not value:
        raise SettingsError(f"{label} bắt buộc")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise SettingsError(f"{label} phải là HTTPS URL tin cậy")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin, parsed.path


def _portal_origin(value: str) -> str:
    origin, path = _https_origin(value, "PORTAL_ORIGIN")
    if path not in {"", "/"} or value.endswith("/"):
        raise SettingsError("PORTAL_ORIGIN chỉ được gồm scheme/host/port")
    return origin


@dataclass(frozen=True)
class Settings:
    """Giá trị cấu hình đã kiểm trước khi tạo app."""

    db_path: Path
    access_issuer: str
    access_audience: str
    access_jwks_url: str
    portal_origin: str
    roles_by_subject: Mapping[str, frozenset[str]]
    sqlite_timeout: float = 5.0
    jwks_timeout: float = 5.0
    jwks_cache_seconds: int = 300

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Đọc cấu hình bắt buộc; không có dev fallback hoặc identity tự khai."""

        values = os.environ if env is None else env
        required = (
            "W05_DB_PATH",
            "CF_ACCESS_ISSUER",
            "CF_ACCESS_AUD",
            "CF_ACCESS_JWKS_URL",
            "PORTAL_ORIGIN",
            "W05_ROLES_JSON",
        )
        try:
            raw = {name: values[name] for name in required}
            role_values = json.loads(raw["W05_ROLES_JSON"])
            if not isinstance(role_values, dict):
                raise TypeError
            roles = {
                subject: frozenset(subject_roles)
                for subject, subject_roles in role_values.items()
                if isinstance(subject, str) and isinstance(subject_roles, list)
            }
            if len(roles) != len(role_values):
                raise TypeError
            sqlite_timeout = float(values.get("W05_SQLITE_TIMEOUT", "5"))
            jwks_timeout = float(values.get("W05_JWKS_TIMEOUT", "5"))
            jwks_cache_seconds = int(values.get("W05_JWKS_CACHE_SECONDS", "300"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SettingsError("Thiếu hoặc sai cấu hình W05 API") from exc
        return cls(
            db_path=Path(raw["W05_DB_PATH"]),
            access_issuer=raw["CF_ACCESS_ISSUER"],
            access_audience=raw["CF_ACCESS_AUD"],
            access_jwks_url=raw["CF_ACCESS_JWKS_URL"],
            portal_origin=raw["PORTAL_ORIGIN"],
            roles_by_subject=roles,
            sqlite_timeout=sqlite_timeout,
            jwks_timeout=jwks_timeout,
            jwks_cache_seconds=jwks_cache_seconds,
        )

    def __post_init__(self) -> None:
        issuer_origin, issuer_path = _https_origin(self.access_issuer, "CF_ACCESS_ISSUER")
        if issuer_path or self.access_issuer != issuer_origin:
            raise SettingsError("CF_ACCESS_ISSUER phải là origin HTTPS chính xác")
        jwks_origin, jwks_path = _https_origin(self.access_jwks_url, "CF_ACCESS_JWKS_URL")
        if jwks_origin != issuer_origin or not jwks_path:
            raise SettingsError("JWKS phải cùng origin với issuer và có path")
        if not isinstance(self.access_audience, str) or not self.access_audience.strip():
            raise SettingsError("CF_ACCESS_AUD bắt buộc")
        portal_origin = _portal_origin(self.portal_origin)
        if not isinstance(self.db_path, Path):
            object.__setattr__(self, "db_path", Path(self.db_path))
        if not isinstance(self.roles_by_subject, Mapping):
            raise SettingsError("roles_by_subject phải là mapping phía server")
        normalized: dict[str, frozenset[str]] = {}
        for subject, roles in self.roles_by_subject.items():
            if not isinstance(subject, str) or not subject.strip() or not isinstance(roles, frozenset):
                raise SettingsError("role mapping không hợp lệ")
            if not all(isinstance(role, str) and role for role in roles):
                raise SettingsError("role mapping không hợp lệ")
            normalized[subject] = roles
        for label, value in (("sqlite_timeout", self.sqlite_timeout), ("jwks_timeout", self.jwks_timeout)):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise SettingsError(f"{label} phải là số hữu hạn dương")
        if (
            isinstance(self.jwks_cache_seconds, bool)
            or not isinstance(self.jwks_cache_seconds, int)
            or self.jwks_cache_seconds <= 0
        ):
            raise SettingsError("jwks_cache_seconds phải là số nguyên dương")
        object.__setattr__(self, "access_issuer", issuer_origin)
        object.__setattr__(self, "portal_origin", portal_origin)
        object.__setattr__(self, "roles_by_subject", MappingProxyType(normalized))
