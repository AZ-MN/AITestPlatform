#!/bin/bash
# ========================================================
# 一键停止脚本 (Linux/macOS)
# 使用方式：chmod +x stop.sh && ./stop.sh
# ========================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="$ROOT_DIR/.run/aitestplatform-unix.env"

stop_pid() {
    local pid="$1"

    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
        kill "$pid" >/dev/null 2>&1 || true
        return 0
    fi

    return 1
}

stop_project_processes() {
    local found=1

    if command -v pgrep >/dev/null 2>&1; then
        mapfile -t pids < <(pgrep -f "$ROOT_DIR/backend/.venv.*app.main:app|$ROOT_DIR/frontend.*vite|$ROOT_DIR/frontend.*npm run dev" || true)
        if [ "${#pids[@]}" -gt 0 ]; then
            found=0
            kill "${pids[@]}" >/dev/null 2>&1 || true
        fi
    fi

    return $found
}

echo "========================================"
echo "  AI 测试用例智能生成平台 - 停止脚本"
echo "========================================"

stopped=1
if [ -f "$STATE_FILE" ]; then
    # shellcheck disable=SC1090
    source "$STATE_FILE"

    if stop_pid "${FRONTEND_PID:-}"; then
        stopped=0
    fi
    if stop_pid "${BACKEND_PID:-}"; then
        stopped=0
    fi
fi

if stop_project_processes; then
    stopped=0
fi

rm -f "$STATE_FILE"

echo ""
if [ $stopped -eq 0 ]; then
    echo "Services stopped."
else
    echo "No running AITestPlatform services found."
fi