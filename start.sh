#!/bin/bash
# ========================================================
# 一键启动脚本 (Linux/macOS)
# 使用方式：chmod +x start.sh && ./start.sh
# ========================================================
set -e

echo "========================================"
echo "  AI 测试用例智能生成平台 - 启动脚本"
echo "========================================"

# ─── 后端 ───────────────────────────────────────────────
echo ""
echo "[1/3] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi
python3 --version

echo ""
echo "[2/3] 安装后端依赖..."
cd backend
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
echo "▶ 启动后端服务 (http://localhost:8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# ─── 前端 ───────────────────────────────────────────────
echo ""
echo "[3/3] 安装前端依赖并启动..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "首次安装前端依赖 (请稍候)..."
    npm install
fi
echo ""
echo "▶ 启动前端服务 (http://localhost:5173)..."
npm run dev &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

echo ""
echo "========================================"
echo "  ✅ 启动成功！"
echo ""
echo "  前端地址：http://localhost:5173"
echo "  后端API： http://localhost:8000/api/v1"
echo "  API文档： http://localhost:8000/docs"
echo ""
echo "  默认账号：admin / Admin@123"
echo "========================================"

# 捕获退出信号，清理进程
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '已停止'" INT TERM
wait
