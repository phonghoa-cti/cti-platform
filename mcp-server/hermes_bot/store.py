"""Hàng chờ cục bộ. Duyệt là quyết định ghi nhận, không thực thi."""

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class Proposal:
    id: str
    chat_id: int
    requester_id: int
    kind: str
    target: str
    reason: str
    status: str
    created_at: str
    reviewer_id: int | None
    decided_at: str | None


SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    requester_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('block', 'extract_report')),
    target TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected')),
    created_at TEXT NOT NULL,
    reviewer_id INTEGER,
    decided_at TEXT,
    CHECK((status = 'pending' AND reviewer_id IS NULL AND decided_at IS NULL)
       OR (status != 'pending' AND reviewer_id IS NOT NULL AND decided_at IS NOT NULL))
)
"""


class ProposalStore:
    def __init__(self, path: Path):
        self.path = path
        with closing(self._connect()) as conn, conn:
            conn.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=3)

    def create(self, chat_id: int, requester_id: int, kind: str, target: str, reason: str) -> str:
        proposal_id = uuid4().hex
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO proposals VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, NULL, NULL)",
                (proposal_id, chat_id, requester_id, kind, target, reason, datetime.now(UTC).isoformat()),
            )
        return proposal_id

    def decide(self, proposal_id: str, chat_id: int, reviewer_id: int, decision: str) -> bool:
        if decision not in {"approved", "rejected"}:
            raise ValueError("Quyết định không hợp lệ")
        # UPDATE có điều kiện: chỉ đúng chat và đúng một lần chuyển từ pending.
        with closing(self._connect()) as conn, conn:
            result = conn.execute(
                "UPDATE proposals SET status=?, reviewer_id=?, decided_at=? "
                "WHERE id=? AND chat_id=? AND status='pending'",
                (decision, reviewer_id, datetime.now(UTC).isoformat(), proposal_id, chat_id),
            )
            return result.rowcount == 1

    def get(self, proposal_id: str) -> Proposal | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        return Proposal(*row) if row else None

    def count(self) -> int:
        with closing(self._connect()) as conn:
            return conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
