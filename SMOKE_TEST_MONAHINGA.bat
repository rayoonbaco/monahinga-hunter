@echo off
setlocal
cd /d "%~dp0"
title Monahinga vNext - Smoke Test

if not exist ".venv\Scripts\python.exe" (
    echo The local Python environment was not found.
    echo Please run FIRST_TIME_SETUP.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python "tools\smoke_test.py"
pause
exit /b %errorlevel%
