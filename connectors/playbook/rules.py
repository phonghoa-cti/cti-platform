"""Bộ nạp YAML khai báo, chỉ hỗ trợ cú pháp dữ liệu hẹp của F19."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

PUBLIC_TLP = frozenset({"TLP:CLEAR", "TLP:GREEN"})
ENTITY_TYPES = frozenset({"indicator", "vulnerability"})
EVENT_TYPES = frozenset({"create", "update"})
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+-]{0,127}\Z")
KEY = re.compile(r"[a-z_]+\Z")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _bad_constant(_value):
    raise ValueError("non-finite value")


def strict_json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_bad_constant)
    except (ValueError, RecursionError, UnicodeError):
        raise ValueError("invalid JSON") from None


def _scalar(raw):
    if raw.startswith('"'):
        value = strict_json(raw)
        if not isinstance(value, str):
            raise ValueError("invalid quoted scalar")
        return value
    if raw in ("true", "false", "null"):
        return {"true": True, "false": False, "null": None}[raw]
    if re.fullmatch(r"-?(?:0|[1-9][0-9]{0,9})", raw):
        return int(raw)
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        # Danh sách phẳng: dấu phẩy phân cách token hoặc chuỗi JSON có ngoặc kép.
        parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', inner)
        return [_scalar(part.strip()) for part in parts if _nonempty(part)]
    if TOKEN.fullmatch(raw):
        return raw
    raise ValueError("unsupported YAML scalar")


def _nonempty(value):
    if not value.strip():
        raise ValueError("empty list item")
    return True


def _tokens(raw):
    result = []
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        value = line.lstrip(" ")
        indent = len(line) - len(value)
        if indent % 2 or indent > 24 or "\t" in line:
            raise ValueError("invalid YAML indentation")
        if value.startswith("- "):
            result.append((indent, "-"))
            result.append((indent + 2, value[2:]))
        else:
            result.append((indent, value))
    return result


def _block(tokens, index, indent):
    if index >= len(tokens) or tokens[index][0] != indent:
        raise ValueError("missing YAML block")
    sequence = tokens[index][1] == "-"
    result = [] if sequence else {}
    while index < len(tokens) and tokens[index][0] == indent:
        value = tokens[index][1]
        index += 1
        if sequence:
            if value != "-":
                raise ValueError("mixed YAML block")
            item, index = _block(tokens, index, indent + 2)
            result.append(item)
        else:
            key, sep, tail = value.partition(":")
            if not sep or not KEY.fullmatch(key) or key in result:
                raise ValueError("invalid or duplicate YAML key")
            if tail and not tail.startswith(" "):
                raise ValueError("invalid YAML mapping")
            if tail.strip():
                result[key] = _scalar(tail.strip())
            else:
                result[key], index = _block(tokens, index, indent + 2)
    return result, index


def _yaml(raw):
    if raw.lstrip().startswith("{"):
        return strict_json(raw)
    tokens = _tokens(raw)
    result, end = _block(tokens, 0, 0)
    if end != len(tokens):
        raise ValueError("invalid YAML block")
    return result


def _mapping(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys():
        raise ValueError("missing mapping fields")
    if value.keys() - set(required) - set(optional):
        raise ValueError("unknown mapping fields")
    return value


def _token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError("invalid token")
    return value


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid integer")
    return value


def _list(value, allowed=None):
    if not isinstance(value, list) or not 1 <= len(value) <= 100:
        raise ValueError("invalid list")
    values = tuple(_token(item) for item in value)
    if len(set(values)) != len(values) or (allowed is not None and not set(values) <= allowed):
        raise ValueError("invalid list values")
    return values


@dataclass(frozen=True)
class Action:
    type: str
    label: str | None = None
    severity: str | None = None
    audience: tuple[str, ...] = ()
    template_id: str | None = None


@dataclass(frozen=True)
class Rule:
    id: str
    version: int
    enabled: bool
    event_types: tuple[str, ...]
    entity_types: tuple[str, ...]
    tlp_in: tuple[str, ...]
    labels_any: tuple[str, ...]
    min_score: int | None
    cve_matches_customer_product: bool
    actions: tuple[Action, ...]
    rule_hash: str


def _action(value):
    if not isinstance(value, dict):
        raise ValueError("invalid action")
    kind = value.get("type")
    if kind == "propose_label":
        _mapping(value, {"type", "label"})
        return Action(kind, label=_token(value["label"]))
    if kind == "create_alert":
        _mapping(value, {"type", "audience", "template_id"}, {"severity"})
        severity = value.get("severity", "medium")
        if severity not in ("medium", "high", "low"):
            raise ValueError("invalid severity")
        return Action(
            kind,
            severity=severity,
            audience=_list(value["audience"], {"portal", "hermes"}),
            template_id=_token(value["template_id"]),
        )
    if kind == "log":
        _mapping(value, {"type"})
        return Action(kind)
    raise ValueError("unsupported action")


def _rule(value):
    _mapping(value, {"id", "version", "enabled", "when", "actions"})
    when = _mapping(
        value["when"],
        {"event_types", "entity_types", "tlp_in"},
        {"labels_any", "min_score", "cve_matches_customer_product"},
    )
    cve = when.get("cve_matches_customer_product", False)
    entities = _list(when["entity_types"], ENTITY_TYPES)
    if (
        type(value["enabled"]) is not bool
        or type(cve) is not bool
        or (cve and entities != ("vulnerability",))
    ):
        raise ValueError("invalid rule flag")
    actions = value["actions"]
    if not isinstance(actions, list) or not 1 <= len(actions) <= 10:
        raise ValueError("invalid actions")
    parsed = tuple(_action(action) for action in actions)
    if len({action.type for action in parsed}) != len(parsed):
        raise ValueError("duplicate action type")
    digest = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    return Rule(
        _token(value["id"]),
        _integer(value["version"], 1, 2**31 - 1),
        value["enabled"],
        _list(when["event_types"], EVENT_TYPES),
        entities,
        _list(when["tlp_in"], PUBLIC_TLP),
        _list(when["labels_any"]) if "labels_any" in when else (),
        _integer(when["min_score"], 0, 100) if "min_score" in when else None,
        cve,
        parsed,
        digest,
    )


def load_rules(path: Path) -> tuple[Rule, ...]:
    with Path(path).open("rb") as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError("rules too large")
    try:
        config = _mapping(_yaml(raw.decode("utf-8")), {"schema_version", "rules"})
        if type(config["schema_version"]) is not int or config["schema_version"] != 1:
            raise ValueError("invalid schema version")
        rules = config["rules"]
        if not isinstance(rules, list) or not 1 <= len(rules) <= 100:
            raise ValueError("invalid rule count")
        result = tuple(_rule(rule) for rule in rules)
        if len({rule.id for rule in result}) != len(result):
            raise ValueError("duplicate rule id")
        return result
    except (ValueError, RecursionError, UnicodeError, TypeError):
        raise ValueError("invalid playbook configuration") from None
