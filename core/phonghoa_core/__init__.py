"""Thư viện lõi của Phong Hỏa.

Các module:
- ioc: nhận diện loại IOC, refang/defang, chuẩn hóa
- extract: trích IOC từ văn bản bằng regex (baseline để so sánh với LLM)
- scoring: chấm điểm IOC 0–100 kèm lời giải thích
- allowlist: lọc IOC thuộc hạ tầng hợp pháp để tránh chặn nhầm
"""

from phonghoa_core.allowlist import Allowlist
from phonghoa_core.extract import extract_iocs
from phonghoa_core.ioc import Ioc, IocType, defang, normalize, refang
from phonghoa_core.scoring import ScoreInput, ScoreResult, score

__all__ = [
    "Allowlist",
    "Ioc",
    "IocType",
    "ScoreInput",
    "ScoreResult",
    "defang",
    "extract_iocs",
    "normalize",
    "refang",
    "score",
]
