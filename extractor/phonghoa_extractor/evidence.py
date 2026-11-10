"""Tìm IOC trong nguyên văn mà không làm mất vị trí ký tự."""

from __future__ import annotations

import re
from collections.abc import Iterator

from phonghoa_core.ioc import Ioc, IocType, normalize

_DEFANGED_DOT = r"(?:\.|\[\.\]|\(\.\)|\{\.\}|\[dot\]|\(dot\))"
_DOMAIN_OR_IP = re.compile(rf"[\w-]+(?:{_DEFANGED_DOT}[\w-]+)+", re.IGNORECASE)
_EMAIL = re.compile(
    rf"[a-z0-9._%+-]+(?:@|\[@\]|\(@\)|\[at\]|\(at\))[\w-]+(?:{_DEFANGED_DOT}[\w-]+)+",
    re.IGNORECASE,
)
_URL = re.compile(
    r"\b(?:https?|hxxps?)(?::|\[:\])(?://|\[/\]\[/\])[^\s<>\"')]+",
    re.IGNORECASE,
)
_HASH = re.compile(r"(?<![a-z0-9])[0-9a-f]{32,64}(?![a-z0-9])", re.IGNORECASE)


def find_ioc_occurrences(text: str, expected: Ioc) -> list[tuple[int, int]]:
    """Trả vị trí token nguyên văn chuẩn hóa đúng bằng ``expected``."""
    matches: list[tuple[int, int]] = []
    for match in _candidate_matches(text, expected.type):
        try:
            candidate = normalize(match.group(0))
        except ValueError:
            continue
        if candidate == expected:
            matches.append(match.span())
    return matches


def find_evidence_span(source_text: str, evidence: str, expected: Ioc) -> tuple[int, int] | None:
    """Tìm lần xuất hiện nguyên văn của quote có chứa đúng IOC, có biên token."""
    start = source_text.find(evidence)
    while start >= 0:
        if find_ioc_occurrences(evidence, expected):
            return start, start + len(evidence)
        start = source_text.find(evidence, start + 1)
    return None


def quote_for_ioc(source_text: str, expected: Ioc) -> tuple[str, tuple[int, int]] | None:
    """Lấy dòng đầu tiên chứa IOC làm quote nguyên văn."""
    occurrences = find_ioc_occurrences(source_text, expected)
    if not occurrences:
        return None
    token_start, token_end = occurrences[0]
    start = source_text.rfind("\n", 0, token_start) + 1
    end = source_text.find("\n", token_end)
    if end < 0:
        end = len(source_text)
    while start < end and source_text[start] in " \t\r":
        start += 1
    while end > start and source_text[end - 1] in " \t\r":
        end -= 1
    return source_text[start:end], (start, end)


def _candidate_matches(text: str, ioc_type: IocType) -> Iterator[re.Match[str]]:
    if ioc_type is IocType.URL:
        yield from _URL.finditer(text)
    elif ioc_type is IocType.EMAIL:
        yield from _EMAIL.finditer(text)
    elif ioc_type in (IocType.MD5, IocType.SHA1, IocType.SHA256):
        yield from _HASH.finditer(text)
    else:
        yield from _DOMAIN_OR_IP.finditer(text)
