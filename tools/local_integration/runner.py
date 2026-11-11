"""Sở hữu trọn vòng đời stack W05 loopback tổng hợp."""

from __future__ import annotations

# ruff: noqa: E402, I001 -- standalone runner exposes repository packages before imports

import argparse
import base64
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import closing
from dataclasses import dataclass
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
from phonghoa_extractor.ingest_queue import get_ingest_provenance, load_ingest_envelope
from portal_api.app import create_app
from portal_api.auth import AccessJwtVerifier
from tools.local_integration.local_settings import make_local_settings

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
INGEST_BROWSER_SCENARIOS = frozenset(
    {
        "ingest-browser-stix",
        "ingest-browser-self-approve",
        "ingest-browser-save-refresh-503",
        "ingest-browser-decision-refresh-503",
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
    | INGEST_BROWSER_SCENARIOS
)
E2E_SOURCE_BYTES = "Cảnh báo thử nghiệm 😀 ghi nhận evil-one.example và evil-two.example.\n".encode()
E2E_CREATOR_SUBJECT = "e2e-author-sub"


@dataclass(frozen=True)
class IngestSeedResult:
    draft_id: int
    import_result: str
    duplicate_result: str
    input_format: str
    raw_sha256: str
    canonical_text_sha256: str
    envelope_sha256: str
    eligible_indices: tuple[int, ...]
    ioc_values: tuple[str, ...]


def _run_harness_cli(
    command: list[str], *, cwd: Path, timeout: float = 20
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("CLI seed quá thời hạn") from None
    except OSError:
        raise RuntimeError("không khởi chạy được CLI seed") from None
    if result.returncode != 0:
        raise RuntimeError("CLI seed thất bại")
    return result


def _decode_cli_summary(stdout: str, keys: set[str]) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        raise RuntimeError("CLI seed trả kết quả không hợp lệ") from None
    if type(value) is not dict or set(value) != keys:
        raise RuntimeError("CLI seed trả kết quả không hợp lệ")
    return value


def seed_ingest_fixture(
    *,
    input_path: Path,
    envelope_path: Path,
    db_path: Path,
    producer_root: Path,
    producer_python: Path,
    importer_python: Path,
    created_by_subject: str,
) -> IngestSeedResult:
    """Chạy producer/importer thật và chứng minh retry duplicate trên cùng DB."""

    producer_script = producer_root / "extractor" / "ingest" / "run.py"
    importer_script = ROOT / "extractor" / "ingest_queue" / "run.py"
    if not input_path.is_file() or not producer_script.is_file() or not importer_script.is_file():
        raise RuntimeError("đầu vào harness không tồn tại")
    if envelope_path.exists() or db_path.exists():
        raise RuntimeError("đầu ra harness phải chưa tồn tại")

    source_bytes = input_path.read_bytes()
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    produced = _run_harness_cli(
        [
            str(producer_python),
            "-X",
            "utf8",
            "-B",
            str(producer_script),
            "--input",
            str(input_path),
            "--output",
            str(envelope_path),
            "--language",
            "vi",
            "--tlp",
            "TLP:GREEN",
        ],
        cwd=producer_root,
    )
    producer_summary = _decode_cli_summary(produced.stdout, {"schema_version", "format", "output_created"})
    if (
        producer_summary["schema_version"] != "x01-local-ingest/1.0"
        or producer_summary["format"] not in {"text", "pdf"}
        or producer_summary["output_created"] is not True
    ):
        raise RuntimeError("producer CLI trả kết quả không hợp lệ")

    envelope = load_ingest_envelope(envelope_path)
    metadata = envelope["input"]
    draft = envelope["draft"]
    if metadata["raw_sha256"] != source_digest:
        raise RuntimeError("producer raw hash không khớp input")
    with closing(sqlite3.connect(db_path)):
        pass

    importer_command = [
        str(importer_python),
        "-X",
        "utf8",
        "-B",
        str(importer_script),
        "import",
        "--envelope",
        str(envelope_path),
        "--db",
        str(db_path),
        "--created-by-subject",
        created_by_subject,
    ]
    first = _decode_cli_summary(_run_harness_cli(importer_command, cwd=ROOT).stdout, {"draft_id", "result"})
    second = _decode_cli_summary(_run_harness_cli(importer_command, cwd=ROOT).stdout, {"draft_id", "result"})
    if (
        type(first["draft_id"]) is not int
        or first["draft_id"] < 1
        or first["result"] != "imported"
        or second != {"draft_id": first["draft_id"], "result": "duplicate"}
    ):
        raise RuntimeError("importer CLI trả kết quả không hợp lệ")

    provenance = get_ingest_provenance(db_path, first["draft_id"])
    if (
        provenance.raw_sha256 != metadata["raw_sha256"]
        or provenance.canonical_text_sha256 != metadata["canonical_text_sha256"]
        or provenance.input_format != metadata["format"]
        or draft["source"]["sha256"] != metadata["canonical_text_sha256"]
    ):
        raise RuntimeError("provenance sau import không khớp envelope")
    with closing(sqlite3.connect(db_path)) as connection:
        counts = tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("drafts", "draft_ingest_provenance", "draft_selection_audit", "draft_audit")
        )
    if counts != (1, 1, 0, 0) or hashlib.sha256(input_path.read_bytes()).hexdigest() != source_digest:
        raise RuntimeError("import hoặc retry làm thay đổi dữ liệu ngoài contract")

    eligible = tuple(
        index
        for index, item in enumerate(draft["items"])
        if item["kind"] == "ioc" and item["keep"] is True and item["status"] == "ok"
    )
    return IngestSeedResult(
        draft_id=first["draft_id"],
        import_result=first["result"],
        duplicate_result=second["result"],
        input_format=metadata["format"],
        raw_sha256=metadata["raw_sha256"],
        canonical_text_sha256=metadata["canonical_text_sha256"],
        envelope_sha256=provenance.envelope_sha256,
        eligible_indices=eligible,
        ioc_values=tuple(draft["items"][index]["value"] for index in eligible),
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
        producer_root: Path | None = None,
        producer_python: Path | None = None,
        ingest_input: Path | None = None,
        created_by_subject: str | None = None,
    ):
        if scenario not in SCENARIOS:
            raise ValueError("scenario không được phép")
        if isinstance(duration_seconds, bool) or not 1 <= duration_seconds <= 300:
            raise ValueError("duration phải từ 1 đến 300 giây")
        ingest_values = (producer_root, producer_python, ingest_input, created_by_subject)
        if scenario in INGEST_BROWSER_SCENARIOS and any(value is None for value in ingest_values):
            raise ValueError("scenario ingest-browser cần đủ producer/input/creator")
        if scenario not in INGEST_BROWSER_SCENARIOS and any(value is not None for value in ingest_values):
            raise ValueError("producer/input/creator chỉ dành cho scenario ingest-browser")
        self.scenario = scenario
        self.actor_subject = (
            created_by_subject
            if scenario == "ingest-browser-self-approve"
            else "analyst-sub"
            if scenario == "analyst-self"
            else "it-sub"
            if scenario == "insufficient-role"
            else "admin-sub"
        )
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
        self.producer_root = producer_root
        self.producer_python = producer_python
        self.ingest_input = ingest_input
        self.created_by_subject = created_by_subject
        self.ingest_seed: IngestSeedResult | None = None
        self.draft_ids: tuple[int, ...] = ()
        self.selection_draft_id: int | None = None
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
        claims: dict[str, Any] = {
            "sub": self.actor_subject,
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
        if self.scenario in INGEST_BROWSER_SCENARIOS:
            self._save_ingest_browser_fixture()
            return
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

    def _save_ingest_browser_fixture(self) -> None:
        if (
            self.producer_root is None
            or self.producer_python is None
            or self.ingest_input is None
            or self.created_by_subject is None
        ):
            raise RuntimeError("cấu hình ingest-browser bị thiếu")
        self.source_path = self.temp_root / self.ingest_input.name
        shutil.copyfile(self.ingest_input, self.source_path)
        config_source = ROOT / "extractor" / "draft" / "examples" / "stix" / "exporter-config.example.json"
        self.exporter_config_path.write_bytes(config_source.read_bytes())
        self.ingest_seed = seed_ingest_fixture(
            input_path=self.source_path,
            envelope_path=self.draft_json_path,
            db_path=self.db_path,
            producer_root=self.producer_root,
            producer_python=self.producer_python,
            importer_python=Path(sys.executable),
            created_by_subject=self.created_by_subject,
        )
        self.selection_draft_id = self.ingest_seed.draft_id
        self.draft_ids = (self.ingest_seed.draft_id,)
        if self.scenario == "ingest-browser-decision-refresh-503":
            store.save_selection(
                self.db_path,
                self.ingest_seed.draft_id,
                actor=store.Actor(self.actor_subject, frozenset({"admin"})),
                selected_indices=[1],
                expected_version=0,
            )

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
                "e2e-author-sub": frozenset({"analyst"}),
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
            if self.scenario in {
                "post-ok-refresh-503",
                "selection-save-refresh-503",
                "selection-decision-refresh-503",
                "ingest-browser-save-refresh-503",
                "ingest-browser-decision-refresh-503",
            }:
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
