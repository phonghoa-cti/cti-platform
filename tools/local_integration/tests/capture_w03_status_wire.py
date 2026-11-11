"""Capture W03 status wire fixtures from the real loopback gateway."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- standalone capture exposes repository packages before imports

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for source_root in (ROOT / "core", ROOT / "extractor"):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

import httpx

from portal_api.cves import CvesUnavailable, FixtureCveReadPort, _validate_dataset
from tools.local_integration.runner import LocalRun

RELATION = "/api/cves/CVE-2026-2001/technologies/1"
STATUS = RELATION + "/status"
HISTORY = RELATION + "/status-history?limit=25"
HISTORY_100 = RELATION + "/status-history?limit=100"


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def request(method: str, base: str, path: str, **kwargs: object) -> httpx.Response:
    return httpx.request(method, base + path, timeout=5, **kwargs)


def save_body(
    context: dict[str, object], version: int, *, note: str = "Wire fixture W03"
) -> dict[str, object]:
    return {
        "status": "patching",
        "note": note,
        "expected_status_version": version,
        "expected_technology_record_version": context["technology_record_version"],
        "expected_dataset_id": context["dataset_id"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    observed: dict[str, int] = {}

    with LocalRun("w03-status-it", duration_seconds=30, start_ui=False) as run:
        unset = request("GET", run.url, STATUS)
        observed["unset"] = unset.status_code
        write(output / "unset.json", unset.json())
        context = unset.json()["context"]

        committed = request(
            "PUT",
            run.url,
            STATUS,
            headers={"Origin": run.url},
            json=save_body(context, 0),
        )
        observed["committed"] = committed.status_code
        write(output / "committed.json", committed.json())

        history = request("GET", run.url, HISTORY)
        observed["history"] = history.status_code
        write(output / "history.json", history.json())

        changed = request(
            "PUT",
            run.url,
            "/api/assets/technologies/1",
            headers={"Origin": run.url},
            json={
                "vendor": "Fortinet",
                "product": "FortiOS",
                "software_version": "7.4.3",
                "note": "Wire fixture context change",
                "expected_version": 1,
            },
        )
        if changed.status_code != 200:
            raise RuntimeError(f"technology mutation failed: {changed.status_code}")
        review = request("GET", run.url, STATUS)
        observed["review_required"] = review.status_code
        write(output / "review-required.json", review.json())
        conflict = request(
            "PUT",
            run.url,
            STATUS,
            headers={"Origin": run.url},
            json=save_body(context, 1),
        )
        observed["conflict"] = conflict.status_code
        write(output / "conflict.json", conflict.json())

    with LocalRun("w03-status-known-commit", duration_seconds=30, start_ui=False) as run:
        context = request("GET", run.url, STATUS).json()["context"]
        committed = request(
            "PUT",
            run.url,
            STATUS,
            headers={"Origin": run.url},
            json=save_body(context, 0),
        )
        if committed.status_code != 200:
            raise RuntimeError(f"fault setup failed: {committed.status_code}")
        unavailable = request("GET", run.url, STATUS)
        observed["unavailable"] = unavailable.status_code
        write(output / "unavailable.json", unavailable.json())

    product_256 = "Sản phẩm " + "P" * (256 - len("Sản phẩm "))
    with LocalRun("w03-status-it", duration_seconds=30, start_ui=False) as run:
        changed = request(
            "PUT",
            run.url,
            "/api/assets/technologies/1",
            headers={"Origin": run.url},
            json={
                "vendor": "Fortinet",
                "product": product_256,
                "software_version": "7.4.2",
                "note": "Repro product 256",
                "expected_version": 1,
            },
        )
        if changed.status_code != 200:
            raise RuntimeError(f"product 256 technology setup failed: {changed.status_code}")
        fixture = json.loads(run.cve_fixture_path.read_text(encoding="utf-8"))
        candidate = next(item for item in fixture["candidates"] if item["cve_id"] == "CVE-2026-2001")
        candidate["affected_products"] = [{"vendor": "Fortinet", "product": product_256}]
        write(run.cve_fixture_path, fixture)
        loader_error = None
        try:
            _validate_dataset(FixtureCveReadPort(run.cve_fixture_path).list_candidates())
        except CvesUnavailable as exc:
            loader_error = str(exc)
        if loader_error is None:
            raise RuntimeError("product 256 unexpectedly passed CVE dataset validation")
        product_status = request("GET", run.url, STATUS)
        if product_status.status_code != 503:
            raise RuntimeError(f"product 256 status repro changed: {product_status.status_code}")
        observed["product_256_repro"] = product_status.status_code
        write(
            output / "product-256-repro.json",
            {
                "product_length": len(product_256),
                "technology_update": {"status": changed.status_code, "body": changed.json()},
                "loader_error": loader_error,
                "status_read": {"status": product_status.status_code, "body": product_status.json()},
            },
        )

    actor = "a" * 512
    vendor = "Nhà cung cấp " + "V" * (128 - len("Nhà cung cấp "))
    product = "Sản phẩm " + "P" * (128 - len("Sản phẩm "))
    software_version = "Phiên bản " + "S" * (128 - len("Phiên bản "))
    boundary_note = "Đã xác minh trạng thái " + "N" * (1000 - len("Đã xác minh trạng thái "))
    with LocalRun(
        "w03-status-it",
        duration_seconds=120,
        start_ui=False,
        subject_override=actor,
    ) as run:
        changed = request(
            "PUT",
            run.url,
            "/api/assets/technologies/1",
            headers={"Origin": run.url},
            json={
                "vendor": vendor,
                "product": product,
                "software_version": software_version,
                "note": "Wire boundary context",
                "expected_version": 1,
            },
        )
        if changed.status_code != 200:
            raise RuntimeError(f"boundary technology mutation failed: {changed.status_code}")
        fixture = json.loads(run.cve_fixture_path.read_text(encoding="utf-8"))
        candidate = next(item for item in fixture["candidates"] if item["cve_id"] == "CVE-2026-2001")
        candidate["affected_products"] = [{"vendor": vendor, "product": product}]
        write(run.cve_fixture_path, fixture)

        context_response = request("GET", run.url, STATUS)
        if context_response.status_code != 200:
            raise RuntimeError(
                f"boundary context failed: {context_response.status_code} {context_response.text}"
            )
        context = context_response.json()["context"]
        for version in range(101):
            saved = request(
                "PUT",
                run.url,
                STATUS,
                headers={"Origin": run.url},
                json={
                    **save_body(context, version, note=boundary_note),
                    "status": "patching" if version % 2 == 0 else "patched",
                },
            )
            if saved.status_code != 200:
                raise RuntimeError(f"boundary status write {version + 1} failed: {saved.status_code}")
        observed["boundary_status"] = saved.status_code
        write(output / "boundary-status.json", saved.json())

        history_100 = request("GET", run.url, HISTORY_100)
        observed["history_100"] = history_100.status_code
        write(output / "history-100.json", history_100.json())
        cursor = history_100.json()["page"]["next_cursor"]
        history_tail = request(
            "GET",
            run.url,
            RELATION + "/status-history",
            params={"limit": 100, "cursor": cursor},
        )
        observed["history_tail"] = history_tail.status_code
        write(output / "history-tail.json", history_tail.json())

    expected = {
        "unset": 200,
        "committed": 200,
        "history": 200,
        "review_required": 200,
        "conflict": 409,
        "unavailable": 503,
        "product_256_repro": 503,
        "boundary_status": 200,
        "history_100": 200,
        "history_tail": 200,
    }
    if observed != expected:
        raise RuntimeError(f"wire status mismatch: {observed!r}")
    write(
        output / "manifest.json",
        {
            "status": "PARTIAL",
            "capture_status": "PASS",
            "responses": observed,
            "boundaries": {
                "actor": len(actor),
                "history_first_items": len(history_100.json()["items"]),
                "history_tail_items": len(history_tail.json()["items"]),
                "note": len(boundary_note),
                "product": len(product),
                "product_requested": len(product_256),
                "product_blocker": "CVE dataset product validation is capped at 128",
                "software_version": len(software_version),
                "vendor": len(vendor),
            },
        },
    )
    print(json.dumps({"fixtures": len(observed), "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
