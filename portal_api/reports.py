"""F21: báo cáo lỗ hổng tuần tiếng Việt từ read model W03, render HTML an toàn."""

from __future__ import annotations

import hashlib
import html
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from string import Template

from portal_api.cves import CveQuery, CveReadService, _decode_cursor
from portal_api.email_templates import clean_text

REPORT_KIND = "weekly_vulnerability"
ALLOWED_TLP = ("TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT")
DEFAULT_TLP = "TLP:AMBER"
MAX_REPORT_ITEMS = 200
PAGE_LIMIT = 100
REPORT_NOTICE = (
    "Khớp theo vendor/product chính xác, chưa đánh giá phiên bản; "
    "đây là dữ liệu hỗ trợ ưu tiên, không phải kết luận đã bị ảnh hưởng."
)


class InvalidReportRequest(ValueError):
    """Tham số báo cáo không hợp lệ."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _severity(cvss: object) -> str:
    if not isinstance(cvss, (int, float)):
        return "unknown"
    if cvss >= 9:
        return "critical"
    if cvss >= 7:
        return "high"
    if cvss >= 4:
        return "medium"
    return "low"


def _report_item(item: Mapping[str, object]) -> dict[str, object]:
    matches = item.get("matches") or []
    return {
        "priority": item["priority"],
        "cve_id": item["cve_id"],
        "title": item["title"],
        "kev": item["kev"],
        "kev_due_date": item.get("kev_due_date"),
        "cvss_base_score": item.get("cvss_base_score"),
        "epss_score": item.get("epss_score"),
        "advisory_url": item.get("advisory_url"),
        "technologies": [
            f"{match['vendor']} {match['product']} {match['software_version']}".strip() for match in matches
        ],
    }


def _collect_items(service: CveReadService) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Đọc lần lượt các trang W03 (cùng snapshot) tới khi hết hoặc chạm giới hạn."""

    items: list[dict[str, object]] = []
    cursor = None
    while True:
        query = CveQuery(kev=None, asset_id=None, q=None, limit=PAGE_LIMIT, cursor=cursor)
        page = service.read(query, "detail")
        items.extend(_report_item(item) for item in page["items"])
        next_cursor = page["page"]["next_cursor"]
        if next_cursor is None or len(items) >= MAX_REPORT_ITEMS:
            return items[:MAX_REPORT_ITEMS], page
        cursor = _decode_cursor(next_cursor)


def build_weekly_vulnerability_report(
    service: CveReadService,
    *,
    tenant_name: str,
    tlp: str = DEFAULT_TLP,
    clock: Callable[[], datetime] = _utc_now,
) -> dict[str, object]:
    """Tạo dữ liệu báo cáo (dict thuần) để render HTML, preview và tạo outbox."""

    if tlp not in ALLOWED_TLP:
        raise InvalidReportRequest("unsupported tlp")
    name = clean_text(tenant_name)
    if not name:
        raise InvalidReportRequest("tenant name required")
    now = clock().astimezone(UTC)
    items, last_page = _collect_items(service)
    severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    for item in items:
        severity[_severity(item["cvss_base_score"])] += 1
    summary = last_page["summary"]
    period_start = (now - timedelta(days=7)).date().isoformat()
    report: dict[str, object] = {
        "kind": REPORT_KIND,
        "tenant_name": name,
        "tlp": tlp,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period_label": f"{period_start} → {now.date().isoformat()}",
        "matched_cves": summary["matched_cves"],
        "kev_cves": summary["kev_cves"],
        "severity": severity,
        "affected_technologies": len({tech for item in items for tech in item["technologies"]}),
        "items": items,
        "truncated": summary["matched_cves"] > len(items),
        "source": last_page["source"],
        "notice": REPORT_NOTICE,
    }
    report["content_hash"] = report_hash(report)
    return report


def report_hash(report: Mapping[str, object]) -> str:
    content = {key: value for key, value in report.items() if key != "content_hash"}
    raw = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _e(value: object) -> str:
    """Escape mọi giá trị trước khi chèn vào HTML (tương đương autoescape bật)."""

    if value is None:
        return "—"
    return html.escape(str(value), quote=True)


_PAGE = Template(
    """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Báo cáo lỗ hổng tuần - $tenant_name</title>
<style>
body { font-family: "Noto Sans", Arial, sans-serif; color: #1a1a1a; margin: 2rem; }
h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
.tlp { display: inline-block; padding: 0.1rem 0.5rem; background: #1a1a1a;
  color: #ffc000; font-weight: bold; }
table { border-collapse: collapse; width: 100%; margin-top: 1rem; font-size: 0.9rem; }
th, td { border: 1px solid #999; padding: 0.3rem 0.5rem; text-align: left; vertical-align: top; }
th { background: #eee; }
.kev { color: #b00020; font-weight: bold; }
.notice { font-size: 0.85rem; color: #444; }
@page { size: A4; margin: 15mm; }
@media print {
  body { margin: 0; }
  tr { page-break-inside: avoid; }
  a { color: inherit; text-decoration: none; }
}
</style>
</head>
<body>
<p><span class="tlp">$tlp</span></p>
<h1>Báo cáo lỗ hổng tuần</h1>
<p>Doanh nghiệp: <strong>$tenant_name</strong> · Kỳ báo cáo: $period_label · Tạo lúc: $generated_at</p>
<h2>Tóm tắt</h2>
<ul>
<li>Số CVE khớp tài sản: <strong>$matched_cves</strong></li>
<li>Số CVE đang bị khai thác (CISA KEV): <strong class="kev">$kev_cves</strong></li>
<li>Theo mức CVSS: nghiêm trọng $critical · cao $high · trung bình $medium · thấp $low
 · chưa có điểm $unknown</li>
<li>Số công nghệ bị ảnh hưởng: $affected_technologies</li>
</ul>
<h2>Danh sách ưu tiên</h2>
<table>
<thead><tr><th>#</th><th>CVE</th><th>Tiêu đề</th><th>KEV</th><th>CVSS</th><th>EPSS</th>
<th>Tài sản khớp</th><th>Nguồn</th></tr></thead>
<tbody>
$rows
</tbody>
</table>
$truncated
<h2>Nguồn và giới hạn</h2>
<p class="notice">Dataset: $dataset_id · Dữ liệu tính đến: $source_as_of · Loại nguồn: $source_kind</p>
<p class="notice">$notice</p>
</body>
</html>
"""
)

_ROW = Template(
    "<tr><td>$priority</td><td>$cve_id</td><td>$title</td><td>$kev</td><td>$cvss</td>"
    "<td>$epss</td><td>$technologies</td><td>$advisory</td></tr>"
)


def _advisory_cell(url: object) -> str:
    if isinstance(url, str) and url.startswith("https://"):
        return f'<a href="{_e(url)}" rel="noopener noreferrer">{_e(url)}</a>'
    return "—"


def _render_row(item: Mapping[str, object]) -> str:
    kev = f'<span class="kev">Có (hạn {_e(item["kev_due_date"])})</span>' if item["kev"] else "Không"
    return _ROW.substitute(
        priority=_e(item["priority"]),
        cve_id=_e(item["cve_id"]),
        title=_e(item["title"]),
        kev=kev,
        cvss=_e(item["cvss_base_score"]),
        epss=_e(item["epss_score"]),
        technologies="<br>".join(_e(tech) for tech in item["technologies"]) or "—",
        advisory=_advisory_cell(item["advisory_url"]),
    )


def render_report_html(report: Mapping[str, object]) -> str:
    """Render HTML tự chứa, không script, in được ra PDF bằng chức năng in của trình duyệt."""

    rows = "\n".join(_render_row(item) for item in report["items"])
    if not rows:
        rows = '<tr><td colspan="8">Không có CVE nào khớp tài sản trong kỳ này.</td></tr>'
    truncated = ""
    if report["truncated"]:
        truncated = f'<p class="notice">Chỉ hiển thị {_e(len(report["items"]))} CVE đầu tiên.</p>'
    severity = report["severity"]
    source = report["source"]
    return _PAGE.substitute(
        tenant_name=_e(report["tenant_name"]),
        tlp=_e(report["tlp"]),
        period_label=_e(report["period_label"]),
        generated_at=_e(report["generated_at"]),
        matched_cves=_e(report["matched_cves"]),
        kev_cves=_e(report["kev_cves"]),
        affected_technologies=_e(report["affected_technologies"]),
        rows=rows,
        truncated=truncated,
        dataset_id=_e(source.get("dataset_id")),
        source_as_of=_e(source.get("source_as_of")),
        source_kind=_e(source.get("kind")),
        notice=_e(report["notice"]),
        **{key: _e(value) for key, value in severity.items()},
    )


def email_rows(report: Mapping[str, object]) -> list[dict[str, object]]:
    """Dữ liệu hàng cho mẫu email (đã giới hạn số hàng trong email_templates)."""

    return [
        {
            "cve_id": item["cve_id"],
            "title": item["title"],
            "kev_label": "KEV" if item["kev"] else "không KEV",
            "cvss": "—" if item["cvss_base_score"] is None else item["cvss_base_score"],
        }
        for item in report["items"]
    ]
