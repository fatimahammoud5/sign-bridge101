@echo off
title SignBridge Launcher

echo ========================================
echo        Starting SignBridge
echo ========================================
echo.

echo [1/2] Starting AI Backend...

start "SignBridge AI Backend" cmd /k ^
"cd /d %~dp0ASL-Smart-Video-Translator && .venv\Scripts\python.exe backend_api.py"

echo.
echo Waiting for backend to start...
timeout /t 8 /nobreak >nul

echo.
echo [2/2] Starting Flutter App...
echo.

cd /d "%~dp0"

flutter run