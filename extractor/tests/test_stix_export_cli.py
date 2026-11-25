from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from test_stix_export import approve_draft, exporter_config

from phonghoa_extractor import store

SCRIPT = Path(__file__).parents[1] / "draft" / "stix_export.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )


def test_cli_exports_one_bundle_with_exact_safe_stdout_and_idempotent_reexport(tmp_path: Path):
    db = tmp_path / "approved.sqlite"
    draft_id = approve_draft(db, selected=(2,))
    config = tmp_path / "exporter.json"
    config.write_text(json.dumps(exporter_config()), encoding="utf-8")
    output = tmp_path / "bundle.json"

    args = (
        "export-approved",
        "--db",
        str(db),
        "--id",
        str(draft_id),
        "--exporter-config",
        str(config),
        "--output",
        str(output),
    )
    first = run_cli(*args)
    before = output.stat().st_mtime_ns
    second = run_cli(*args)

    assert first.returncode == second.returncode == 0
    summary = json.loads(first.stdout)
    assert summary == {
        "draft_id": draft_id,
        "bundle_sha256": summary["bundle_sha256"],
        "object_count": 4,
    }
    assert len(summary["bundle_sha256"]) == 64
    assert first.stdout == second.stdout == json.dumps(summary, separators=(",", ":")) + "\n"
    assert first.stderr == second.stderr == ""
    assert output.stat().st_mtime_ns == before
    assert not Path(str(output) + ".manifest.json").exists()
    bundle = json.loads(output.read_bytes())
    assert [obj["type"] for obj in bundle["objects"]] == [
        "marking-definition",
        "identity",
        "domain-name",
        "report",
    ]


def test_cli_errors_are_one_safe_line_and_do_not_create_or_clobber_output(tmp_path: Path):
    db = tmp_path / "pending.sqlite"
    store.save_draft(
        db, exporter_draft := __import__("test_stix_export").make_ioc_draft(), created_by_subject="author"
    )
    assert exporter_draft["source"]["name"] == "synthetic.txt"
    config = tmp_path / "exporter.json"
    config.write_text(json.dumps(exporter_config()), encoding="utf-8")
    output = tmp_path / "bundle.json"
    output.write_bytes(b"keep-me")

    result = run_cli(
        "export-approved",
        "--db",
        str(db),
        "--id",
        "1",
        "--exporter-config",
        str(config),
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == '{"error":"export_failed"}\n'
    assert output.read_bytes() == b"keep-me"


@pytest.mark.parametrize(
    "change",
    [
        {"tlp": []},
        {"tlp": {}},
        {"created": "0001-01-01T00:00:00+01:00"},
        {"created": "9999-12-31T23:59:59-01:00"},
    ],
)
def test_cli_config_domain_errors_are_one_safe_line(tmp_path: Path, change: dict[str, object]):
    config_value = exporter_config()
    config_value.update(change)
    config = tmp_path / "exporter.json"
    config.write_text(json.dumps(config_value), encoding="utf-8")
    output = tmp_path / "bundle.json"

    result = run_cli(
        "export-approved",
        "--db",
        str(tmp_path / "absent.sqlite"),
        "--id",
        "1",
        "--exporter-config",
        str(config),
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == '{"error":"export_failed"}\n'
    assert not output.exists()


def test_cli_rejects_output_aliases_for_database_config_and_sidecars(tmp_path: Path):
    db = tmp_path / "approved.sqlite"
    draft_id = approve_draft(db, selected=(2,))
    config = tmp_path / "exporter.json"
    config.write_text(json.dumps(exporter_config()), encoding="utf-8")

    for output in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm"), config):
        before_db = db.read_bytes()
        before_config = config.read_bytes()
        result = run_cli(
            "export-approved",
            "--db",
            str(db),
            "--id",
            str(draft_id),
            "--exporter-config",
            str(config),
            "--output",
            str(output),
        )
        assert result.returncode == 1
        assert db.read_bytes() == before_db
        assert config.read_bytes() == before_config


def test_cli_help_uses_argparse_exit_zero():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "export-approved" in result.stdout
