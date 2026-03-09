@echo off
chcp 65001 >nul
title AI 测试用例智能生成平台

echo ========================================
echo   AI 测试用例智能生成平台 - 启动脚本
echo ========================================

:: ─── 后端 ─────────────────────────────────
echo.
echo [1/3] 检查 Python 环境...
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请安装 Python 3.9+
    pause & exit /b 1
)

echo.
echo [2/3] 安装后端依赖并启动...
cd backend
if not exist ".venv" (
    python -m venv .venv
    echo 虚拟环境创建成功
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
if not exist ".env" (
    copy .env.example .env >nul
    echo [警告] 已创建 .env，请填入 AI 模型 API Key
)

echo 启动后端服务 http://localhost:8000 ...
start "后端服务" cmd /k "call .venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: ─── 前端 ─────────────────────────────────
echo.
echo [3/3] 安装前端依赖并启动...
cd ..\frontend
if not exist "node_modules" (
    echo 首次安装前端依赖，请稍候...
    npm install --cache %TEMP%\npm-cache --no-audit --no-fund
)

echo 启动前端服务 http://localhost:5173 ...
start "前端服务" cmd /k "npm run dev"

echo.
echo ========================================
echo   启动成功！
echo.
echo   前端地址：http://localhost:5173
echo   后端API： http://localhost:8000/api/v1
echo   API文档： http://localhost:8000/docs
echo.
echo   默认账号：admin / Admin@123
echo ========================================
echo.
pause
