"""Tạo label, milestone và issue trên GitHub từ docs/backlog.json.

Cách dùng (cần cài GitHub CLI `gh` và đã chạy `gh auth login`):
    python scripts/create_issues.py --repo phonghoa-cti/cti-platform            # chạy thử, chỉ in ra
    python scripts/create_issues.py --repo phonghoa-cti/cti-platform --apply    # tạo thật

Mặc định chỉ "chạy thử" để bạn đọc trước những gì sẽ được tạo — nên luôn chạy thử trước.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

BACKLOG = Path(__file__).resolve().parent.parent / "docs" / "backlog.json"


def run(cmd: list[str], apply: bool) -> None:
    print(("CHẠY: " if apply else "THỬ:  ") + " ".join(cmd))
    if apply:
        subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="dạng owner/repo, ví dụ phonghoa-cti/cti-platform")
    parser.add_argument("--apply", action="store_true", help="tạo thật trên GitHub")
    args = parser.parse_args()
    data = json.loads(BACKLOG.read_text(encoding="utf-8"))

    for label in data["labels"]:
        run(["gh", "label", "create", label["name"], "--repo", args.repo, "--force"], args.apply)

    for ms in data["milestones"]:
        run(
            [
                "gh", "api", f"repos/{args.repo}/milestones",
                "-f", f"title={ms['title']}",
                "-f", f"due_on={ms['due']}T16:59:59Z",  # 23:59 giờ Việt Nam
            ],
            args.apply,
        )  # fmt: skip

    for issue in data["issues"]:
        run(
            [
                "gh", "issue", "create", "--repo", args.repo,
                "--title", issue["title"],
                "--body", issue["body"],
                "--label", issue["label"],
                "--milestone", issue["milestone"],
            ],
            args.apply,
        )  # fmt: skip

    if not args.apply:
        print("\nĐây mới là chạy thử. Đọc kỹ danh sách trên, rồi thêm --apply để tạo thật.")


if __name__ == "__main__":
    main()
