from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from phonghoa_extractor.attack_catalog import (
    _MAX_BYTES,
    _TECHNIQUE_ID,
    AttackCatalog,
    AttackCatalogError,
    SnapshotPin,
    TechniqueRecord,
    _stix_id,
    _timestamp,
    _validate_pin,
)


@dataclass(frozen=True)
class RetrievedTechnique:
    external_id: str
    name: str
    description: str | None
    modified: str
    parent_external_ids: tuple[str, ...]
    ranking_score: float
    snapshot_version: str
    snapshot_sha256: str
    pin_kind: Literal["synthetic", "official"]
    source_url: str | None
    release_tag: str | None
    commit: str | None
    semantic_status: Literal["unverified"] = "unverified"
    operational_draft_eligible: Literal[False] = False


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    top_k: int
    context_budget_bytes: int
    context: str
    snapshot_version: str
    snapshot_sha256: str
    results: tuple[RetrievedTechnique, ...]


class AttackRetrievalError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return self.code


_MAPPING_PROXY_TYPE = type(MappingProxyType({}))


def _fail(code: str) -> None:
    raise AttackRetrievalError(code)


def _encoded(value: str, code: str) -> bytes:
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError:
        _fail(code)


def _tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return tuple(
        token for token in re.findall(r"[^\W_]+", normalized, flags=re.UNICODE) if 2 <= len(token) <= 64
    )


def _validate_query(query: object) -> tuple[str, frozenset[str]]:
    if type(query) is not str or not query or len(query) > 512:
        _fail("invalid_query")
    encoded = _encoded(query, "invalid_query")
    if len(encoded) > 4096 or not query.strip():
        _fail("invalid_query")
    tokens = frozenset(_tokens(query))
    if not tokens:
        _fail("invalid_query")
    return query, tokens


def _validate_bounds(top_k: object, context_budget_bytes: object) -> tuple[int, int]:
    if type(top_k) is not int or not 1 <= top_k <= 10:
        _fail("invalid_bounds")
    if type(context_budget_bytes) is not int or not 256 <= context_budget_bytes <= 8192:
        _fail("invalid_bounds")
    return top_k, context_budget_bytes


def _validate_catalog(catalog: object) -> AttackCatalog:
    if type(catalog) is not AttackCatalog or type(catalog.pin) is not SnapshotPin:
        _fail("invalid_catalog")
    if type(catalog.records_by_external_id) not in (dict, _MAPPING_PROXY_TYPE):
        _fail("invalid_catalog")
    try:
        _validate_pin(catalog.pin, _MAX_BYTES)
    except AttackCatalogError:
        _fail("invalid_catalog")
    for external_id, record in catalog.records_by_external_id.items():
        _validate_record(external_id, record)
    return catalog


def _validate_record(key: object, record: object) -> None:
    if type(key) is not str or _TECHNIQUE_ID.fullmatch(key) is None:
        _fail("invalid_record")
    if type(record) is not TechniqueRecord or key != record.external_id:
        _fail("invalid_record")
    try:
        _stix_id(record.stix_id, "attack-pattern", "invalid_record")
        _timestamp(record.modified, "invalid_record")
    except AttackCatalogError:
        _fail("invalid_record")
    if (
        type(record.name) is not str
        or not record.name
        or len(record.name) > 256
        or type(record.revoked) is not bool
        or type(record.deprecated) is not bool
        or type(record.is_subtechnique) is not bool
        or type(record.parent_external_ids) is not tuple
        or ("." in record.external_id) != record.is_subtechnique
    ):
        _fail("invalid_record")
    _encoded(record.name, "invalid_record")
    for parent_id in record.parent_external_ids:
        if type(parent_id) is not str or _TECHNIQUE_ID.fullmatch(parent_id) is None:
            _fail("invalid_record")
    if record.description is not None:
        if type(record.description) is not str:
            _fail("invalid_record")
        if len(_encoded(record.description, "invalid_record")) > 32 * 1024:
            _fail("invalid_record")


def _retrieved(record: TechniqueRecord, score: float, pin: SnapshotPin) -> RetrievedTechnique:
    return RetrievedTechnique(
        external_id=record.external_id,
        name=record.name,
        description=record.description,
        modified=record.modified,
        parent_external_ids=tuple(record.parent_external_ids),
        ranking_score=score,
        snapshot_version=pin.version,
        snapshot_sha256=pin.sha256,
        pin_kind=pin.kind,
        source_url=pin.source_url,
        release_tag=pin.release_tag,
        commit=pin.commit,
    )


def _snapshot(pin: SnapshotPin) -> dict[str, object]:
    return {
        "version": pin.version,
        "sha256": pin.sha256,
        "kind": pin.kind,
        "source_url": pin.source_url,
        "release_tag": pin.release_tag,
        "commit": pin.commit,
    }


def _item(result: RetrievedTechnique, snippet: str, truncated: bool) -> dict[str, object]:
    return {
        "id": result.external_id,
        "name": result.name,
        "snippet": snippet,
        "snippet_truncated": truncated,
        "modified": result.modified,
        "parents": list(result.parent_external_ids),
    }


def _serialize(pin: SnapshotPin, items: list[dict[str, object]]) -> str:
    envelope = {
        "schema_version": "1.0",
        "snapshot": _snapshot(pin),
        "techniques": items,
    }
    try:
        return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError, UnicodeEncodeError):
        _fail("invalid_record")


def _fits(context: str, budget: int) -> bool:
    return len(_encoded(context, "invalid_record")) <= budget


def _truncated_first(
    pin: SnapshotPin,
    result: RetrievedTechnique,
    budget: int,
) -> str:
    description = result.description or ""
    empty_item = _item(result, "", True)
    empty_context = _serialize(pin, [empty_item])
    if not _fits(empty_context, budget):
        _fail("context_budget_exceeded")
    low = 0
    high = len(description) - 1
    while low < high:
        middle = (low + high + 1) // 2
        candidate = _item(result, description[:middle], True)
        if _fits(_serialize(pin, [candidate]), budget):
            low = middle
        else:
            high = middle - 1
    item = _item(result, description[:low], True)
    return _serialize(pin, [item])


def _context(
    pin: SnapshotPin,
    ranked: tuple[RetrievedTechnique, ...],
    budget: int,
) -> tuple[str, tuple[RetrievedTechnique, ...]]:
    empty = _serialize(pin, [])
    if not _fits(empty, budget):
        _fail("context_budget_exceeded")
    if not ranked:
        return empty, ()
    items: list[dict[str, object]] = []
    included: list[RetrievedTechnique] = []
    for index, result in enumerate(ranked):
        item = _item(result, result.description or "", False)
        candidate = _serialize(pin, [*items, item])
        if _fits(candidate, budget):
            items.append(item)
            included.append(result)
            continue
        if index == 0 and result.description:
            return _truncated_first(pin, result, budget), (result,)
        if index == 0:
            _fail("context_budget_exceeded")
        break
    return _serialize(pin, items), tuple(included)


def retrieve_techniques(
    catalog: AttackCatalog,
    query: str,
    *,
    top_k: int = 5,
    context_budget_bytes: int = 4096,
) -> RetrievalResult:
    top_k, context_budget_bytes = _validate_bounds(top_k, context_budget_bytes)
    query, query_tokens = _validate_query(query)
    catalog = _validate_catalog(catalog)
    scored: list[tuple[float, TechniqueRecord]] = []
    for record in catalog.records_by_external_id.values():
        if record.revoked or record.deprecated:
            continue
        search_view = "\n".join(
            (
                record.external_id,
                record.name,
                record.description or "",
                " ".join(record.parent_external_ids),
            )
        )
        overlap = query_tokens.intersection(_tokens(search_view))
        score = len(overlap) / len(query_tokens)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda pair: (-pair[0], pair[1].external_id))
    ranked = tuple(_retrieved(record, score, catalog.pin) for score, record in scored[:top_k])
    context, included = _context(catalog.pin, ranked, context_budget_bytes)
    return RetrievalResult(
        query=query,
        top_k=top_k,
        context_budget_bytes=context_budget_bytes,
        context=context,
        snapshot_version=catalog.pin.version,
        snapshot_sha256=catalog.pin.sha256,
        results=included,
    )
