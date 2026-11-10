"""Chạy adapter C2/C3 với phản hồi giả lập, hoàn toàn ngoại tuyến."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor.llm_adapter import (  # noqa: E402
    MAX_RESPONSE_BYTES,
    AdapterError,
    ProviderResponse,
    ScriptedProvider,
    run_extraction,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, choices=("C2", "C3"))
    parser.add_argument("--input", required=True, type=Path, help="báo cáo .txt UTF-8")
    parser.add_argument("--response", required=True, type=Path, help="fixture response JSON")
    parser.add_argument("--language", required=True, choices=("vi", "en"))
    parser.add_argument(
        "--tlp",
        required=True,
        choices=("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"),
    )
    parser.add_argument("--output", required=True, type=Path, help="artifact JSON sẽ tạo")
    return parser.parse_args()


def _ensure_distinct(paths: list[Path]) -> None:
    output = paths[-1]
    output_resolved = os.path.normcase(str(output.resolve()))
    for source in paths[:-1]:
        if os.path.normcase(str(source.resolve())) == output_resolved:
            raise AdapterError("unsafe_output_path")
        if source.exists() and output.exists() and source.samefile(output):
            raise AdapterError("unsafe_output_path")


def _provider_from_fixture(value: object) -> ScriptedProvider:
    if not isinstance(value, dict) or set(value) != {"provider", "responses"}:
        raise AdapterError("invalid_fixture")
    metadata, responses = value["provider"], value["responses"]
    if not isinstance(metadata, dict) or set(metadata) != {"name", "destination", "egress"}:
        raise AdapterError("invalid_fixture")
    if not isinstance(responses, list) or not responses:
        raise AdapterError("invalid_fixture")
    return ScriptedProvider(
        [_response_from_value(item) for item in responses],
        name=metadata["name"],
        destination=metadata["destination"],
        egress=metadata["egress"],
    )


def _response_from_value(value: object) -> ProviderResponse:
    allowed = {"status", "payload", "model_id", "usage", "retryable", "error_code"}
    if not isinstance(value, dict) or "status" not in value or not set(value) <= allowed:
        raise AdapterError("invalid_fixture")
    return ProviderResponse(
        status=value["status"],
        payload=value.get("payload"),
        model_id=value.get("model_id", ""),
        usage=value.get("usage"),
        retryable=value.get("retryable", False),
        error_code=value.get("error_code"),
    )


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temp_name = handle.name
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    try:
        _ensure_distinct([args.input, args.response, args.output])
        if args.response.stat().st_size > MAX_RESPONSE_BYTES:
            raise AdapterError("invalid_fixture")
        text = args.input.read_text(encoding="utf-8")
        fixture = json.loads(args.response.read_text(encoding="utf-8"))
        provider = _provider_from_fixture(fixture)
        result = run_extraction(
            text=text,
            language=args.language,
            tlp=args.tlp,
            config=args.config,
            provider=provider,
        )
        _write_json_atomic(args.output, result)
    except (OSError, UnicodeError, json.JSONDecodeError, AdapterError):
        print("Lỗi: offline_adapter_failed", file=sys.stderr)
        return 1
    count = len(result.get("raw_iocs", result.get("iocs", [])))
    print(
        json.dumps(
            {
                "config": args.config,
                "count": count,
                "mode": result["result_mode"],
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
