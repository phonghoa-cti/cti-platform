"""Chuyển các dấu hiệu trích thô thành observable, không gán nhãn độc hại."""

import json
import uuid
from dataclasses import dataclass
from typing import Any

from connectors.common.articles import Article
from phonghoa_core import Ioc, IocType

SCO_NAMESPACE = uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7")
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


def _id(kind: str, key: str, namespace: uuid.UUID) -> str:
    return f"{kind}--{uuid.uuid5(namespace, key)}"


@dataclass(frozen=True)
class SourceProfile:
    name: str
    namespace: uuid.UUID
    marking_id: str
    marking: str
    tlp_label: str
    description: str


class BundleBuilder:
    def __init__(self, profile: SourceProfile) -> None:
        self.profile = profile

    def _id(self, kind: str, key: str, namespace: uuid.UUID | None = None) -> str:
        return _id(kind, key, namespace or self.profile.namespace)

    def _base(self, kind: str, object_id: str) -> dict[str, Any]:
        return {
            "type": kind,
            "spec_version": "2.1",
            "id": object_id,
            "object_marking_refs": [self.profile.marking_id],
        }

    def _sco(self, ioc: Ioc) -> dict[str, Any]:
        props = {"hashes": {HASHES[ioc.type]: ioc.value}} if ioc.type in HASHES else {"value": ioc.value}
        kind = TYPES[ioc.type]
        return {**self._base(kind, self._id(kind, _canonical(props), SCO_NAMESPACE)), **props}

    def _identity(self) -> dict[str, Any]:
        return {
            **self._base("identity", self._id("identity", self.profile.name)),
            "name": self.profile.name,
            "identity_class": "organization",
            "created": CREATED,
            "modified": CREATED,
        }

    def _vulnerability(self, cve: str, identity_id: str) -> dict[str, Any]:
        return {
            **self._base("vulnerability", self._id("vulnerability", cve)),
            "name": cve,
            "created_by_ref": identity_id,
            "created": CREATED,
            "modified": CREATED,
            "external_references": [{"source_name": "cve", "external_id": cve}],
        }

    def _report(self, article: Article, refs: list[str], identity_id: str, synthetic: bool) -> dict[str, Any]:
        return {
            **self._base("report", self._id("report", article.url)),
            "created_by_ref": identity_id,
            "created": article.published,
            "modified": article.published,
            "published": article.published,
            "name": article.title,
            "description": self.profile.description + self.profile.name,
            "report_types": ["threat-report"],
            "labels": [self.profile.tlp_label, "unverified", *(["synthetic"] if synthetic else [])],
            "object_refs": sorted(set(refs)),
            "external_references": [{"source_name": self.profile.name, "url": article.url}],
        }

    def build_bundle(self, articles: tuple[Article, ...], *, synthetic: bool = False) -> dict[str, Any]:
        # TLP:CLEAR dùng WHITE chuẩn STIX 2.1; GREEN dùng marking GREEN.
        marking = {
            "type": "marking-definition",
            "spec_version": "2.1",
            "id": self.profile.marking_id,
            "created": "2017-01-20T00:00:00.000Z",
            "name": "TLP:" + self.profile.marking.upper(),
            "definition_type": "tlp",
            "definition": {"tlp": self.profile.marking},
        }
        identity = self._identity()
        objects = {o["id"]: o for o in (marking, identity)}
        for article in articles:
            related = [self._sco(ioc) for ioc in article.iocs]
            related += [self._vulnerability(cve, identity["id"]) for cve in article.cves]
            objects.update((o["id"], o) for o in related)
            report = self._report(article, [o["id"] for o in related], identity["id"], synthetic)
            objects[report["id"]] = report
        ordered = list(objects.values())
        return {"type": "bundle", "id": self._id("bundle", _canonical(ordered)), "objects": ordered}
