"""Cấu hình truy cập từ env, mặc định từ chối."""

from collections.abc import Mapping
from dataclasses import dataclass


def ids(raw: str, *, positive: bool = False) -> frozenset[int]:
    if not raw:
        return frozenset()
    values = frozenset(int(item.strip()) for item in raw.split(","))
    if any(value == 0 or abs(value) >= 2**52 or (positive and value < 0) for value in values):
        raise ValueError("ID Telegram không hợp lệ")
    return values


@dataclass(frozen=True)
class Access:
    chats: frozenset[int]
    users: frozenset[int]
    reviewers: frozenset[int]

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Access":
        chats = ids(env.get("HERMES_TELEGRAM_CHAT_IDS", ""))
        users = ids(env.get("HERMES_TELEGRAM_USER_IDS", ""), positive=True)
        if not users and all(chat > 0 for chat in chats):
            users = chats
        reviewers = ids(env.get("HERMES_TELEGRAM_REVIEWER_IDS", ""), positive=True)
        if not chats or not users or not reviewers <= users:
            raise ValueError("Cần allowlist chat/user hợp lệ; reviewer phải thuộc user allowlist")
        return cls(chats, users, reviewers)
