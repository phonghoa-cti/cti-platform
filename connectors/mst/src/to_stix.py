"""Chuyển các dấu hiệu trích thô thành observable, không gán nhãn độc hại."""

import json
import uuid
from typing import Any

from connectors.mst.src.parse import Article
from phonghoa_core import Ioc, IocType

SCO_NAMESPACE = uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7")
NAMESPACE = uuid.UUID("59a3f17f-0383-40cb-a92f-0b9f36e2a003")
SOURCE = "Cổng Thông tin điện tử Bộ Khoa học và Công nghệ"
MARKING_ID = "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"
CREATED = "2026-11-26T00:00:00.000Z"
TYPES = {
    IocType.IPV4: "ipv4-addr",
    IocType.IPV6: "ipv6-addr",
    IocType.DOMAIN: "domain-name",
    IocType.URL: "url",
    IocType.EMAIL: "email-addr",
    IocType.MD5: "file",
    IocType.SHA1: "file",
    IocType.SHA256: "file",
}
HASHES = {IocType.MD5: "MD5", IocType.SHA1: "SHA-1", IocType.SHA256: "SHA-256"}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _id(kind: str, key: str, namespace: uuid.UUID = NAMESPACE) -> str:
    return f"{kind}--{uuid.uuid5(namespace, key)}"


def _base(kind: str, object_id: str) -> dict[str, Any]:
    return {
        "type": kind,
        "spec_version": "2.1",
        "id": object_id,
        "object_marking_refs": [MARKING_ID],
    }


def _sco(ioc: Ioc) -> dict[str, Any]:
    props = {"hashes": {HASHES[ioc.type]: ioc.value}} if ioc.type in HASHES else {"value": ioc.value}
    kind = TYPES[ioc.type]
    return {**_base(kind, _id(kind, _canonical(props), SCO_NAMESPACE)), **props}


def _identity() -> dict[str, Any]:
    return {
        **_base("identity", _id("identity", SOURCE)),
        "name": SOURCE,
        "identity_class": "organization",
        "created": CREATED,
        "modified": CREATED,
    }


def _vulnerability(cve: str, identity_id: str) -> dict[str, Any]:
    return {
        **_base("vulnerability", _id("vulnerability", cve)),
        "name": cve,
        "created_by_ref": identity_id,
        "created": CREATED,
        "modified": CREATED,
        "external_references": [{"source_name": "cve", "external_id": cve}],
    }


def _report(article: Article, refs: list[str], identity_id: str, synthetic: bool) -> dict[str, Any]:
    return {
        **_base("report", _id("report", article.url)),
        "created_by_ref": identity_id,
        "created": article.published,
        "modified": article.published,
        "published": article.published,
        "name": article.title,
        "description": "Trích tự động từ RSS, chưa xác minh IOC độc hại. Theo " + SOURCE,
        "report_types": ["threat-report"],
        "labels": ["TLP:CLEAR", "unverified", *(["synthetic"] if synthetic else [])],
        "object_refs": sorted(set(refs)),
        "external_references": [{"source_name": SOURCE, "url": article.url}],
    }


def build_bundle(articles: tuple[Article, ...], *, synthetic: bool = False) -> dict[str, Any]:
    # TLP 2.0 CLEAR tương đương WHITE trong marking chuẩn STIX 2.1 (profile W05).
    marking = {
        "type": "marking-definition",
        "spec_version": "2.1",
        "id": MARKING_ID,
        "created": "2017-01-20T00:00:00.000Z",
        "name": "TLP:WHITE",
        "definition_type": "tlp",
        "definition": {"tlp": "white"},
    }
    identity = _identity()
    objects = {o["id"]: o for o in (marking, identity)}
    for article in articles:
        related = [_sco(ioc) for ioc in article.iocs]
        related += [_vulnerability(cve, identity["id"]) for cve in article.cves]
        objects.update((o["id"], o) for o in related)
        report = _report(article, [o["id"] for o in related], identity["id"], synthetic)
        objects[report["id"]] = report
    ordered = list(objects.values())
    return {"type": "bundle", "id": _id("bundle", _canonical(ordered)), "objects": ordered}
