"""Bộ gửi thư cho outbox F21. Chỉ được gọi sau khi người duyệt đã approve."""

from __future__ import annotations

import os
import smtplib
import ssl
from collections.abc import Mapping
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol


class SenderError(RuntimeError):
    """Gửi thất bại; nội dung lỗi không chứa secret."""


class SenderSettingsError(ValueError):
    """Thiếu hoặc sai cấu hình SMTP."""


@dataclass(frozen=True)
class OutboundMessage:
    channel: str
    address: str
    subject: str
    text: str
    html: str | None


class MessageSender(Protocol):
    def send(self, message: OutboundMessage) -> None: ...


@dataclass(frozen=True)
class SmtpSettings:
    """Cấu hình SMTP chỉ đọc từ biến môi trường; không có giá trị mặc định cho secret."""

    host: str
    port: int
    username: str
    password: str
    sender: str
    timeout: float = 10.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SmtpSettings:
        values = os.environ if env is None else env
        try:
            settings = cls(
                host=values["F21_SMTP_HOST"],
                port=int(values.get("F21_SMTP_PORT", "587")),
                username=values["F21_SMTP_USERNAME"],
                password=values["F21_SMTP_PASSWORD"],
                sender=values["F21_SMTP_FROM"],
                timeout=float(values.get("F21_SMTP_TIMEOUT", "10")),
            )
        except (KeyError, ValueError) as exc:
            raise SenderSettingsError("Thiếu hoặc sai cấu hình SMTP F21") from exc
        if (
            not settings.host
            or not settings.sender
            or not 1 <= settings.port <= 65535
            or settings.timeout <= 0
        ):
            raise SenderSettingsError("Thiếu hoặc sai cấu hình SMTP F21")
        return settings

    def __repr__(self) -> str:
        return f"SmtpSettings(host={self.host!r}, port={self.port}, sender={self.sender!r})"


class SmtpEmailSender:
    """Gửi qua SMTP + STARTTLS với kiểm tra chứng chỉ mặc định (không bao giờ tắt TLS)."""

    def __init__(self, settings: SmtpSettings) -> None:
        self.settings = settings

    def _build(self, message: OutboundMessage) -> EmailMessage:
        email = EmailMessage()
        email["From"] = self.settings.sender
        email["To"] = message.address
        email["Subject"] = message.subject
        email.set_content(message.text)
        if message.html is not None:
            email.add_alternative(message.html, subtype="html")
        return email

    def send(self, message: OutboundMessage) -> None:
        if message.channel != "email":
            raise SenderError("channel not supported by SMTP sender")
        email = self._build(message)
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(
                self.settings.host, self.settings.port, timeout=self.settings.timeout
            ) as client:
                client.starttls(context=context)
                client.login(self.settings.username, self.settings.password)
                client.send_message(email)
        except (OSError, smtplib.SMTPException) as exc:
            raise SenderError("smtp send failed") from exc
