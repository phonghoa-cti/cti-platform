#!/usr/bin/env bash
# Smoke test lab OpenCTI + portal_api + playbook. Chạy trong Ubuntu/WSL từ gốc repo: make smoke
# Biến: DEMO_DIR (thư mục deploy/demo đang chạy, có .env), PYTHON (python có dependency API).
# Không in secret: mật khẩu admin chỉ được đọc trong tiến trình Python.
set -uo pipefail
cd "$(dirname "$0")/.."
DEMO_DIR="${DEMO_DIR:-$HOME/phonghoa/cti-platform/deploy/demo}"
PYTHON="${PYTHON:-.venv/bin/python}"
PROJECT="${COMPOSE_PROJECT:-phonghoa-f01-demo}"
FAILS=0

result() { # $1=PASS|FAIL $2=mô tả
  echo "$1 $2"
  [ "$1" = PASS ] || FAILS=$((FAILS + 1))
}

if [ ! -f "$DEMO_DIR/.env" ]; then
  echo "FAIL không thấy $DEMO_DIR/.env (đặt DEMO_DIR)"
  exit 1
fi

# 1. Container của project: running, healthcheck (nếu có) phải healthy.
states=$(docker ps -a --filter "label=com.docker.compose.project=$PROJECT" \
  --format '{{.Label "com.docker.compose.service"}} {{.State}} {{.Status}}')
bad=$(echo "$states" | awk '$2 != "running" || /unhealthy|health: starting/' | sort -u)
if [ -n "$states" ] && [ -z "$bad" ]; then
  result PASS "stack: $(echo "$states" | wc -l) container running/healthy"
else
  result FAIL "stack: ${bad:-không có container}"
fi

# 2. HTTP loopback.
port=$(sed -n 's/^OPENCTI_PORT=//p' "$DEMO_DIR/.env" | tr -d '"'"'"'\r')
port="${port:-8080}"
if ! [[ "$port" =~ ^[0-9]{1,5}$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
  echo "FAIL OPENCTI_PORT không hợp lệ"
  exit 1
fi
code=$(curl --noproxy '*' -s -o /dev/null -m 15 -w '%{http_code}' "http://127.0.0.1:$port/")
[ "$code" = 200 ] && result PASS "HTTP 127.0.0.1:$port -> 200" || result FAIL "HTTP 127.0.0.1:$port -> $code"

# 3-4. Đăng nhập admin, me, số Attack-Pattern / Vulnerability.
kev_running=$(docker ps --filter "label=com.docker.compose.project=$PROJECT" \
  --filter "label=com.docker.compose.service=connector-cisa-kev" -q | head -1)
if api_out=$(python3 - "$DEMO_DIR/.env" "$port" "${kev_running:+1}" 2>/dev/null <<'PY'
import http.cookiejar, json, sys, urllib.request

env = {}
for raw in open(sys.argv[1], encoding="utf-8"):
    raw = raw.strip()
    if raw and not raw.startswith("#") and "=" in raw:
        key, value = raw.split("=", 1)
        env[key] = value.strip().strip("\"'")
url = f"http://127.0.0.1:{sys.argv[2]}/graphql"
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def gql(query, variables=None):
    request = urllib.request.Request(
        url, json.dumps({"query": query, "variables": variables or {}}).encode(), {"Content-Type": "application/json"}
    )
    return json.load(opener.open(request, timeout=30))


try:
    login = gql(
        "mutation Login($i: UserLoginInput!) { token(input: $i) }",
        {"i": {"email": env.get("OPENCTI_ADMIN_EMAIL", ""), "password": env.get("OPENCTI_ADMIN_PASSWORD", "")}},
    )
    me = (gql("{ me { user_email } }").get("data") or {}).get("me") or {}
except Exception as exc:  # noqa: BLE001
    print(f"FAIL đăng nhập API: {type(exc).__name__}")
    sys.exit(0)
if not login.get("errors") and me.get("user_email") == env.get("OPENCTI_ADMIN_EMAIL"):
    print("PASS đăng nhập API admin, me khớp email")
else:
    print("FAIL đăng nhập API admin / me không khớp")
    sys.exit(0)
data = gql(
    "{ ap: attackPatterns { pageInfo { globalCount } } vu: vulnerabilities { pageInfo { globalCount } } }"
)["data"]
ap, vu = data["ap"]["pageInfo"]["globalCount"], data["vu"]["pageInfo"]["globalCount"]
print(f"{'PASS' if ap > 0 else 'FAIL'} Attack-Pattern = {ap}")
if len(sys.argv) > 3 and sys.argv[3]:
    print(f"{'PASS' if vu > 0 else 'FAIL'} Vulnerability = {vu} (KEV đang bật)")
else:
    print(f"PASS Vulnerability = {vu} (KEV chưa bật, không bắt buộc)")
PY
); then
  if [ -z "$api_out" ]; then
    result FAIL "GraphQL: không có kết quả"
  else
    while read -r line; do
      [ -n "$line" ] && result "${line%% *}" "${line#* }"
    done <<< "$api_out"
  fi
else
  result FAIL "GraphQL: tiến trình kiểm tra lỗi"
fi

# 5. Worker: tối đa 3 lỗi transport nhất thời/5 phút cho cả stack.
# Lỗi import, lỗi không rõ nguyên nhân, hoặc không đọc được log luôn FAIL;
# 3 là ngân sách nhỏ cho gián đoạn kết nối đơn lẻ, không phải SLA production.
workers=$(docker ps --filter "label=com.docker.compose.project=$PROJECT" \
  --filter "label=com.docker.compose.service=worker" -q)
if [ -z "$workers" ]; then
  result FAIL "worker: không có container"
else
  errors=0
  permanent=0
  log_ok=1
  for id in $workers; do
    if counts=$(docker logs --since 5m "$id" 2>&1 | "$PYTHON" scripts/smoke_checks.py worker); then
      read -r n p <<< "$counts"
      if [[ "$n" =~ ^[0-9]+$ && "$p" =~ ^[0-9]+$ ]]; then
        errors=$((errors + n))
        permanent=$((permanent + p))
      else
        log_ok=0
      fi
    else
      log_ok=0
    fi
  done
  if [ "$log_ok" -ne 1 ]; then
    result FAIL "worker: không đọc/đếm được log"
  elif [ "$permanent" -eq 0 ] && [ "$errors" -le 3 ]; then
    result PASS "worker: $errors ERROR/5 phút, 0 lỗi không dung sai (tối đa 3 lỗi transport)"
  else
    result FAIL "worker: $errors ERROR/5 phút, $permanent lỗi không dung sai (tối đa 3 lỗi transport)"
  fi
fi

# 6. portal_api khởi động, /api/cves 200 (fixture W03 tổng hợp).
if line=$("$PYTHON" scripts/smoke_portal_api.py 2>/dev/null) && [[ "$line" =~ ^PASS\ portal_api\ /api/cves\ HTTP\ 200 ]]; then
  result PASS "portal_api /api/cves HTTP 200"
else
  result FAIL "portal_api: không xác nhận được HTTP 200"
fi

# 7. Playbook dry-run trên fixture: đúng 1 intent create_alert; intent log không phải cảnh báo.
if alerts=$(PYTHONPATH=.:core:extractor "$PYTHON" -m connectors.playbook 2>/dev/null | "$PYTHON" scripts/smoke_checks.py alerts); then
  [ "$alerts" -eq 1 ] && result PASS "playbook dry-run: 1 cảnh báo" || result FAIL "playbook dry-run: $alerts cảnh báo"
else
  result FAIL "playbook dry-run: CLI/JSON không hợp lệ"
fi

echo "---"
[ "$FAILS" -eq 0 ] && { echo "SMOKE PASS"; exit 0; }
echo "SMOKE FAIL ($FAILS mục)"
exit 1
