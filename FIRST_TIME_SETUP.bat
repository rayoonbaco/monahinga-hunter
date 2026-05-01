@echo off
setlocal
cd /d "%~dp0"
title Monahinga vNext - First Time Setup

echo.
echo ============================================
echo   MONAHINGA vNext - FIRST TIME SETUP
echo ============================================
echo.

if exist ".venv\Scripts\python.exe" goto INSTALL

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -m venv .venv
    goto INSTALL
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -m venv .venv
    goto INSTALL
)

echo Python was not found.
echo Install Python 3.12, then run this file again.
pause
exit /b 1

:INSTALL
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 (
    echo pip upgrade failed.
    pause
    exit /b 1
)

pip install -e .
if errorlevel 1 (
    echo Dependency install failed.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo Next: double-click START_MONAHINGA_SERVER.bat
echo.
pause
exit /b 0
