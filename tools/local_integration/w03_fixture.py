"""Fixture W03 tổng hợp, opt-in, dùng TechnologyStore trên SQLite W04."""

from __future__ import annotations

from pathlib import Path

from portal_api.cves import FixtureCveReadPort
from tools.local_integration.w04_fixture import build_w04_technology_fixture

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "w03-cves-synthetic.json"


def build_w03_fixture(db_path: str | Path):
    """Khởi tạo schema/seed trước listener; request W03 chỉ đọc mode=ro."""

    asset_store, technology_store, lookup_port = build_w04_technology_fixture(db_path)
    technology_store.create("Fortinet", "FortiOS", "7.4.2", "Synthetic W03", "setup-w03")
    technology_store.create("Cisco", "IOS XE", "17.9", "Synthetic W03", "setup-w03")
    return asset_store, technology_store, lookup_port, FixtureCveReadPort(FIXTURE_PATH)
