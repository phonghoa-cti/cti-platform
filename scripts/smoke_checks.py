"""Đếm cổng smoke bằng dữ liệu có cấu trúc, không xuất nội dung log."""

import json
import re
import sys
from collections.abc import Iterable

# Chỉ dung sai lỗi transport đã nhận diện; lỗi import/không rõ luôn FAIL.
TRANSIENT = re.compile(
    r"^(?:[\w.]+\.)?(?:TimeoutError|ConnectTimeout|ReadTimeout|ConnectionResetError|"
    r"ConnectionRefusedError|ConnectTimeoutError|ReadTimeoutError):"
)


def count_alerts(lines: Iterable[str]) -> int:
    alerts = 0
    for line in lines:
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict) or not isinstance(obj.get("action"), str):
            raise ValueError("invalid intent")
        alerts += obj["action"] == "create_alert"
    return alerts


def count_worker_errors(lines: Iterable[str]) -> tuple[int, int]:
    errors = permanent = 0
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            obj = None
        if isinstance(obj, dict):
            if str(obj.get("level", "")).upper() != "ERROR":
                continue
            trace = str(obj.get("exc_info", "")).splitlines()
            transient = bool(trace and TRANSIENT.match(trace[-1].strip()))
        elif re.search(r"\bERROR\b", line):
            transient = False
        else:
            continue
        errors += 1
        permanent += not transient
    return errors, permanent


def main() -> int:
    try:
        if sys.argv[1:] == ["alerts"]:
            print(count_alerts(sys.stdin))
        elif sys.argv[1:] == ["worker"]:
            print(*count_worker_errors(sys.stdin))
        else:
            return 2
    except (ValueError, TypeError):
        # Không in raw log / payload / traceback.
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
