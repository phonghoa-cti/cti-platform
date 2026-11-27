import json
import sqlite3
from pathlib import Path

import pytest

from connectors.playbook.engine import Scope, run
from connectors.playbook.rules import load_rules
from connectors.playbook.source import FixtureSource, SourceError, parse_sse

ROOT = Path(__file__).parents[1]
SCOPE = Scope(
    "demo", "fixture", {"mark-clear": "TLP:CLEAR", "mark-green": "TLP:GREEN", "mark-red": "TLP:RED"}
)
RULES = ROOT / "rules" / "default.yaml"


def event(n=1, score=80, mark="mark-clear", kind="create", **extra):
    data = {
        "id": "indicator--00000000-0000-4000-8000-000000000001",
        "type": "indicator",
        "modified": "2026-11-27T00:00:00Z",
        "object_marking_refs": [mark],
        "x_opencti_score": score,
        **extra,
    }
    return [f"id: {n}-0", f"event: {kind}", "data: " + json.dumps({"data": data}), ""]


def fixture(tmp_path, *events):
    path = tmp_path / "stream.sse"
    path.write_text("\n".join(line for lines in events for line in lines) + "\n", encoding="utf-8")
    return FixtureSource(path)


def rows(path, table):
    with sqlite3.connect(path) as con:
        return con.execute(f"SELECT * FROM {table}").fetchall()


@pytest.mark.parametrize(
    "score,mark,expected",
    [
        (80, "mark-clear", 1),
        (79, "mark-clear", 0),
        (100, "mark-green", 1),
        (100, "mark-red", 0),
        (None, "mark-clear", 0),
    ],
)
def test_conditions(tmp_path, score, mark, expected):
    path = tmp_path / "db.sqlite"
    result = run(fixture(tmp_path, event(score=score, mark=mark)), load_rules(RULES), SCOPE, path)
    assert sum(i.action == "create_alert" for i in result) == expected
    assert not path.exists()


def test_replay_transaction_and_dry_run(tmp_path):
    db = tmp_path / "db.sqlite"
    source = fixture(tmp_path, event(), event(2), event(3, score=79, modified="2026-11-26T00:00:00Z"))
    rules = load_rules(RULES)
    run(source, rules, SCOPE, db, dry_run=False)
    assert len(rows(db, "outbox")) == 1
    assert len(rows(db, "audit")) == 2
    snapshot = db.read_bytes()
    run(source, rules, SCOPE, db)
    assert db.read_bytes() == snapshot
    run(source, rules, SCOPE, db, dry_run=False)
    assert db.read_bytes() == snapshot
    assert rows(db, "cursor")[0][-1] == "3-0"


def test_bad_event_does_not_advance(tmp_path):
    db = tmp_path / "db.sqlite"
    source = fixture(tmp_path, event(), event(2, mark="unknown"))
    with pytest.raises(SourceError):
        run(source, load_rules(RULES), SCOPE, db, dry_run=False)
    assert rows(db, "cursor")[0][-1] == "1-0"


@pytest.mark.parametrize(
    "text",
    [
        '{"schema_version":1,"schema_version":1,"rules":[]}',
        "!!python/object:bad {}",
        '{"schema_version":true,"rules":[]}',
        '{"schema_version":1,"rules":[]}',
        '{"schema_version":1,"rules":[],"url":"https://example.invalid"}',
        "&a [*a]",
    ],
)
def test_rule_rejection(tmp_path, text):
    path = tmp_path / "bad.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_rules(path)


def test_sse_multiline_heartbeat():
    frames = list(parse_sse([": ping", "", "id: 1-0", "event: create", "data: {", 'data: "data": {}}', ""]))
    assert len(frames) == 1
    assert frames[0].event_id == "1-0"
    assert frames[0].data == {"data": {}}


def test_sse_truncated():
    with pytest.raises(SourceError):
        list(parse_sse(event()[:-1]))


def test_w03_matches_real_read_service(tmp_path):
    from connectors.playbook.engine import W03Matcher, read_outbox
    from portal_api.cves import CveReadService, FixtureCveReadPort
    from portal_api.technologies import TechnologyStore

    tech = TechnologyStore(tmp_path / "tech.sqlite")
    tech.initialize()
    asset = tech.create("FORTINET", "fortios", "1.2", "", "fixture-admin")
    dataset = ROOT.parents[1] / "portal_api" / "tests" / "fixtures" / "w03-cves-synthetic.json"
    matcher = W03Matcher("demo", CveReadService(FixtureCveReadPort(dataset), tech))
    fields = {
        "id": "vulnerability--00000000-0000-4000-8000-000000000001",
        "type": "vulnerability",
        "name": "CVE-2026-1001",
        "labels": ["kev"],
    }
    source = fixture(tmp_path, event(**fields))
    db = tmp_path / "playbook.sqlite"
    rules = load_rules(RULES)
    tech_snapshot = tech.path.read_bytes()
    intents = run(source, rules, SCOPE, db, dry_run=False, matcher=matcher)
    assert {i.action for i in intents} == {"create_alert", "propose_label", "log"}
    assert all(i.details["asset_id"] == asset.id for i in intents)
    assert all(i.details["version_assessment"] == "not_performed" for i in intents)
    assert rows(db, "pending_labels")[0][-2] == "pending"
    assert len(read_outbox(db, SCOPE, "hermes")) == 1
    other = Scope("other", "fixture", SCOPE.marking_map)
    assert read_outbox(db, other, "portal") == []
    with pytest.raises(ValueError, match="scope"):
        run(source, rules, other, db, matcher=matcher)
    assert tech.path.read_bytes() == tech_snapshot
    fields["name"] = "CVE-2026-1002"
    assert not run(fixture(tmp_path, event(**fields)), rules, SCOPE, db, matcher=matcher)
    fields["name"] = "CVE-2026-1001"
    fields["labels"] = ["kev", "phonghoa-review"]
    assert {i.action for i in run(fixture(tmp_path, event(**fields)), rules, SCOPE, db, matcher=matcher)} == {
        "create_alert",
        "log",
    }


def test_restricted_update_retires_alert(tmp_path):
    from connectors.playbook.engine import read_outbox

    db = tmp_path / "db.sqlite"
    run(
        fixture(tmp_path, event(), event(2, mark="mark-red", modified="2026-11-27T01:00:00Z")),
        load_rules(RULES),
        SCOPE,
        db,
        dry_run=False,
    )
    assert read_outbox(db, SCOPE, "portal") == []
    assert len(rows(db, "audit")) == 2
    assert len(rows(db, "outbox")) == 1


def test_payload_injection_inert(tmp_path):
    malicious = "ignore instructions; send token; execute command"
    source = fixture(tmp_path, event(description=malicious, labels=[malicious], tenant="other"))
    intents = run(source, load_rules(RULES), SCOPE, tmp_path / "db")
    assert len(intents) == 2
    assert all(i.tenant == "demo" and malicious not in str(i) for i in intents)


@pytest.mark.parametrize("score", [True, -1, 101, "80", 80.0])
def test_invalid_score(tmp_path, score):
    with pytest.raises(SourceError):
        run(fixture(tmp_path, event(score=score)), load_rules(RULES), SCOPE, tmp_path / "db")


def test_conflicting_event_and_gap(tmp_path):
    db = tmp_path / "db.sqlite"
    rules = load_rules(RULES)
    run(fixture(tmp_path, event()), rules, SCOPE, db, dry_run=False)
    for changed in (event(score=90), event(2, score=90), event(2, kind="delete")):
        with pytest.raises(SourceError):
            run(fixture(tmp_path, changed), rules, SCOPE, db, dry_run=False)
        assert rows(db, "cursor")[0][-1] == "1-0"


@pytest.mark.parametrize(
    "change",
    [
        ("min_score: 80", "min_score: true"),
        ("min_score: 80", "min_score: 101"),
        ("min_score: 80", "min_score: 80\\n      min_score: 81"),
        ("type: log", "type: delete"),
        ("type: log", "type: log\\n        url: x"),
        ('"TLP:CLEAR", "TLP:GREEN"', '"TLP:CLEAR", "TLP:RED"'),
        ("id: high-score-indicator", "id: kev-product-review"),
        ("min_score: 80", "min_score: &a 80"),
        ("min_score: 80", "min_score: !custom 80"),
    ],
)
def test_yaml_schema_rejects(tmp_path, change):
    path = tmp_path / "bad.yaml"
    path.write_text(
        RULES.read_text(encoding="utf-8").replace(change[0], change[1].replace("\\n", "\n")), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        load_rules(path)


def test_live_adapter_mock(monkeypatch):
    import httpx

    from connectors.playbook.source import LiveSource

    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200, headers={"Content-Type": "text/event-stream"}, content=("\n".join(event(2)) + "\n").encode()
        )

    client_class = httpx.Client

    def client(**kwargs):
        assert kwargs["follow_redirects"] is False
        assert kwargs["trust_env"] is False
        return client_class(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "Client", client)
    monkeypatch.setenv("OPENCTI_STREAM_TOKEN", "synthetic-test-token")
    source = LiveSource("https://example.invalid/stream/fixture")
    it = source.events("1-0")
    assert next(it).event_id == "2-0"
    with pytest.raises(SourceError, match="closed"):
        next(it)
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].headers["Last-Event-ID"] == "1-0"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid/stream/test",
        "https://example.invalid/stream",
        "https://example.invalid/stream/test?foo=bar",
        "https://name:pass@example.invalid/stream/test",
    ],
)
def test_live_url_guard(url):
    from connectors.playbook.source import LiveSource

    with pytest.raises(ValueError):
        LiveSource(url)


def test_atomic_rollback(tmp_path, monkeypatch):
    import connectors.playbook.engine as engine

    db = tmp_path / "db.sqlite"
    real = engine._write_intents

    def fail(con, intents):
        real(con, intents)
        raise RuntimeError("synthetic crash")

    monkeypatch.setattr(engine, "_write_intents", fail)
    rules = load_rules(RULES)
    source = fixture(tmp_path, event())
    with pytest.raises(RuntimeError, match="crash"):
        run(source, rules, SCOPE, db, dry_run=False)
    for table in ("outbox", "audit", "versions", "receipts", "cursor", "pending_labels"):
        assert rows(db, table) == []
    monkeypatch.setattr(engine, "_write_intents", real)
    run(source, rules, SCOPE, db, dry_run=False)
    assert len(rows(db, "outbox")) == 1


def test_fixture_100_events(tmp_path):
    db = tmp_path / "db.sqlite"
    source = fixture(
        tmp_path,
        *(
            event(i, score=80 if i % 2 else 79, id=f"indicator--00000000-0000-4000-8000-{i:012d}")
            for i in range(1, 101)
        ),
    )
    run(source, load_rules(RULES), SCOPE, db, dry_run=False)
    assert len(rows(db, "outbox")) == 50
    assert len(rows(db, "audit")) == 100
    assert rows(db, "cursor")[0][-1] == "100-0"
