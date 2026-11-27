"""Profile STIX của VSEC: GREEN thận trọng, chỉ tạo ứng viên chờ duyệt."""

import uuid
from typing import Any

from connectors.common.articles import Article
from connectors.common.to_stix import BundleBuilder, SourceProfile

PROFILE = SourceProfile(
    "Công ty Cổ phần An ninh mạng Việt Nam (VSEC)",
    uuid.UUID("b6b657f2-3582-45d5-89f8-814a08f587da"),
    "marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da",
    "green",
    "TLP:GREEN",
    "Trích từ tiêu đề/mô tả HTML, chưa xác minh IOC độc hại; ngày không có giờ chính xác. Theo ",
)


def build_bundle(articles: tuple[Article, ...], *, synthetic: bool = False) -> dict[str, Any]:
    return BundleBuilder(PROFILE).build_bundle(articles, synthetic=synthetic)
