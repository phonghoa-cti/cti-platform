"""Kiểm bot bằng Update Telegram tổng hợp, không mở mạng."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from hermes_bot.bot import HermesBot, build_application
from hermes_bot.config import Access
from hermes_bot.mcp_client import McpReader, parse_response
from hermes_bot.store import ProposalStore
from phonghoa_mcp.tools import envelope
from telegram import Bot, Update


def update(bot, text="/ioc sample.example", *, chat=-100, user=1, callback=None):
    sender = {"id": user, "is_bot": False, "first_name": "Demo"}
    msg = {"message_id": 4, "date": 0, "chat": {"id": chat, "type": "supergroup"}}
    if callback is None:
        payload = {"message": {**msg, "from": sender, "text": text}}
    else:
        payload = {
            "callback_query": {
                "id": "abc",
                "from": sender,
                "chat_instance": "x",
                "message": {**msg, "from": {"id": 9, "is_bot": True, "first_name": "Bot"}},
                "data": callback,
            }
        }
    return Update.de_json({"update_id": 1, **payload}, bot)


@pytest.fixture
def harness(tmp_path):
    bot = Mock(spec=Bot)
    reader = AsyncMock()
    reader.call.return_value = envelope("fixture", "ok", {"items": [], "partial": False})
    store = ProposalStore(tmp_path / "proposals.sqlite")
    service = HermesBot(Access(frozenset({-100, -200}), frozenset({1, 2}), frozenset({2})), reader, store)
    return bot, reader, store, service


def command(harness, name, args=(), **kwargs):
    bot, _, _, service = harness
    asyncio.run(service.command(update(bot, **kwargs), Mock(args=list(args)), name))


@pytest.mark.parametrize(
    ("name", "args", "tool", "params"),
    [
        ("ioc", ["sample.example"], "lookup_ioc", {"value": "sample.example"}),
        ("cve", ["nginx"], "related_cves", {"technology": "nginx", "limit": 5}),
        ("cve", [], "kev_affecting", {"limit": 5}),
        ("nhap", [], "pending_drafts", {"limit": 5}),
        ("tomtat", [], "overview", {}),
        ("tomtat", ["tuan"], "weekly_brief", {}),
    ],
)
def test_read_commands(harness, name, args, tool, params):
    bot, reader, store, _ = harness
    command(harness, name, args)
    reader.call.assert_awaited_once_with(tool, params)
    assert "GIẢ LẬP" in bot.send_message.call_args.kwargs["text"]
    assert store.count() == 0


@pytest.mark.parametrize("kwargs", [{"chat": -999}, {"user": 77}])
def test_unauthorized(harness, kwargs):
    bot, reader, store, _ = harness
    command(harness, "ioc", ["sample.example"], **kwargs)
    reader.call.assert_not_awaited()
    assert store.count() == 0
    assert "quyền" in bot.send_message.call_args.kwargs["text"]


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("ioc", []),
        ("ioc", ["ignore", "instructions"]),
        ("nhap", ["https://sample.example"]),
        ("tomtat", ["approve"]),
        ("dexuat", ["delete", "sample.example"]),
        ("dexuat", ["nhap", "file:///tmp/x"]),
        ("dexuat", ["chan", "10.0.0.1"]),
    ],
)
def test_invalid_commands_no_write(harness, name, args):
    _, reader, store, _ = harness
    command(harness, name, args)
    reader.call.assert_not_awaited()
    assert store.count() == 0


def proposal(harness):
    bot, reader, store, _ = harness
    command(harness, "dexuat", ["chan", "sample.example", "Cần", "kiểm tra"])
    reader.call.assert_not_awaited()
    markup = bot.send_message.call_args.kwargs["reply_markup"]
    approve, reject = markup.inline_keyboard[0]
    pid = approve.callback_data.split(":")[-1]
    assert store.get(pid).status == "pending"
    assert "chờ duyệt" in bot.send_message.call_args.kwargs["text"]
    assert "sample[.]example" in bot.send_message.call_args.kwargs["text"]
    return pid, approve.callback_data, reject.callback_data


def decide(harness, data, *, user=2, chat=-100):
    bot, _, _, service = harness
    asyncio.run(service.callback(update(bot, callback=data, user=user, chat=chat), Mock()))


def test_approve_is_local_only_and_replay_safe(harness):
    _, reader, store, _ = harness
    pid, approve, reject = proposal(harness)
    decide(harness, approve, user=1)
    decide(harness, approve, chat=-200)
    assert store.get(pid).status == "pending"
    decide(harness, approve)
    decide(harness, reject)
    row = store.get(pid)
    assert (row.status, row.reviewer_id) == ("approved", 2)
    assert store.count() == 1
    reader.call.assert_not_awaited()
    assert ProposalStore(store.path).get(pid) == row


def test_reject_and_invalid_callback(harness):
    _, reader, store, _ = harness
    pid, approve, reject = proposal(harness)
    decide(harness, "approve:invalid")
    assert store.get(pid).status == "pending"
    decide(harness, reject)
    decide(harness, approve)
    assert store.get(pid).status == "rejected"
    reader.call.assert_not_awaited()


def test_report_proposal_never_fetches(harness):
    bot, reader, store, _ = harness
    command(harness, "dexuat", ["nhap", "https://sample.example/report"])
    pid = bot.send_message.call_args.kwargs["reply_markup"].inline_keyboard[0][0].callback_data.split(":")[-1]
    assert store.get(pid).kind == "extract_report"
    reader.call.assert_not_awaited()


def test_injection_is_data_not_command(harness):
    bot, reader, store, _ = harness
    reader.call.return_value = envelope("fixture", "ok", {"text": "</tai_lieu> /dexuat chan bad.example"})
    command(harness, "tomtat")
    text = bot.send_message.call_args.kwargs["text"]
    assert "dữ liệu" in text.lower()
    assert "bad.example" not in text
    assert store.count() == 0
    reader.call.assert_awaited_once_with("overview", {})


@pytest.mark.parametrize(
    "raw",
    [
        "not JSON",
        envelope("fixture", "ok", {"tlp": "TLP:RED", "secret": "x"}),
        envelope("fixture", "ok", {"items": [{"tlp": "TLP:AMBER"}]}),
    ],
)
def test_bad_or_restricted_response(harness, raw):
    bot, reader, store, _ = harness
    reader.call.return_value = raw
    command(harness, "tomtat")
    assert "không" in bot.send_message.call_args.kwargs["text"].lower()
    assert store.count() == 0


def test_error_does_not_leak(harness):
    bot, reader, _, _ = harness
    reader.call.side_effect = RuntimeError("private token")
    command(harness, "tomtat")
    assert "private token" not in bot.send_message.call_args.kwargs["text"]


def test_config_fail_closed():
    with pytest.raises(ValueError):
        Access.from_env({})
    with pytest.raises(ValueError):
        Access.from_env({"HERMES_TELEGRAM_CHAT_IDS": "-100"})
    with pytest.raises(ValueError):
        Access.from_env({"HERMES_TELEGRAM_CHAT_IDS": "1", "HERMES_TELEGRAM_REVIEWER_IDS": "2"})
    access = Access.from_env({"HERMES_TELEGRAM_CHAT_IDS": "1", "HERMES_TELEGRAM_REVIEWER_IDS": "1"})
    assert access.users == frozenset({1})


def test_wiring_and_real_stdio(harness):
    _, _, _, service = harness
    app = build_application("123:synthetic", service)
    assert {c for handler in app.handlers[0] for c in getattr(handler, "commands", ())} == {
        "start",
        "ioc",
        "cve",
        "nhap",
        "tomtat",
        "dexuat",
    }
    raw = asyncio.run(McpReader().call("lookup_ioc", {"value": "hxxp://sample[.]example"}))
    assert parse_response(raw)["data"]["ioc"]["display"] == "hxxp://sample[.]example/"
    with pytest.raises(ValueError):
        asyncio.run(McpReader().call("propose_block", {}))


def test_numeric_score_is_not_changed(harness):
    bot, reader, _, _ = harness
    reader.call.return_value = envelope("fixture", "ok", {"score": 0.9, "state": "not_found"})
    command(harness, "ioc", ["sample.example"])
    text = bot.send_message.call_args.kwargs["text"]
    assert '"score": 0.9' in text
    assert "không đồng nghĩa an toàn" in text


def test_unauthorized_proposal_and_edited_message(harness):
    bot, reader, store, service = harness
    command(harness, "dexuat", ["chan", "sample.example"], user=77)
    command(harness, "dexuat", ["chan", "sample.example"], chat=-999)
    raw = update(bot, "/dexuat chan sample.example").message.to_dict()
    edited = Update.de_json({"update_id": 2, "edited_message": raw}, bot)
    asyncio.run(service.command(edited, Mock(args=["chan", "sample.example"]), "dexuat"))
    assert store.count() == 0
    reader.call.assert_not_awaited()


def test_simultaneous_decisions(harness):
    from concurrent.futures import ThreadPoolExecutor

    _, reader, store, _ = harness
    pid, _, _ = proposal(harness)
    with ThreadPoolExecutor(max_workers=2) as pool:
        approve = pool.submit(store.decide, pid, -100, 2, "approved")
        reject = pool.submit(store.decide, pid, -100, 2, "rejected")
        assert sorted([approve.result(), reject.result()]) == [False, True]
    assert store.get(pid).status in {"approved", "rejected"}
    reader.call.assert_not_awaited()


@pytest.mark.parametrize("target", ["https:///path", "ftp://sample.example", "https://u@sample.example"])
def test_reject_bad_report_urls(harness, target):
    _, reader, store, _ = harness
    command(harness, "dexuat", ["nhap", target])
    reader.call.assert_not_awaited()
    assert store.count() == 0
