"""F21: danh sách nhận và outbox cần người duyệt (preview → approve → send).

Không có đường nào tự gửi: chỉ hàm ``send_batch`` gửi, và chỉ khi lô đã ``approved``.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from portal_api.email_templates import RenderedMessage, clean_text, render_message
from portal_api.reports import email_rows
from portal_api.senders import MessageSender, OutboundMessage, SenderError

CHANNELS = ("email", "telegram")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}\Z")
TELEGRAM_PATTERN = re.compile(r"-?[0-9]{1,20}\Z")
TEMPLATE_BY_CHANNEL = {"email": "weekly_vulnerability_email", "telegram": "weekly_vulnerability_telegram"}
MAX_RECIPIENTS = 200

SCHEMA = """
CREATE TABLE IF NOT EXISTS dissemination_recipients(
  id INTEGER PRIMARY KEY,
  display_name TEXT NOT NULL,
  channel TEXT NOT NULL CHECK(channel IN ('email','telegram')),
  address TEXT NOT NULL,
  address_key TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(channel, address_key)
);
CREATE TABLE IF NOT EXISTS outbox_batches(
  id INTEGER PRIMARY KEY,
  report_kind TEXT NOT NULL,
  report_hash TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN
    ('pending_approval','approved','rejected','sending','sent','partially_failed')),
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  decided_by TEXT,
  decided_at TEXT,
  sent_by TEXT,
  sent_at TEXT
);
CREATE TABLE IF NOT EXISTS outbox_messages(
  id INTEGER PRIMARY KEY,
  batch_id INTEGER NOT NULL REFERENCES outbox_batches(id),
  recipient_id INTEGER NOT NULL REFERENCES dissemination_recipients(id),
  channel TEXT NOT NULL,
  address TEXT NOT NULL,
  subject TEXT NOT NULL,
  text_body TEXT NOT NULL,
  html_body TEXT,
  status TEXT NOT NULL CHECK(status IN ('pending','sent','failed','skipped')),
  error_code TEXT,
  sent_at TEXT
);
CREATE TABLE IF NOT EXISTS dissemination_audit(
  id INTEGER PRIMARY KEY,
  batch_id INTEGER,
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  at TEXT NOT NULL,
  detail TEXT NOT NULL
);
"""


class InvalidRecipient(ValueError):
    """Người nhận không hợp lệ."""


class RecipientExists(RuntimeError):
    """Địa chỉ đã có trong danh sách."""


class RecipientNotFound(RuntimeError):
    """Không tìm thấy người nhận đang hoạt động."""


class OutboxNotFound(RuntimeError):
    """Không tìm thấy lô outbox."""


class OutboxStateError(RuntimeError):
    """Lô không ở trạng thái cho phép thao tác."""


class OutboxPolicyError(RuntimeError):
    """Vi phạm chính sách duyệt (ví dụ tự duyệt lô mình tạo)."""


class OutboxEmpty(RuntimeError):
    """Không có người nhận đang hoạt động để tạo outbox."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _stamp(clock: Callable[[], datetime]) -> str:
    return clock().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_recipient(display_name: object, channel: object, address: object) -> tuple[str, str, str]:
    if channel not in CHANNELS:
        raise InvalidRecipient("invalid channel")
    if not isinstance(display_name, str) or not isinstance(address, str):
        raise InvalidRecipient("invalid recipient")
    name = clean_text(display_name)
    if not 1 <= len(name) <= 120 or name != display_name.strip():
        raise InvalidRecipient("invalid display name")
    pattern = EMAIL_PATTERN if channel == "email" else TELEGRAM_PATTERN
    if len(address) > 254 or not pattern.fullmatch(address):
        raise InvalidRecipient("invalid address")
    return name, channel, address


def messages_hash(messages: list[Mapping[str, object]]) -> str:
    content = [
        [item["channel"], item["address"], item["subject"], item["text_body"], item["html_body"]]
        for item in messages
    ]
    raw = json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class DisseminationStore:
    """SQLite riêng cho danh sách nhận, outbox và audit gửi."""

    def __init__(
        self, path: str | Path, *, timeout: float = 5.0, clock: Callable[[], datetime] = _utc_now
    ) -> None:
        self.path = Path(path)
        self.timeout = timeout
        self.clock = clock

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def _audit(self, connection, batch_id, action: str, actor: str, detail: Mapping[str, object]) -> None:
        connection.execute(
            "INSERT INTO dissemination_audit(batch_id,action,actor,at,detail) VALUES(?,?,?,?,?)",
            (batch_id, action, actor, _stamp(self.clock), json.dumps(detail, sort_keys=True)),
        )

    # --- Danh sách nhận ---------------------------------------------------------------

    def add_recipient(self, display_name: object, channel: object, address: object, actor: str) -> dict:
        name, channel, address = validate_recipient(display_name, channel, address)
        key = address.casefold()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT id, active FROM dissemination_recipients WHERE channel=? AND address_key=?",
                (channel, key),
            ).fetchone()
            if row is not None and row["active"]:
                raise RecipientExists("recipient exists")
            if row is not None:
                connection.execute(
                    "UPDATE dissemination_recipients SET active=1, display_name=?, address=? WHERE id=?",
                    (name, address, row["id"]),
                )
                recipient_id = row["id"]
            else:
                recipient_id = connection.execute(
                    "INSERT INTO dissemination_recipients(display_name,channel,address,address_key,"
                    "created_by,created_at) VALUES(?,?,?,?,?,?)",
                    (name, channel, address, key, actor, _stamp(self.clock)),
                ).lastrowid
            self._audit(connection, None, "recipient_added", actor, {"recipient_id": recipient_id})
            connection.execute("COMMIT")
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {"id": recipient_id, "display_name": name, "channel": channel, "address": address}

    def list_recipients(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, display_name, channel, address FROM dissemination_recipients "
                "WHERE active=1 ORDER BY id LIMIT ?",
                (MAX_RECIPIENTS,),
            ).fetchall()
        return [dict(row) for row in rows]

    def deactivate_recipient(self, recipient_id: int, actor: str) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            changed = connection.execute(
                "UPDATE dissemination_recipients SET active=0 WHERE id=? AND active=1", (recipient_id,)
            ).rowcount
            if changed != 1:
                raise RecipientNotFound("recipient not found")
            self._audit(connection, None, "recipient_removed", actor, {"recipient_id": recipient_id})
            connection.execute("COMMIT")
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    # --- Outbox -----------------------------------------------------------------------

    def _render_for(self, report: Mapping[str, object], channel: str) -> RenderedMessage:
        variables = {
            "tenant_name": report["tenant_name"],
            "period_label": report["period_label"],
            "matched_cves": report["matched_cves"],
            "kev_cves": report["kev_cves"],
            "tlp": report["tlp"],
        }
        name = TEMPLATE_BY_CHANNEL[channel]
        if channel == "telegram":
            variables = {key: variables[key] for key in ("period_label", "matched_cves", "kev_cves")}
            return render_message(name, variables)
        return render_message(name, variables, email_rows(report))

    def create_batch(self, report: Mapping[str, object], actor: str) -> dict:
        """Tạo lô chờ duyệt cho mọi người nhận đang hoạt động; không gửi gì."""

        recipients = self.list_recipients()
        if not recipients:
            raise OutboxEmpty("no active recipients")
        messages = []
        for recipient in recipients:
            rendered = self._render_for(report, recipient["channel"])
            messages.append(
                {
                    "recipient_id": recipient["id"],
                    "channel": recipient["channel"],
                    "address": recipient["address"],
                    "subject": rendered.subject,
                    "text_body": rendered.text,
                    "html_body": rendered.html,
                }
            )
        content_hash = messages_hash(messages)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            batch_id = connection.execute(
                "INSERT INTO outbox_batches(report_kind,report_hash,content_hash,status,created_by,"
                "created_at) VALUES(?,?,?,'pending_approval',?,?)",
                (report["kind"], report["content_hash"], content_hash, actor, _stamp(self.clock)),
            ).lastrowid
            connection.executemany(
                "INSERT INTO outbox_messages(batch_id,recipient_id,channel,address,subject,text_body,"
                "html_body,status) VALUES(?,?,?,?,?,?,?,'pending')",
                [
                    (
                        batch_id,
                        item["recipient_id"],
                        item["channel"],
                        item["address"],
                        item["subject"],
                        item["text_body"],
                        item["html_body"],
                    )
                    for item in messages
                ],
            )
            self._audit(
                connection,
                batch_id,
                "outbox_created",
                actor,
                {"messages": len(messages), "hash": content_hash},
            )
            connection.execute("COMMIT")
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.get_batch(batch_id)

    def get_batch(self, batch_id: int) -> dict:
        with self._connect() as connection:
            batch = connection.execute("SELECT * FROM outbox_batches WHERE id=?", (batch_id,)).fetchone()
            if batch is None:
                raise OutboxNotFound("batch not found")
            messages = connection.execute(
                "SELECT id, channel, address, subject, text_body, html_body, status, error_code, sent_at "
                "FROM outbox_messages WHERE batch_id=? ORDER BY id",
                (batch_id,),
            ).fetchall()
        result = dict(batch)
        result["messages"] = [dict(row) for row in messages]
        return result

    def audit_entries(self, batch_id: int | None = None) -> list[dict]:
        with self._connect() as connection:
            if batch_id is None:
                rows = connection.execute("SELECT * FROM dissemination_audit ORDER BY id").fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM dissemination_audit WHERE batch_id=? ORDER BY id", (batch_id,)
                ).fetchall()
        return [dict(row) for row in rows]

    def decide(self, batch_id: int, actor: str, decision: str, expected_hash: str) -> dict:
        """Duyệt hoặc từ chối; người duyệt phải khác người tạo và đã xem đúng nội dung (hash)."""

        if decision not in {"approve", "reject"}:
            raise OutboxStateError("invalid decision")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            batch = connection.execute("SELECT * FROM outbox_batches WHERE id=?", (batch_id,)).fetchone()
            if batch is None:
                raise OutboxNotFound("batch not found")
            if batch["status"] != "pending_approval":
                raise OutboxStateError("batch not pending")
            if batch["created_by"] == actor:
                raise OutboxPolicyError("self approval not allowed")
            if batch["content_hash"] != expected_hash:
                raise OutboxStateError("content hash mismatch")
            status = "approved" if decision == "approve" else "rejected"
            connection.execute(
                "UPDATE outbox_batches SET status=?, decided_by=?, decided_at=? WHERE id=?",
                (status, actor, _stamp(self.clock), batch_id),
            )
            self._audit(connection, batch_id, f"outbox_{status}", actor, {"hash": expected_hash})
            connection.execute("COMMIT")
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.get_batch(batch_id)

    def _claim_for_send(self, batch_id: int, actor: str) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            batch = connection.execute("SELECT status FROM outbox_batches WHERE id=?", (batch_id,)).fetchone()
            if batch is None:
                raise OutboxNotFound("batch not found")
            if batch["status"] != "approved":
                raise OutboxStateError("batch not approved")
            connection.execute(
                "UPDATE outbox_batches SET status='sending', sent_by=? WHERE id=?", (actor, batch_id)
            )
            self._audit(connection, batch_id, "outbox_send_started", actor, {})
            connection.execute("COMMIT")
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def send_batch(self, batch_id: int, actor: str, senders: Mapping[str, MessageSender]) -> dict:
        """Gửi lô đã duyệt đúng một lần; kênh chưa có sender được đánh dấu skipped."""

        self._claim_for_send(batch_id, actor)
        batch = self.get_batch(batch_id)
        results = {"sent": 0, "failed": 0, "skipped": 0}
        with self._connect() as connection:
            for message in batch["messages"]:
                status, error = self._deliver(message, senders)
                results[status] += 1
                connection.execute(
                    "UPDATE outbox_messages SET status=?, error_code=?, sent_at=? WHERE id=?",
                    (status, error, _stamp(self.clock) if status == "sent" else None, message["id"]),
                )
            final = "sent" if results["failed"] == 0 and results["skipped"] == 0 else "partially_failed"
            connection.execute(
                "UPDATE outbox_batches SET status=?, sent_at=? WHERE id=?",
                (final, _stamp(self.clock), batch_id),
            )
            self._audit(connection, batch_id, "outbox_send_finished", actor, results)
        return self.get_batch(batch_id)

    @staticmethod
    def _deliver(
        message: Mapping[str, object], senders: Mapping[str, MessageSender]
    ) -> tuple[str, str | None]:
        sender = senders.get(message["channel"])
        if sender is None:
            return "skipped", "no_sender"
        try:
            sender.send(
                OutboundMessage(
                    channel=message["channel"],
                    address=message["address"],
                    subject=message["subject"],
                    text=message["text_body"],
                    html=message["html_body"],
                )
            )
        except SenderError:
            return "failed", "send_failed"
        return "sent", None
