@echo off
chcp 65001 >nul
title AI 测试用例智能生成平台

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %EXIT_CODE%
