"""Tạo bản nháp IOC pending từ một file .txt cục bộ."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for source_dir in (REPO_ROOT / "core", REPO_ROOT / "extractor"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))

from phonghoa_extractor.drafts import build_regex_draft  # noqa: E402

TLP_CHOICES = ("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="file .txt UTF-8")
    parser.add_argument("--output", required=True, type=Path, help="file JSON sẽ tạo")
    parser.add_argument("--language", required=True, choices=("vi", "en"))
    parser.add_argument("--tlp", default="TLP:AMBER", choices=TLP_CHOICES)
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = _parse_args()
    if args.input.suffix.lower() != ".txt":
        print("Lỗi: --input phải là file .txt", file=sys.stderr)
        return 2
    try:
        text = args.input.read_text(encoding="utf-8")
        draft = build_regex_draft(text, source=args.input.name, language=args.language, tlp=args.tlp)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(draft, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    print(f"Đã tạo bản nháp pending: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
