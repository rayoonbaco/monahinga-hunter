@echo off
setlocal

cd /d "%~dp0"
title Monahinga Server

echo ==========================================
echo Starting Monahinga Server...
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Local Python environment not found.
    echo Run FIRST_TIME_SETUP.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Opening browser...
start "" http://127.0.0.1:8010/

echo.
echo Server starting in this window...
echo Press CTRL+C in this window to stop it.
echo ==========================================
echo.

python -m uvicorn apps.api.main:app --port 8010

endlocal