@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===================================================
echo [1/3] Checking Python environment...
echo ===================================================

set "PYTHON_CMD="
set "PYTHONW_CMD="

:: Check if py launcher exists
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    set "PYTHONW_CMD=pyw"
) else (
    :: Check if python exists
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
        set "PYTHONW_CMD=pythonw"
    )
)

:: If Python is NOT found, automatically install Python silently
if not defined PYTHON_CMD (
    echo [!] Python is not installed. Starting automatic installation...
    echo.
    echo Downloading Python 3.12 installer...
    
    set "INSTALLER=%TEMP%\python_installer.exe"
    
    :: Download Python installer using PowerShell
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe', '%INSTALLER%')"
    
    if exist "%INSTALLER%" (
        echo Installing Python silently (this may take 1-2 minutes)...
        "%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        del "%INSTALLER%" >nul 2>&1
        
        :: Re-check standard installation paths
        if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
            set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe""
            set "PYTHONW_CMD="%LocalAppData%\Programs\Python\Python312\pythonw.exe""
        ) else if exist "C:\Program Files\Python312\python.exe" (
            set "PYTHON_CMD="C:\Program Files\Python312\python.exe""
            set "PYTHONW_CMD="C:\Program Files\Python312\pythonw.exe""
        ) else (
            py --version >nul 2>&1 && (
                set "PYTHON_CMD=py"
                set "PYTHONW_CMD=pyw"
            )
        )
    )
)

if not defined PYTHON_CMD (
    echo.
    echo [ERROR] Automatic Python installation failed or requires admin rights.
    echo Please install Python manually from https://www.python.org/downloads/
    echo (Make sure to check "Add python.exe to PATH" during installation)
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
