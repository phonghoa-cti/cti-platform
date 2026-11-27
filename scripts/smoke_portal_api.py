"""Smoke: khởi động portal_api thật (uvicorn, loopback) trên fixture W03 tổng hợp, gọi GET /api/cves.

Không cần Node/gateway; JWT ký bằng khóa RSA tạm sinh trong tiến trình. In "PASS ..." hoặc "FAIL ...".
"""

from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "core"), str(ROOT / "extractor")]

import httpx  # noqa: E402
import uvicorn  # noqa: E402

from phonghoa_extractor import store  # noqa: E402
from portal_api.app import create_app  # noqa: E402
from tools.local_integration.local_settings import make_local_settings  # noqa: E402
from tools.local_integration.runner import LocalRun, _free_port, _wait_port  # noqa: E402
from tools.local_integration.w03_fixture import build_w03_fixture  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="smoke-portal-") as tmp:
        root = Path(tmp)
        db_path = root / "drafts.sqlite"
        port = _free_port()
        settings = make_local_settings(db_path, root, port, {"it-sub": frozenset({"it"})})
        # Chỉ mượn phần sinh JWT + verifier của harness; không start gateway/UI.
        token, verifier = LocalRun("w03-it", 60, start_ui=False)._token_and_verifier(settings)
        asset_store, technology_store, lookup_port, cve_port = build_w03_fixture(db_path)
        app = create_app(
            settings,
            store,
            verifier=verifier,
            lookup_port=lookup_port,
            asset_store=asset_store,
            technology_store=technology_store,
            cve_port=cve_port,
        )
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            _wait_port(port, timeout=10)
            response = httpx.get(
                f"http://127.0.0.1:{port}/api/cves",
                headers={"Cf-Access-Jwt-Assertion": token},
                timeout=10,
                trust_env=False,
            )
        finally:
            server.should_exit = True
            deadline = time.monotonic() + 5
            while thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.1)
    if response.status_code == 200:
        print(f"PASS portal_api /api/cves HTTP 200 ({len(response.content)} byte)")
        return 0
    print(f"FAIL portal_api /api/cves HTTP {response.status_code}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
