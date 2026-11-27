"""Profile STIX của MST; giữ nguyên ID, provenance và nhãn của B03."""

import uuid
from typing import Any

from connectors.common.articles import Article
from connectors.common.to_stix import BundleBuilder, SourceProfile

SOURCE = "Cổng Thông tin điện tử Bộ Khoa học và Công nghệ"
NAMESPACE = uuid.UUID("59a3f17f-0383-40cb-a92f-0b9f36e2a003")
MARKING_ID = "marking-definition--613f2e26-407d-48c7-9eca-b8e91df99dc9"
PROFILE = SourceProfile(
    SOURCE,
    NAMESPACE,
    MARKING_ID,
    "white",
    "TLP:CLEAR",
    "Trích tự động từ RSS, chưa xác minh IOC độc hại. Theo ",
)


def build_bundle(articles: tuple[Article, ...], *, synthetic: bool = False) -> dict[str, Any]:
    return BundleBuilder(PROFILE).build_bundle(articles, synthetic=synthetic)
