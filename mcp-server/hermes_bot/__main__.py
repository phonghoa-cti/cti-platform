"""Khởi động polling Telegram khi cấu hình đầy đủ."""

import logging
import os
from pathlib import Path

from .bot import HermesBot, build_application
from .config import Access
from .mcp_client import McpReader
from .store import ProposalStore


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    # HTTPX có thể ghi URL chứa token Telegram, không bật log request.
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    logging.getLogger("telegram").setLevel(logging.CRITICAL)
    try:
        if os.environ.get("PHONGHOA_MCP_SOURCE", "fixture") not in ("", "fixture"):
            raise ValueError("B11 chỉ hỗ trợ MCP fixture")
        access = Access.from_env(os.environ)
        token = os.environ["HERMES_TELEGRAM_TOKEN"]
        path = Path(os.environ["HERMES_TELEGRAM_DB"])
        if not token or not path.is_absolute() or not path.parent.is_dir() or path.suffix != ".sqlite":
            raise ValueError("Cần token và đường dẫn SQLite tuyệt đối")
        service = HermesBot(access, McpReader(), ProposalStore(path))
        app = build_application(token, service)
        app.run_polling(
            allowed_updates=["message", "callback_query"], drop_pending_updates=True, bootstrap_retries=0
        )
    except Exception:
        logging.error("Không thể khởi động hoặc chạy bot; kiểm tra cấu hình và kết nối.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
