@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===================================================
echo [1/3] Checking Python environment...
echo ===================================================

set "PYTHON_CMD="
set "PYTHONW_CMD="

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    set "PYTHONW_CMD=pyw"
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
        set "PYTHONW_CMD=pythonw"
    )
)

if not defined PYTHON_CMD (
    echo.
    echo [ERROR] Python was not found on your computer!
    echo.
    echo Please install Python:
    echo 1. Download Python from https://www.python.org/downloads/
    echo 2. MUST check the box "Add python.exe to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [+] Using Python: !PYTHON_CMD!

echo.
echo ===================================================
echo [2/3] Installing required libraries (pywin32)...
echo ===================================================
!PYTHON_CMD! -m pip install pywin32 --quiet

echo.
echo ===================================================
echo [3/3] Launching Brother Label Printer...
echo ===================================================

start "" !PYTHONW_CMD! "src\windows_version\print_gui.py"

exit /b 0
