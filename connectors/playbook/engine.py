"""F19: chỉ sinh intent cục bộ, không có executor hoặc LLM."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from connectors.playbook.rules import PUBLIC_TLP, TOKEN, Rule
from connectors.playbook.source import Frame, Source, SourceError
from portal_api.cves import CVE_ID, CveQuery, CveReadService

MARKINGS = PUBLIC_TLP | {"TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"}
STIX_ID = re.compile(
    r"(indicator|vulnerability)--[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}\Z"
)
TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?Z\Z"
)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class Scope:
    tenant: str
    stream: str
    marking_map: dict[str, str]

    def __post_init__(self):
        if not all(isinstance(value, str) and TOKEN.fullmatch(value) for value in (self.tenant, self.stream)):
            raise ValueError("invalid scope")
        if not self.marking_map or any(
            not isinstance(key, str) or not TOKEN.fullmatch(key) or value not in MARKINGS
            for key, value in self.marking_map.items()
        ):
            raise ValueError("invalid marking map")
        object.__setattr__(self, "marking_map", dict(self.marking_map))


@dataclass(frozen=True)
class Event:
    event_id: str
    kind: str
    entity_id: str
    entity_type: str
    version: str
    tlp: str
    score: int | None
    labels: tuple[str, ...]
    cve: str | None
    entity_hash: str


def _marking(data, scope):
    refs = data.get("object_marking_refs")
    if not isinstance(refs, list) or not refs or len(refs) > 100:
        raise SourceError("marking missing or invalid")
    if any(not isinstance(ref, str) or ref not in scope.marking_map for ref in refs):
        raise SourceError("unknown marking")
    order = ("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED")
    return max((scope.marking_map[ref] for ref in refs), key=order.index)


def _normalize(frame: Frame, scope: Scope) -> Event:
    if frame.kind not in ("create", "update"):
        raise SourceError("merge/delete requires reconciliation")
    data = frame.data.get("data")
    if not isinstance(data, dict):
        raise SourceError("missing STIX object")
    entity_id, entity_type = data.get("id"), data.get("type")
    if not isinstance(entity_id, str) or not STIX_ID.fullmatch(entity_id):
        raise SourceError("unsupported entity id")
    if entity_type != entity_id.split("--")[0]:
        raise SourceError("entity type mismatch")
    version = data.get("modified", data.get("created"))
    if not isinstance(version, str) or not TIMESTAMP.fullmatch(version):
        raise SourceError("invalid entity version")
    try:
        version = datetime.fromisoformat(version).isoformat(timespec="microseconds")
    except ValueError:
        raise SourceError("invalid entity version") from None
    score = data.get("x_opencti_score")
    if score is not None and (type(score) is not int or not 0 <= score <= 100):
        raise SourceError("invalid score")
    labels = data.get("labels", [])
    if (
        not isinstance(labels, list)
        or len(labels) > 100
        or any(not isinstance(label, str) or len(label) > 128 for label in labels)
    ):
        raise SourceError("invalid labels")
    cve = data.get("name") if entity_type == "vulnerability" else None
    if cve is not None and (not isinstance(cve, str) or not CVE_ID.fullmatch(cve)):
        raise SourceError("invalid CVE id")
    return Event(
        frame.event_id,
        frame.kind,
        entity_id,
        entity_type,
        version,
        _marking(data, scope),
        score,
        tuple(labels),
        cve,
        _hash(data),
    )


@dataclass(frozen=True)
class W03Matcher:
    """Dùng kết quả W03, chỉ từ snapshot synthetic và W04 read-only của đúng scope."""

    tenant: str
    service: CveReadService

    def matches(self, cve: str) -> tuple[dict, ...]:
        result = self.service.read(CveQuery(kev=True, asset_id=None, q=cve, limit=100, cursor=None), "detail")
        return tuple(
            {
                "asset_id": match["technology_id"],
                "cve": cve,
                "version_assessment": match["version_assessment"],
                "source": result["source"],
            }
            for item in result["items"]
            if item["cve_id"] == cve and item["kev"] is True
            for match in item["matches"]
        )


@dataclass(frozen=True)
class Intent:
    id: str
    tenant: str
    stream: str
    event_id: str
    entity_id: str
    object_version: str
    entity_hash: str
    rule: str
    rule_version: int
    rule_hash: str
    action: str
    tlp: str
    at: str
    details: dict


def _matches(rule: Rule, event: Event) -> bool:
    return (
        rule.enabled
        and event.kind in rule.event_types
        and event.entity_type in rule.entity_types
        and event.tlp in rule.tlp_in
        and (not rule.labels_any or bool(set(rule.labels_any).intersection(event.labels)))
        and (rule.min_score is None or event.score is not None and event.score >= rule.min_score)
    )


def _intents(event, rules, scope, matcher):
    if event.tlp not in PUBLIC_TLP:
        return []
    results = []
    for rule in rules:
        if not _matches(rule, event):
            continue
        if rule.cve_matches_customer_product:
            if matcher is None or event.cve is None:
                continue
            evidence = matcher.matches(event.cve)
        else:
            evidence = ({},)
        for match in evidence:
            for action in rule.actions:
                if action.type == "propose_label" and action.label in event.labels:
                    continue
                identity = _hash(
                    [
                        scope.tenant,
                        scope.stream,
                        event.entity_id,
                        event.version,
                        rule.id,
                        rule.version,
                        match.get("asset_id"),
                        action.type,
                    ]
                )
                details = {
                    **match,
                    **{
                        key: value
                        for key, value in asdict(action).items()
                        if key != "type" and value is not None and value != ()
                    },
                }
                results.append(
                    Intent(
                        identity,
                        scope.tenant,
                        scope.stream,
                        event.event_id,
                        event.entity_id,
                        event.version,
                        event.entity_hash,
                        rule.id,
                        rule.version,
                        rule.rule_hash,
                        action.type,
                        event.tlp,
                        datetime.now(UTC).isoformat(),
                        details,
                    )
                )
    return results


SCHEMA = (
    "CREATE TABLE IF NOT EXISTS cursor(tenant TEXT, stream TEXT, last_event_id TEXT, "
    "PRIMARY KEY(tenant,stream))",
    "CREATE TABLE IF NOT EXISTS receipts(tenant TEXT, stream TEXT, event_id TEXT, digest TEXT, "
    "PRIMARY KEY(tenant,stream,event_id))",
    "CREATE TABLE IF NOT EXISTS versions(tenant TEXT, stream TEXT, "
    "object_key TEXT, version TEXT, digest TEXT, "
    "PRIMARY KEY(tenant,stream,object_key))",
    "CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, tenant TEXT, stream TEXT, payload TEXT)",
    "CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, tenant TEXT, stream TEXT, object_key TEXT, "
    "active INTEGER, payload TEXT)",
    "CREATE TABLE IF NOT EXISTS pending_labels(id TEXT PRIMARY KEY, tenant TEXT, stream TEXT, "
    "object_key TEXT, status TEXT, payload TEXT)",
)


def _initialize(connection):
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    expected = {"cursor", "receipts", "versions", "audit", "outbox", "pending_labels"}
    if tables and tables != expected:
        raise ValueError("dedicated playbook database required")
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        for statement in SCHEMA:
            connection.execute(statement)


def _cursor(connection, scope):
    row = connection.execute(
        "SELECT last_event_id FROM cursor WHERE tenant=? AND stream=?", (scope.tenant, scope.stream)
    ).fetchone()
    return row[0] if row else None


def _order(event_id):
    return tuple(int(value) for value in event_id.split("-"))


def _seen(connection, frame, scope, digest):
    row = connection.execute(
        "SELECT digest FROM receipts WHERE tenant=? AND stream=? AND event_id=?",
        (scope.tenant, scope.stream, frame.event_id),
    ).fetchone()
    if row:
        if row[0] != digest:
            raise SourceError("event id reused with different content")
        return True
    last = _cursor(connection, scope)
    if last is not None and _order(frame.event_id) <= _order(last):
        raise SourceError("unseen event older than cursor")
    return False


def _superseded(connection, event, scope):
    key = (scope.tenant, scope.stream, _hash(event.entity_id))
    row = connection.execute(
        "SELECT version,digest FROM versions WHERE tenant=? AND stream=? AND object_key=?", key
    ).fetchone()
    if row and event.version == row[0] and event.entity_hash != row[1]:
        raise SourceError("conflicting object version")
    if row and event.version <= row[0]:
        return True
    connection.execute(
        "INSERT INTO versions VALUES(?,?,?,?,?) ON CONFLICT(tenant,stream,object_key) "
        "DO UPDATE SET version=excluded.version,digest=excluded.digest",
        (*key, event.version, event.entity_hash),
    )
    # Phiên bản mới làm bản nháp trước đó lỗi thời; không xóa lịch sử.
    connection.execute("UPDATE outbox SET active=0 WHERE tenant=? AND stream=? AND object_key=?", key)
    connection.execute(
        "UPDATE pending_labels SET status='stale' WHERE tenant=? AND stream=? AND object_key=? "
        "AND status='pending'",
        key,
    )
    return False


def _write_intents(connection, intents):
    for intent in intents:
        payload = json.dumps(asdict(intent), ensure_ascii=True, sort_keys=True)
        key = (intent.id, intent.tenant, intent.stream)
        connection.execute("INSERT INTO audit VALUES(?,?,?,?)", (*key, payload))
        if intent.action == "create_alert":
            connection.execute(
                "INSERT INTO outbox VALUES(?,?,?,?,1,?)", (*key, _hash(intent.entity_id), payload)
            )
        if intent.action == "propose_label":
            connection.execute(
                "INSERT INTO pending_labels VALUES(?,?,?,?,'pending',?)",
                (*key, _hash(intent.entity_id), payload),
            )


def _process(connection, frame, rules, scope, matcher):
    digest = _hash([frame.kind, frame.data])
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        if _seen(connection, frame, scope, digest):
            return []
        event = _normalize(frame, scope)
        intents = [] if _superseded(connection, event, scope) else _intents(event, rules, scope, matcher)
        _write_intents(connection, intents)
        connection.execute(
            "INSERT INTO receipts VALUES(?,?,?,?)", (scope.tenant, scope.stream, frame.event_id, digest)
        )
        connection.execute(
            "INSERT INTO cursor VALUES(?,?,?) ON CONFLICT(tenant,stream) "
            "DO UPDATE SET last_event_id=excluded.last_event_id",
            (scope.tenant, scope.stream, frame.event_id),
        )
    return intents


def run(
    source: Source,
    rules: tuple[Rule, ...],
    scope: Scope,
    db: Path,
    *,
    dry_run: bool = True,
    matcher: W03Matcher | None = None,
) -> list[Intent]:
    if matcher is not None and matcher.tenant != scope.tenant:
        raise ValueError("W03 snapshot scope mismatch")
    results = []
    # Dry-run chỉ dùng DB trong RAM, không mở/khởi tạo DB thật.
    with closing(sqlite3.connect(":memory:" if dry_run else db, timeout=5)) as connection:
        _initialize(connection)
        for frame in source.events(_cursor(connection, scope)):
            results.extend(_process(connection, frame, rules, scope, matcher))
    return results


def read_outbox(db: Path, scope: Scope, audience: str) -> list[dict]:
    """Projection cục bộ cho adapter portal/MCP tương lai; caller phải kiểm quyền nguồn/người đọc."""
    if audience not in ("portal", "hermes"):
        raise ValueError("invalid audience")
    uri = Path(db).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        rows = connection.execute(
            "SELECT payload FROM outbox WHERE tenant=? AND stream=? AND active=1 ORDER BY id",
            (scope.tenant, scope.stream),
        )
        return [
            item
            for (payload,) in rows
            if (item := json.loads(payload))["tlp"] in PUBLIC_TLP and audience in item["details"]["audience"]
        ]
