"""Factory cấu hình loopback tổng hợp, tách khỏi đường production."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from portal_api.settings import Settings, SettingsError


def make_local_settings(
    db_path: Path,
    temp_root: Path,
    gateway_port: int,
    roles_by_subject: Mapping[str, frozenset[str]],
) -> Settings:
    """Tạo Settings HTTP chỉ cho DB chưa tồn tại nằm trong temp root do run sở hữu."""

    if not isinstance(db_path, Path) or not isinstance(temp_root, Path):
        raise SettingsError("DB và temp root phải là Path")
    if isinstance(gateway_port, bool) or not isinstance(gateway_port, int):
        raise SettingsError("gateway port phải là số nguyên")
    if not 1 <= gateway_port <= 65535:
        raise SettingsError("gateway port ngoài phạm vi")
    try:
        root = temp_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SettingsError("temp root không tồn tại") from exc
    if not root.is_dir():
        raise SettingsError("temp root không phải thư mục")
    database = db_path.resolve(strict=False)
    if database.exists() or database == root or not database.is_relative_to(root):
        raise SettingsError("DB phải là file mới trong temp root")
    return Settings._for_local_integration(
        db_path=database,
        portal_origin=f"http://127.0.0.1:{gateway_port}",
        roles_by_subject=roles_by_subject,
    )
