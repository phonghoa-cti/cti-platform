"""Mẫu thư tĩnh cho F21: biến nằm trong allowlist và luôn được escape khi render."""

from __future__ import annotations

import html
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from string import Template


class TemplateError(ValueError):
    """Tên mẫu, biến hoặc giá trị không hợp lệ."""


@dataclass(frozen=True)
class MessageTemplate:
    """Một mẫu tĩnh; nội dung mẫu do nhóm viết, không nhận mẫu từ người dùng."""

    channel: str
    variables: frozenset[str]
    subject: str
    text: str
    html: str | None = None
    text_row: str | None = None
    html_row: str | None = None


@dataclass(frozen=True)
class RenderedMessage:
    channel: str
    subject: str
    text: str
    html: str | None


_ROW_VARIABLES = frozenset({"cve_id", "title", "kev_label", "cvss"})
MAX_ROWS = 10
MAX_VALUE_LENGTH = 500

TEMPLATES: Mapping[str, MessageTemplate] = {
    "weekly_vulnerability_email": MessageTemplate(
        channel="email",
        variables=frozenset({"tenant_name", "period_label", "matched_cves", "kev_cves", "tlp"}),
        subject="[Phong Hỏa][$tlp] Báo cáo lỗ hổng tuần $period_label - $tenant_name",
        text=(
            "Kính gửi $tenant_name,\n\n"
            "Phong Hỏa gửi báo cáo lỗ hổng tuần $period_label.\n"
            "- Số CVE khớp tài sản: $matched_cves\n"
            "- Số CVE đang bị khai thác (KEV): $kev_cves\n\n"
            "CVE ưu tiên:\n$rows\n\n"
            "Lưu ý: khớp theo vendor/product, chưa đánh giá phiên bản. "
            "Vui lòng kiểm tra trên portal trước khi xử lý.\n"
            "Phân loại chia sẻ: $tlp\n"
        ),
        html=(
            "<p>Kính gửi $tenant_name,</p>"
            "<p>Phong Hỏa gửi báo cáo lỗ hổng tuần $period_label.</p>"
            "<ul><li>Số CVE khớp tài sản: $matched_cves</li>"
            "<li>Số CVE đang bị khai thác (KEV): $kev_cves</li></ul>"
            "<table><thead><tr><th>CVE</th><th>Tiêu đề</th><th>KEV</th><th>CVSS</th></tr></thead>"
            "<tbody>$rows</tbody></table>"
            "<p>Lưu ý: khớp theo vendor/product, chưa đánh giá phiên bản.</p>"
            "<p>Phân loại chia sẻ: $tlp</p>"
        ),
        text_row="- $cve_id ($kev_label, CVSS $cvss): $title",
        html_row="<tr><td>$cve_id</td><td>$title</td><td>$kev_label</td><td>$cvss</td></tr>",
    ),
    "weekly_vulnerability_telegram": MessageTemplate(
        channel="telegram",
        variables=frozenset({"period_label", "matched_cves", "kev_cves"}),
        subject="Phong Hỏa: báo cáo lỗ hổng tuần $period_label",
        text=(
            "Phong Hỏa: báo cáo lỗ hổng tuần $period_label đã sẵn sàng "
            "($matched_cves CVE khớp tài sản, $kev_cves KEV). Vui lòng xem chi tiết trên portal."
        ),
    ),
}


def clean_text(value: object) -> str:
    """Chuyển giá trị thành chuỗi một dòng, bỏ ký tự điều khiển để chặn chèn header."""

    text = "" if value is None else str(value)
    cleaned = "".join(
        " " if unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} else char for char in text
    )
    cleaned = " ".join(cleaned.split())
    return cleaned[:MAX_VALUE_LENGTH]


def _substitute(template: str, values: Mapping[str, str]) -> str:
    try:
        return Template(template).substitute(values)
    except (KeyError, ValueError) as exc:
        raise TemplateError("template variable missing") from exc


def _check_keys(values: Mapping[str, object], allowed: frozenset[str]) -> None:
    if set(values) != allowed:
        raise TemplateError("template variables must match allowlist")


def render_message(
    name: str,
    variables: Mapping[str, object],
    rows: Sequence[Mapping[str, object]] = (),
) -> RenderedMessage:
    """Render mẫu: text đã làm sạch, HTML đã escape từng biến trước khi chèn."""

    template = TEMPLATES.get(name)
    if template is None:
        raise TemplateError("unknown template")
    _check_keys(variables, template.variables)
    for row in rows:
        _check_keys(row, _ROW_VARIABLES)
    plain = {key: clean_text(value) for key, value in variables.items()}
    plain_rows = [{key: clean_text(value) for key, value in row.items()} for row in rows[:MAX_ROWS]]
    text_rows = ""
    html_rows = ""
    if template.text_row is not None:
        text_rows = "\n".join(_substitute(template.text_row, row) for row in plain_rows) or "- (không có)"
    if template.html_row is not None:
        escaped_rows = [{key: html.escape(value) for key, value in row.items()} for row in plain_rows]
        html_rows = "".join(_substitute(template.html_row, row) for row in escaped_rows)
    subject = _substitute(template.subject, plain)
    text = _substitute(template.text, {**plain, "rows": text_rows})
    body_html = None
    if template.html is not None:
        escaped = {key: html.escape(value) for key, value in plain.items()}
        body_html = _substitute(template.html, {**escaped, "rows": html_rows})
    return RenderedMessage(channel=template.channel, subject=clean_text(subject), text=text, html=body_html)
