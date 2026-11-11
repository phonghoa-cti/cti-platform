"""Child PDF riêng cho local ingest; không phải public API."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _write_result(path: Path, payload: dict[str, object], cap: int) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")
    if len(encoded) > cap:
        encoded = b"x" * (cap + 1)
    with path.open("xb") as handle:
        handle.write(encoded)
        handle.flush()


def _extract_pages(
    source: Path,
    max_pages: int,
    max_page_codepoints: int,
    max_total_codepoints: int,
) -> dict[str, object]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(source)
        if reader.is_encrypted:
            return {"code": "pdf_encrypted", "ok": False}
        if len(reader.pages) == 0:
            return {"code": "pdf_malformed", "ok": False}
        if len(reader.pages) > max_pages:
            return {"code": "pdf_page_limit", "ok": False}
        return _read_page_text(reader.pages, max_page_codepoints, max_total_codepoints)
    except Exception:
        return {"code": "pdf_malformed", "ok": False}


def _read_page_text(pages, max_page_codepoints: int, max_total_codepoints: int) -> dict[str, object]:
    texts: list[str] = []
    total = 0
    for index, page in enumerate(pages):
        text = page.extract_text()
        if type(text) is not str:
            return {"code": "pdf_malformed", "ok": False}
        try:
            text.encode("utf-8", "strict")
        except UnicodeError:
            return {"code": "pdf_malformed", "ok": False}
        if len(text) > max_page_codepoints:
            return {"code": "pdf_page_text_limit", "ok": False}
        total += len(text) + (3 if index else 0)
        if total > max_total_codepoints:
            return {"code": "pdf_total_text_limit", "ok": False}
        texts.append(text)
    if not any(text.strip() for text in texts):
        return {"code": "pdf_no_extractable_text", "ok": False}
    return {"ok": True, "pages": texts}


def main() -> int:
    if len(sys.argv) != 7:
        return 2
    source, result = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        limits = [int(value) for value in sys.argv[3:]]
        payload = _extract_pages(source, limits[0], limits[1], limits[2])
        _write_result(result, payload, limits[3])
    except (OSError, ValueError, TypeError):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
