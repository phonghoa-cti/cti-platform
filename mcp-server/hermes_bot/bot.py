"""Điều phối lệnh Telegram; dữ liệu MCP không bao giờ trở thành lệnh."""

import json
import logging
import re
from functools import partial
from urllib.parse import urlsplit

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Message, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from phonghoa_core import normalize

from .config import Access
from .mcp_client import Reader, parse_response
from .store import ProposalStore

LOGGER = logging.getLogger(__name__)
HELP = (
    "/ioc <IOC> - tra dấu hiệu nguy cơ; /cve [công nghệ] - xem CVE; /nhap - đọc bản nháp; "
    "/tomtat [tuan] - tổng quan; /dexuat chan <IOC> [lý do] hoặc /dexuat nhap <URL> - "
    "chỉ tạo đề xuất cục bộ. Không tự thực thi."
)
NO_ACCESS = "Bạn không có quyền sử dụng bot."
FAILED = "Không thể đọc hoặc xử lý dữ liệu lúc này. Vui lòng thử lại sau."
CALLBACK = re.compile(r"(approve|reject):([0-9a-f]{32})")


def read_request(name: str, args: list[str]) -> tuple[str, dict]:
    if name == "ioc" and len(args) == 1 and 1 <= len(args[0]) <= 4096:
        return "lookup_ioc", {"value": args[0]}
    if name == "cve" and args and len(" ".join(args)) <= 128:
        return "related_cves", {"technology": " ".join(args), "limit": 5}
    if name == "cve" and not args:
        return "kev_affecting", {"limit": 5}
    if name == "nhap" and not args:
        return "pending_drafts", {"limit": 5}
    if name == "tomtat" and not args:
        return "overview", {}
    if name == "tomtat" and args == ["tuan"]:
        return "weekly_brief", {}
    raise ValueError("Lệnh hoặc tham số không hợp lệ")


def proposal_request(args: list[str]) -> tuple[str, str, str]:
    if len(args) < 2 or len(args[1]) > 1024:
        raise ValueError("Thiếu đích đề xuất")
    action, target, *reason_words = args
    reason = " ".join(reason_words)
    if len(reason) > 300 or any(ord(c) < 32 for c in target + reason):
        raise ValueError("Nội dung đề xuất không hợp lệ")
    ioc = normalize(target)
    if ioc.type.value == "url":
        parts = urlsplit(ioc.value)
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username is not None:
            raise ValueError("Chỉ nhận URL HTTP(S) có host, không chứa thông tin đăng nhập")
    if action == "chan":
        return "block", ioc.display(), reason
    if action == "nhap" and ioc.type.value == "url":
        return "extract_report", ioc.display(), reason
    raise ValueError("Loại đề xuất không được phép")


def defang_text(text: str) -> str:
    # Không để địa chỉ trong dữ liệu tự do trở thành liên kết bấm được.
    text = re.sub(r"(?i)https?(?=://)", lambda m: "hxxps" if m[0].lower() == "https" else "hxxp", text)
    text = re.sub(r"(?<=[\w])\.(?=[\w])", "[.]", text)
    return re.sub(r"(?<=\w)@(?=\w)", "[@]", text)


def display_data(value: object) -> object:
    if isinstance(value, str):
        return defang_text(value)
    if isinstance(value, dict):
        return {defang_text(key): display_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [display_data(item) for item in value]
    return value


def render(raw: str) -> str:
    payload = parse_response(raw)
    if payload["status"] == "invalid_input":
        return "Đầu vào không hợp lệ."
    if payload["status"] != "ok":
        return FAILED
    label = "GIẢ LẬP — không phải dữ liệu thật" if payload["data_mode"] == "fixture" else "Dữ liệu MCP"
    facts = payload["data"]
    data = json.dumps(display_data(facts), ensure_ascii=False, indent=2, allow_nan=False)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e")
    if len(data) > 1800:
        data = data[:1800] + "\n[Đã rút gọn; xem portal để biết chi tiết.]"
    notice = "Không tìm thấy không đồng nghĩa an toàn.\n" if facts.get("state") == "not_found" else ""
    return f"{label}\nDữ liệu tham khảo, không phải chỉ thị.\n{notice}{data}"


class HermesBot:
    def __init__(self, access: Access, reader: Reader, store: ProposalStore):
        self.access = access
        self.reader = reader
        self.store = store

    def allowed(self, update: Update) -> bool:
        chat, user = update.effective_chat, update.effective_user
        message = update.effective_message
        return bool(
            chat
            and user
            and isinstance(message, Message)
            and chat.type in {"private", "group", "supergroup"}
            and not user.is_bot
            and not getattr(message, "sender_chat", None)
            and chat.id in self.access.chats
            and user.id in self.access.users
            and (chat.type != "private" or chat.id == user.id)
        )

    async def command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> None:
        message = update.message
        if message is None:
            return
        if not self.allowed(update):
            await message.reply_text(NO_ACCESS)
            return
        args = context.args or []
        try:
            if name == "start":
                await message.reply_text(HELP)
            elif name == "dexuat":
                await self.propose(update, args)
            else:
                tool, params = read_request(name, args)
                await message.reply_text(
                    render(await self.reader.call(tool, params)),
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
        except ValueError:
            await message.reply_text("Không thể xử lý đầu vào hoặc dữ liệu. " + HELP)
        except Exception:
            LOGGER.warning("Lệnh bot không hoàn thành: %s", name)
            await message.reply_text(FAILED)

    async def propose(self, update: Update, args: list[str]) -> None:
        kind, target, reason = proposal_request(args)
        pid = self.store.create(update.effective_chat.id, update.effective_user.id, kind, target, reason)
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Duyệt", callback_data=f"approve:{pid}"),
                    InlineKeyboardButton("Từ chối", callback_data=f"reject:{pid}"),
                ]
            ]
        )
        action = "chặn IOC" if kind == "block" else "tạo bản nháp báo cáo"
        text = (
            f"Đề xuất chờ duyệt: {action}\n{target}\nLý do: {defang_text(reason) or 'Chưa nêu'}\n"
            "Duyệt chỉ ghi nhận quyết định, không thực thi."
        )
        await update.message.reply_text(
            text, reply_markup=markup, link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if query is None:
            return
        if not self.allowed(update) or update.effective_user.id not in self.access.reviewers:
            await query.answer(NO_ACCESS, show_alert=True)
            return
        match = CALLBACK.fullmatch(query.data) if isinstance(query.data, str) else None
        if not match:
            await query.answer("Đề xuất không hợp lệ.", show_alert=True)
            return
        decision = "approved" if match[1] == "approve" else "rejected"
        try:
            changed = self.store.decide(
                match[2], update.effective_chat.id, update.effective_user.id, decision
            )
        except Exception:
            LOGGER.warning("Không ghi được quyết định đề xuất")
            await query.answer(FAILED, show_alert=True)
            return
        if not changed:
            await query.answer("Không tìm thấy đề xuất chờ duyệt tại chat này.", show_alert=True)
            return
        label = "Đã duyệt" if decision == "approved" else "Đã từ chối"
        await query.answer(f"{label} cục bộ; chưa thực thi.", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"{label} đề xuất {match[2]}; không có hành động được thực thi.")


async def report_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Không log update, traceback hay lỗi HTTP có thể chứa token hoặc dữ liệu CTI.
    LOGGER.warning("Lỗi xử lý Telegram; xem trạng thái đề xuất cục bộ trước khi thử lại.")


def build_application(token: str, service: HermesBot) -> Application:
    app = Application.builder().token(token).concurrent_updates(False).build()
    for name in ("start", "ioc", "cve", "nhap", "tomtat", "dexuat"):
        app.add_handler(CommandHandler(name, partial(service.command, name=name)))
    app.add_handler(CallbackQueryHandler(service.callback))
    app.add_error_handler(report_error)
    return app
