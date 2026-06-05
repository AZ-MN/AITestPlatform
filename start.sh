#!/bin/bash
# ========================================================
# 一键启动脚本 (Linux/macOS)
# 使用方式：chmod +x start.sh && ./start.sh
# ========================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/.run"
STATE_FILE="$RUNTIME_DIR/aitestplatform-unix.env"

cleanup_state() {
    rm -f "$STATE_FILE"
}

write_state() {
    mkdir -p "$RUNTIME_DIR"
    cat > "$STATE_FILE" <<EOF
BACKEND_PID=$BACKEND_PID
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PID=$FRONTEND_PID
FRONTEND_PORT=$FRONTEND_PORT
ROOT_DIR=$ROOT_DIR
EOF
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_port_in_use() {
    local port="$1"

    if command_exists lsof; then
        lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
        return $?
    fi

    if command_exists ss; then
        ss -ltn | awk '{print $4}' | grep -E "(^|:)$port$" >/dev/null 2>&1
        return $?
    fi

    if command_exists netstat; then
        netstat -ltn 2>/dev/null | awk '{print $4}' | grep -E "(^|:)$port$" >/dev/null 2>&1
        return $?
    fi

    echo "无法检测端口占用：请安装 lsof、ss 或 netstat 之一"
    exit 1
}

find_free_port() {
    local preferred_port="$1"
    local end_port=$((preferred_port + 20))
    local port

    for ((port=preferred_port; port<=end_port; port++)); do
        if ! is_port_in_use "$port"; then
            echo "$port"
            return 0
        fi
    done

    echo ""
    return 1
}

wait_for_port() {
    local port="$1"
    local retries="$2"
    local attempt

    for ((attempt=1; attempt<=retries; attempt++)); do
        if is_port_in_use "$port"; then
            return 0
        fi
        sleep 1
    done

    return 1
}

echo "========================================"
echo "  AI 测试用例智能生成平台 - 启动脚本"
echo "========================================"

cleanup_state

echo ""
echo "[1/4] 检查运行环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到 npm，请确认 Node.js 安装完整"
    exit 1
fi
python3 --version

BACKEND_PORT="$(find_free_port 8000)"
if [ -z "$BACKEND_PORT" ]; then
    echo "❌ 无法找到可用的后端端口"
    exit 1
fi

FRONTEND_PORT="$(find_free_port 5173)"
if [ -z "$FRONTEND_PORT" ]; then
    echo "❌ 无法找到可用的前端端口"
    exit 1
fi

if [ "$BACKEND_PORT" != "8000" ]; then
    echo "⚠️  端口 8000 已占用，后端将使用 $BACKEND_PORT"
fi
if [ "$FRONTEND_PORT" != "5173" ]; then
    echo "⚠️  端口 5173 已占用，前端将使用 $FRONTEND_PORT"
fi

echo ""
echo "[2/4] 安装后端依赖..."
cd "$ROOT_DIR/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
fi
source .venv/bin/activate
pip install -r requirements.txt -q
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  已创建 .env 文件，请填入 AI 模型 API Key"
fi

echo ""
echo "▶ 启动后端服务 (http://127.0.0.1:$BACKEND_PORT)..."
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

if ! wait_for_port "$BACKEND_PORT" 15; then
    echo "❌ 后端未能在预期时间内启动"
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

echo ""
echo "[3/4] 安装前端依赖并启动..."
cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "首次安装前端依赖 (请稍候)..."
    npm install
fi
echo ""
echo "▶ 启动前端服务 (http://127.0.0.1:$FRONTEND_PORT)..."
VITE_API_PROXY_TARGET="http://127.0.0.1:$BACKEND_PORT" npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

if ! wait_for_port "$FRONTEND_PORT" 30; then
    echo "❌ 前端未能在预期时间内启动"
    kill "$FRONTEND_PID" "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

write_state

echo ""
echo "========================================"
echo "  ✅ 启动成功！"
echo ""
echo "  前端地址：http://127.0.0.1:$FRONTEND_PORT"
echo "  后端API： http://127.0.0.1:$BACKEND_PORT/api/v1"
echo "  API文档： http://127.0.0.1:$BACKEND_PORT/docs"
echo "  前端代理：http://127.0.0.1:$BACKEND_PORT"
echo "  停止命令：./stop.sh"
echo ""
echo "  默认账号：admin / Admin@123"
echo "========================================"

# 捕获退出信号，清理进程
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; cleanup_state; echo '已停止'" INT TERM EXIT
wait
