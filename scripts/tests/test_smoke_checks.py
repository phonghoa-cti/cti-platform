"""Cổng smoke: chỉ đếm alert thật và không che lỗi import."""

import pytest

from scripts.smoke_checks import count_alerts, count_worker_errors


def test_alerts_count_actual_intent():
    assert count_alerts(['{"action":"create_alert"}', '{"action": "log"}']) == 1
    assert count_alerts(['{"action":"log","details":{"action":"create_alert"}}']) == 0
    assert count_alerts(['{"action":"alert"}']) == 0


@pytest.mark.parametrize("line", ["not JSON", "[]", "{}", '{"action":42}'])
def test_bad_playbook_output_fails(line):
    with pytest.raises(ValueError):
        count_alerts([line])


def test_worker_counts_only_error_records():
    lines = [
        '{"level":"INFO","message":"ERROR was mentioned"}',
        '{"level":"ERROR","message":"failed","exc_info":"Traceback\\nValueError: Name X not found"}',
        '{"level":"ERROR","message":"failed","exc_info":"Traceback\\nTimeoutError: timed out"}',
        '{"level":"WARNING","message":"retrying"}',
    ]
    assert count_worker_errors(lines) == (2, 1)


def test_worker_unknown_error_is_not_transient():
    assert count_worker_errors(["ERROR unexpected failure"]) == (1, 1)
    assert count_worker_errors(['{"level":"ERROR","message":"timeout word only"}']) == (1, 1)
