"""CLI demo chỉ chạy fixture, không kết nối CE thật."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from connectors.playbook.engine import Scope, W03Matcher, run
from connectors.playbook.rules import load_rules
from connectors.playbook.source import FixtureSource
from portal_api.cves import CveReadService, FixtureCveReadPort
from portal_api.technologies import TechnologyStore

ROOT = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(description="F19 playbook synthetic fixture")
    parser.add_argument("--fixture", type=Path, default=ROOT / "tests" / "fixtures" / "demo.sse")
    parser.add_argument("--rules", type=Path, default=ROOT / "rules" / "default.yaml")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--persist", action="store_true", help="Lưu intent fixture, không publish")
    parser.add_argument("--technology-db", type=Path)
    parser.add_argument("--cve-fixture", type=Path)
    args = parser.parse_args()
    if args.persist and args.db is None:
        parser.error("--persist requires --db")
    if bool(args.technology_db) != bool(args.cve_fixture):
        parser.error("W03 requires both --technology-db and --cve-fixture")
    scope = Scope(
        "demo", "fixture", {"mark-clear": "TLP:CLEAR", "mark-green": "TLP:GREEN", "mark-red": "TLP:RED"}
    )
    matcher = None
    if args.technology_db:
        matcher = W03Matcher(
            scope.tenant,
            CveReadService(FixtureCveReadPort(args.cve_fixture), TechnologyStore(args.technology_db)),
        )
    for intent in run(
        FixtureSource(args.fixture),
        load_rules(args.rules),
        scope,
        args.db,
        dry_run=not args.persist,
        matcher=matcher,
    ):
        print(json.dumps(asdict(intent), ensure_ascii=True))


if __name__ == "__main__":
    main()
