"""Sở hữu trọn vòng đời stack W05 loopback tổng hợp."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- standalone runner exposes repository packages before imports

import argparse
import base64
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
from portal_api.auth import AccessJwtVerifier
from tools.local_integration.local_settings import make_local_settings

SCENARIOS = frozenset(
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
        self.draft_ids: tuple[int, ...] = ()
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self._api_server: uvicorn.Server | None = None
        self._api_thread: threading.Thread | None = None
        self._ui_process: subprocess.Popen[bytes] | None = None
        self._gateway_process: subprocess.Popen[bytes] | None = None
        self._timer: threading.Timer | None = None
        self._closed = False
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
        subject = (
            "analyst-sub"
            if self.scenario == "analyst-self"
            else "it-sub"
            if self.scenario == "insufficient-role"
            else "admin-sub"
        )
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
            if self.scenario == "missing-token"
            else jwt.encode(claims, signing_key, algorithm="RS256", headers={"kid": "w05-local"})
        )
        return token, AccessJwtVerifier(settings, jwks_client=LocalJwksClient(jwk))

    def _save_fixtures(self) -> None:
        creators = ("author-sub", "author-sub", "analyst-sub", "other-author")
        ids = []
        for index, creator in enumerate(creators, start=1):
            draft = build_regex_draft(
                f"Synthetic local report {index} evil{index}.example",
                source=f"local-{index}.txt",
                language="vi",
            )
            ids.append(store.save_draft(self.db_path, draft, created_by_subject=creator))
        self.draft_ids = tuple(ids)

    def start(self) -> LocalRun:
        if self._temporary is not None:
            raise RuntimeError("run đã start")
        try:
            _require_available_port(self.gateway_port)
            self._temporary = tempfile.TemporaryDirectory(prefix="w05-local-")
            self.temp_root = Path(self._temporary.name)
            self.db_path = self.temp_root / "drafts.sqlite"
            roles = {
                "admin-sub": frozenset({"admin"}),
                "analyst-sub": frozenset({"analyst"}),
                "it-sub": frozenset({"it"}),
                "author-sub": frozenset({"analyst"}),
            }
            settings = make_local_settings(self.db_path, self.temp_root, self.gateway_port, roles)
            self._save_fixtures()
            token, verifier = self._token_and_verifier(settings)
            app = create_app(settings, store, verifier=verifier)
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
            if self.scenario == "post-ok-refresh-503":
                env["W05_FAIL_REFRESH"] = "1"
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
            return self
        except Exception as start_error:
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
