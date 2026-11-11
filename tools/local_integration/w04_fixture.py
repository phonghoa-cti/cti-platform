"""Fixture W04 tổng hợp dùng chung một SQLite cho CRUD và W02 lookup."""

from __future__ import annotations

from pathlib import Path

from portal_api.assets import AssetStore
from portal_api.technologies import TechnologyStore
from tools.local_integration.w02_fixture import W02FixtureLookupPort, build_w02_fixture


def build_w04_fixture(db_path: str | Path) -> tuple[AssetStore, W02FixtureLookupPort]:
    """Khởi tạo asset store opt-in và giữ nguồn lookup W02 deterministic."""

    asset_store = AssetStore(db_path)
    asset_store.initialize()
    return asset_store, build_w02_fixture()


def build_w04_technology_fixture(
    db_path: str | Path,
) -> tuple[AssetStore, TechnologyStore, W02FixtureLookupPort]:
    """Khởi tạo hai store opt-in trên cùng DB trước khi nhận request."""

    asset_store, lookup_port = build_w04_fixture(db_path)
    technology_store = TechnologyStore(db_path)
    technology_store.initialize()
    return asset_store, technology_store, lookup_port
