"""Xác minh Cloudflare Access JWT và tạo principal phía server."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Protocol

import jwt

from portal_api.settings import Settings


class AuthenticationError(ValueError):
    """Token không hợp lệ; luôn trả lỗi đã làm sạch."""


class AuthenticationUnavailable(RuntimeError):
    """Nguồn khóa xác minh tạm thời không dùng được."""


class JwksClient(Protocol):
    def get_signing_key_from_jwt(self, token: str): ...


@dataclass(frozen=True)
class Principal:
    """Danh tính sau xác minh; role chỉ đến từ cấu hình server."""

    subject: str
    roles: frozenset[str]
    email: str | None = None


def _require_numeric_dates(claims: dict[str, Any]) -> None:
    for name in ("exp", "nbf", "iat"):
        if name not in claims:
            continue
        value = claims[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise AuthenticationError("invalid numeric date")


def _require_exact_audience(claims: dict[str, Any], expected: str) -> None:
    audience = claims.get("aud")
    if isinstance(audience, str):
        valid = bool(audience) and audience == expected
    elif isinstance(audience, list):
        valid = (
            bool(audience)
            and all(isinstance(value, str) and bool(value) for value in audience)
            and expected in audience
        )
    else:
        valid = False
    if not valid:
        raise AuthenticationError("invalid audience")


class AccessJwtVerifier:
    """Verifier RS256; không lấy URL hoặc thuật toán từ claim chưa tin cậy."""

    def __init__(self, settings: Settings, *, jwks_client: JwksClient | None = None):
        self._settings = settings
        self._jwks_client = jwks_client or jwt.PyJWKClient(
            settings.access_jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            cache_jwk_set=True,
            lifespan=settings.jwks_cache_seconds,
            timeout=settings.jwks_timeout,
        )

    def verify(self, token: str) -> Principal:
        if not isinstance(token, str) or not token:
            raise AuthenticationError("missing token")
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise AuthenticationError("algorithm or kid not allowed")
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._settings.access_audience,
                issuer=self._settings.access_issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
            _require_numeric_dates(claims)
            _require_exact_audience(claims, self._settings.access_audience)
        except AuthenticationError:
            raise
        except jwt.PyJWKClientConnectionError as exc:
            raise AuthenticationUnavailable("jwks unavailable") from exc
        except (jwt.InvalidTokenError, jwt.PyJWKClientError, TypeError, ValueError) as exc:
            raise AuthenticationError("invalid token") from exc
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise AuthenticationError("invalid subject")
        roles = self._settings.roles_by_subject.get(subject, frozenset())
        return Principal(subject=subject, roles=roles)
