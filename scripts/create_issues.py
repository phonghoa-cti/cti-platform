"""Tạo label, milestone và issue trên GitHub từ docs/backlog.json (dùng GitHub REST API qua `gh api`).

Cách dùng (cần cài GitHub CLI `gh` và đã chạy `gh auth login`):
    python scripts/create_issues.py --repo phonghoa-cti/cti-platform            # chạy thử, chỉ in ra
    python scripts/create_issues.py --repo phonghoa-cti/cti-platform --apply    # tạo thật

Mặc định chỉ "chạy thử". Chạy lại nhiều lần an toàn: label/milestone/issue đã có (trùng tên) sẽ được bỏ qua.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

BACKLOG = Path(__file__).resolve().parent.parent / "docs" / "backlog.json"


def api(path: str, method: str = "GET", fields: list[str] | None = None) -> object:
    """Gọi GitHub REST API qua `gh api`; mỗi field dạng "key=value"."""
    cmd = ["gh", "api", path, "--method", method]
    for f in fields or []:
        cmd += ["-f", f]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    return json.loads(out) if out.strip() else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="dạng owner/repo, ví dụ phonghoa-cti/cti-platform")
    parser.add_argument("--apply", action="store_true", help="tạo thật trên GitHub")
    args = parser.parse_args()
    data = json.loads(BACKLOG.read_text(encoding="utf-8"))
    repo = f"repos/{args.repo}"

    existing_labels = {lb["name"] for lb in api(f"{repo}/labels?per_page=100")} if args.apply else set()
    for label in data["labels"]:
        if label["name"] in existing_labels:
            continue
        print(("TẠO" if args.apply else "THỬ") + f" label: {label['name']}")
        if args.apply:
            api(f"{repo}/labels", "POST", [f"name={label['name']}", "color=1F6FEB"])

    milestones = {m["title"]: m["number"] for m in api(f"{repo}/milestones?state=all")} if args.apply else {}
    for ms in data["milestones"]:
        if ms["title"] in milestones:
            continue
        print(("TẠO" if args.apply else "THỬ") + f" milestone: {ms['title']} (hạn {ms['due']})")
        if args.apply:
            created = api(
                f"{repo}/milestones", "POST", [f"title={ms['title']}", f"due_on={ms['due']}T16:59:59Z"]
            )
            milestones[ms["title"]] = created["number"]

    existing_issues = set()
    if args.apply:
        existing_issues = {i["title"] for i in api(f"{repo}/issues?state=all&per_page=100")}
    for issue in data["issues"]:
        if issue["title"] in existing_issues:
            continue
        print(("TẠO" if args.apply else "THỬ") + f" issue [{issue['milestone']}]: {issue['title']}")
        if args.apply:
            subprocess.run(
                [
                    "gh", "api", f"{repo}/issues", "--method", "POST", "--silent",
                    "-f", f"title={issue['title']}",
                    "-f", f"body={issue['body']}",
                    "-f", f"labels[]={issue['label']}",
                    "-F", f"milestone={milestones[issue['milestone']]}",
                ],
                check=True,
            )  # fmt: skip

    if not args.apply:
        print("\nĐây mới là chạy thử. Đọc kỹ danh sách trên, rồi thêm --apply để tạo thật.")


if __name__ == "__main__":
    main()
