"""Sở hữu trọn vòng đời stack W05 loopback tổng hợp."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- standalone runner exposes repository packages before imports

import argparse
import base64
import gc
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXTRACTOR_ROOT = ROOT / "extractor"
for source_root in (ROOT / "core", EXTRACTOR_ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

import jwt
import uvicorn
from cryptography.hazmat.primitives.asymmetric import rsa

from phonghoa_extractor import store
from phonghoa_extractor.drafts import build_regex_draft
from portal_api.app import create_app
from portal_api.assets import AssetStore
from portal_api.auth import AccessJwtVerifier
from tools.local_integration.local_settings import make_local_settings
from tools.local_integration.w02_fixture import build_w02_fixture
from tools.local_integration.w04_fixture import build_w04_fixture

SELECTION_SCENARIOS = frozenset(
    {
        "selection-admin",
        "selection-empty",
        "selection-reject",
        "selection-save-refresh-503",
        "selection-decision-refresh-503",
    }
)
STIX_E2E_SCENARIOS = frozenset({"stix-e2e"})
W02_SCENARIOS = frozenset(
    {
        "w02-it",
        "w02-it-hidden-mutated",
        "w02-analyst",
        "w02-multi-role",
        "w02-missing-token",
        "w02-forbidden",
        "w02-lookup-503",
    }
)
W04_SCENARIOS = frozenset(
    {
        "w04-it",
        "w04-analyst",
        "w04-multi-role",
        "w04-missing-token",
        "w04-forbidden",
        "w04-refresh-503",
    }
)
SCENARIOS = (
    frozenset(
        {
            "admin-other",
            "analyst-self",
            "insufficient-role",
            "missing-token",
            "expired",
            "wrong-signature",
            "post-ok-refresh-503",
        }
    )
    | SELECTION_SCENARIOS
    | STIX_E2E_SCENARIOS
    | W02_SCENARIOS
    | W04_SCENARIOS
)
E2E_SOURCE_BYTES = "Cảnh báo thử nghiệm 😀 ghi nhận evil-one.example và evil-two.example.\n".encode()
E2E_CREATOR_SUBJECT = "e2e-author-sub"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _require_available_port(port: int) -> None:
    try:
        with socket.socket() as probe:
            if os.name == "nt":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", port))
    except OSError as exc:
        raise RuntimeError("gateway port đã được process khác sử dụng") from exc


def _wait_port(port: int, process: subprocess.Popen[bytes] | None = None, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError("child process dừng trước readiness")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                if process is not None:
                    time.sleep(0.05)
                    if process.poll() is not None:
                        raise RuntimeError("child process dừng sau khi port đích đã có listener khác")
                return
        except OSError:
            time.sleep(0.03)
    raise RuntimeError("listener không ready trước deadline")


def _b64uint(value: int) -> str:
    size = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(size, "big")).rstrip(b"=").decode("ascii")


class LocalJwksClient:
    def __init__(self, jwk: dict[str, str]):
        self._jwk = jwk

    def get_signing_key_from_jwt(self, token: str):
        header = jwt.get_unverified_header(token)
        if header.get("kid") != self._jwk["kid"]:
            raise jwt.PyJWKClientError("unknown synthetic kid")
        return jwt.PyJWK.from_dict(self._jwk)


class LocalRun:
    """Context manager chỉ đóng listener/process/temp root do chính run tạo."""

    def __init__(
        self,
        scenario: str,
        duration_seconds: int = 300,
        *,
        start_ui: bool = True,
        gateway_port: int | None = None,
    ):
        if scenario not in SCENARIOS:
            raise ValueError("scenario không được phép")
        if isinstance(duration_seconds, bool) or not 1 <= duration_seconds <= 300:
            raise ValueError("duration phải từ 1 đến 300 giây")
        self.scenario = scenario
        self.duration_seconds = duration_seconds
        self.start_ui = start_ui
        self.gateway_port = gateway_port or _free_port()
        self.api_port = _free_port()
        self.ui_port = _free_port()
        self.url = f"http://127.0.0.1:{self.gateway_port}"
        self.temp_root = Path(tempfile.gettempdir()) / "w05-not-started"
        self.db_path = self.temp_root / "drafts.sqlite"
        self.source_path = self.temp_root / "stix-e2e-input.txt"
        self.draft_json_path = self.temp_root / "stix-e2e-draft.json"
        self.exporter_config_path = self.temp_root / "exporter-config.json"
        self.bundle_path = self.temp_root / "approved-bundle.json"
        self.draft_ids: tuple[int, ...] = ()
        self.selection_draft_id: int | None = None
        self.asset_store: AssetStore | None = None
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self._api_server: uvicorn.Server | None = None
        self._api_thread: threading.Thread | None = None
        self._ui_process: subprocess.Popen[bytes] | None = None
        self._gateway_process: subprocess.Popen[bytes] | None = None
        self._timer: threading.Timer | None = None
        self._closed = False
        self._lifecycle = "new"
        self._lock = threading.Lock()

    def _token_and_verifier(self, settings):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = private_key.public_key().public_numbers()
        jwk = {
            "kty": "RSA",
            "kid": "w05-local",
            "use": "sig",
            "alg": "RS256",
            "n": _b64uint(public.n),
            "e": _b64uint(public.e),
        }
        now = datetime.now(UTC)
        if self.scenario in {"analyst-self", "w02-analyst", "w04-analyst"}:
            subject = "analyst-sub"
        elif self.scenario in {"insufficient-role", "w02-it", "w02-it-hidden-mutated", "w04-it"}:
            subject = "it-sub"
        elif self.scenario in {"w02-multi-role", "w04-multi-role"}:
            subject = "multi-sub"
        elif self.scenario == "w02-forbidden":
            subject = "viewer-sub"
        elif self.scenario == "w04-forbidden":
            subject = "leader-sub"
        else:
            subject = "admin-sub"
        claims: dict[str, Any] = {
            "sub": subject,
            "iss": settings.access_issuer,
            "aud": settings.access_audience,
            "iat": now,
            "nbf": now - timedelta(seconds=1),
            "exp": now + timedelta(seconds=self.duration_seconds),
        }
        if self.scenario == "expired":
            claims["exp"] = now - timedelta(seconds=1)
        signing_key = (
            rsa.generate_private_key(public_exponent=65537, key_size=2048)
            if self.scenario == "wrong-signature"
            else private_key
        )
        token = (
            None
            if self.scenario in {"missing-token", "w02-missing-token", "w04-missing-token"}
            else jwt.encode(claims, signing_key, algorithm="RS256", headers={"kid": "w05-local"})
        )
        return token, AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))

    def _save_fixtures(self) -> None:
        if self.scenario in STIX_E2E_SCENARIOS:
            self._save_stix_e2e_fixture()
            return
        creators = ("author-sub", "author-sub", "analyst-sub", "other-author")
        ids = []
        for index, creator in enumerate(creators, start=1):
            draft = build_regex_draft(
                f"Synthetic local report {index} evil{index}.example",
                source=f"local-{index}.txt",
                language="vi",
            )
            ids.append(store.save_draft(self.db_path, draft, created_by_subject=creator))
        if self.scenario in SELECTION_SCENARIOS:
            selection_draft = build_regex_draft(
                "Synthetic selection report evil-one.example and evil-two.example",
                source="selection-local-synthetic.txt",
                language="vi",
            )
            self.selection_draft_id = store.save_draft(
                self.db_path, selection_draft, created_by_subject="selection-author-sub"
            )
            ids.append(self.selection_draft_id)
            if self.scenario == "selection-decision-refresh-503":
                store.save_selection(
                    self.db_path,
                    self.selection_draft_id,
                    actor=store.Actor("admin-sub", frozenset({"admin"})),
                    selected_indices=[1],
                    expected_version=0,
                )
        self.draft_ids = tuple(ids)

    def _run_seed_cli(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=10,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("seed CLI quá thời hạn") from None
        except OSError:
            raise RuntimeError("không khởi chạy được seed CLI") from None
        if result.returncode != 0:
            raise RuntimeError("seed CLI thất bại")
        return result

    def _save_stix_e2e_fixture(self) -> None:
        self.source_path.write_bytes(E2E_SOURCE_BYTES)
        config_source = ROOT / "extractor" / "draft" / "examples" / "stix" / "exporter-config.example.json"
        self.exporter_config_path.write_bytes(config_source.read_bytes())
        self._run_seed_cli(
            [
                sys.executable,
                "-X",
                "utf8",
                "-B",
                str(ROOT / "extractor" / "draft" / "run.py"),
                "--input",
                str(self.source_path),
                "--output",
                str(self.draft_json_path),
                "--language",
                "vi",
                "--tlp",
                "TLP:GREEN",
            ]
        )
        saved = self._run_seed_cli(
            [
                sys.executable,
                "-X",
                "utf8",
                "-B",
                str(ROOT / "extractor" / "draft" / "store.py"),
                "save",
                "--db",
                str(self.db_path),
                "--input",
                str(self.draft_json_path),
                "--created-by-subject",
                E2E_CREATOR_SUBJECT,
            ]
        )
        try:
            value = json.loads(saved.stdout)
        except (TypeError, json.JSONDecodeError):
            raise RuntimeError("store CLI trả kết quả không hợp lệ") from None
        if (
            not isinstance(value, dict)
            or set(value) != {"id", "status"}
            or isinstance(value["id"], bool)
            or not isinstance(value["id"], int)
            or value["id"] < 1
            or value["status"] != "pending"
        ):
            raise RuntimeError("store CLI trả kết quả không hợp lệ")
        self.selection_draft_id = value["id"]
        self.draft_ids = (value["id"],)

    def start(self) -> LocalRun:
        with self._lock:
            if self._lifecycle != "new":
                raise RuntimeError("mỗi LocalRun chỉ được start một lần")
            self._lifecycle = "starting"
        try:
            _require_available_port(self.gateway_port)
            self._temporary = tempfile.TemporaryDirectory(prefix="w05-local-")
            self.temp_root = Path(self._temporary.name)
            self.db_path = self.temp_root / "drafts.sqlite"
            self.source_path = self.temp_root / "stix-e2e-input.txt"
            self.draft_json_path = self.temp_root / "stix-e2e-draft.json"
            self.exporter_config_path = self.temp_root / "exporter-config.json"
            self.bundle_path = self.temp_root / "approved-bundle.json"
            roles = {
                "admin-sub": frozenset({"admin"}),
                "analyst-sub": frozenset({"analyst"}),
                "it-sub": frozenset({"it"}),
                "author-sub": frozenset({"analyst"}),
                "multi-sub": frozenset({"it", "analyst"}),
                "viewer-sub": frozenset({"viewer"}),
                "leader-sub": frozenset({"leader"}),
            }
            settings = make_local_settings(self.db_path, self.temp_root, self.gateway_port, roles)
            self._save_fixtures()
            token, verifier = self._token_and_verifier(settings)
            lookup_port = None
            asset_store = None
            if self.scenario in W02_SCENARIOS:
                lookup_port = build_w02_fixture(
                    fail=self.scenario == "w02-lookup-503",
                    mutate_hidden=self.scenario == "w02-it-hidden-mutated",
                )
            elif self.scenario in W04_SCENARIOS:
                asset_store, lookup_port = build_w04_fixture(self.db_path)
                self.asset_store = asset_store
            app = create_app(
                settings,
                store,
                verifier=verifier,
                lookup_port=lookup_port,
                asset_store=asset_store,
            )
            self._api_server = uvicorn.Server(
                uvicorn.Config(app, host="127.0.0.1", port=self.api_port, log_level="warning", lifespan="off")
            )
            self._api_thread = threading.Thread(target=self._api_server.run, name="w05-uvicorn", daemon=True)
            self._api_thread.start()
            _wait_port(self.api_port)
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            if self.start_ui:
                web = Path(__file__).resolve().parents[2] / "portal" / "web"
                command = [
                    "node",
                    str(web / "node_modules" / "next" / "dist" / "bin" / "next"),
                    "start",
                    "-H",
                    "127.0.0.1",
                    "-p",
                    str(self.ui_port),
                ]
                self._ui_process = subprocess.Popen(
                    command,
                    cwd=web,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags,
                )
                _wait_port(self.ui_port, self._ui_process, 8)
            gateway = Path(__file__).with_name("gateway.mjs")
            env = os.environ.copy()
            env.update(
                {
                    "W05_API_PORT": str(self.api_port),
                    "W05_UI_PORT": str(self.ui_port),
                    "W05_GATEWAY_PORT": str(self.gateway_port),
                    "W05_REQUEST_TIMEOUT_MS": "1000",
                }
            )
            if token is not None:
                env["W05_GATEWAY_JWT"] = token
            if self.scenario in {
                "post-ok-refresh-503",
                "selection-save-refresh-503",
                "selection-decision-refresh-503",
            }:
                env["W05_FAIL_REFRESH"] = "1"
            if self.scenario == "w04-refresh-503":
                env["W04_FAIL_ASSET_REFRESH_ONCE"] = "1"
            self._gateway_process = subprocess.Popen(
                ["node", str(gateway)],
                cwd=gateway.parent,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            _wait_port(self.gateway_port, self._gateway_process)
            self._timer = threading.Timer(self.duration_seconds, self.close)
            self._timer.daemon = True
            self._timer.start()
            with self._lock:
                self._lifecycle = "running"
            return self
        except Exception as start_error:
            with self._lock:
                self._lifecycle = "failed"
            try:
                self.close()
            except ExceptionGroup as cleanup_error:
                raise ExceptionGroup(
                    "khởi động và cleanup local integration đều thất bại", [start_error, cleanup_error]
                ) from None
            raise

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._lifecycle = "cleanup"
            errors: list[Exception] = []
            if self._timer is not None:
                try:
                    self._timer.cancel()
                    self._timer = None
                except Exception as exc:
                    errors.append(RuntimeError("không hủy được TTL timer"))
                    errors[-1].__cause__ = exc
            for attribute, label in (("_gateway_process", "gateway"), ("_ui_process", "UI")):
                process = getattr(self, attribute)
                if process is None:
                    continue
                try:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=2)
                    setattr(self, attribute, None)
                except Exception as exc:
                    error = RuntimeError(f"không dừng được process {label} do run sở hữu")
                    error.__cause__ = exc
                    errors.append(error)

            api_stopped = self._api_thread is None
            if self._api_server is not None:
                try:
                    self._api_server.should_exit = True
                except Exception as exc:
                    error = RuntimeError("không gửi được tín hiệu dừng API")
                    error.__cause__ = exc
                    errors.append(error)
            if self._api_thread is not None:
                try:
                    self._api_thread.join(timeout=3)
                    if self._api_thread.is_alive():
                        raise RuntimeError("API thread còn chạy sau deadline")
                    self._api_thread = None
                    self._api_server = None
                    api_stopped = True
                except Exception as exc:
                    error = RuntimeError("không xác nhận được API đã dừng")
                    error.__cause__ = exc
                    errors.append(error)

            if api_stopped and self._temporary is not None:
                try:
                    if self.asset_store is not None:
                        self.asset_store = None
                        gc.collect()
                    self._temporary.cleanup()
                    self._temporary = None
                except Exception as exc:
                    error = RuntimeError("không xóa được temp root do run sở hữu")
                    error.__cause__ = exc
                    errors.append(error)

            self._closed = all(
                resource is None
                for resource in (
                    self._timer,
                    self._gateway_process,
                    self._ui_process,
                    self._api_thread,
                    self._temporary,
                )
            )
            self._lifecycle = "closed" if self._closed else "cleanup-pending"
            if errors:
                raise ExceptionGroup("cleanup local integration chưa hoàn tất", errors)

    def __enter__(self) -> LocalRun:
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    parser.add_argument("--duration-seconds", type=int, default=300)
    args = parser.parse_args()
    with LocalRun(args.scenario, args.duration_seconds) as run:
        print(f"W05 local URL: {run.url}; scenario={run.scenario}", flush=True)
        deadline = time.monotonic() + args.duration_seconds
        try:
            while time.monotonic() < deadline:
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
