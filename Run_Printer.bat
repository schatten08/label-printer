@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo [1/3] Checking Python environment...
echo ===================================================

set "PYTHON_CMD="
set "PYTHONW_CMD="

:: Check standard py launcher
py --version >nul 2>&1
if %errorlevel% equ 0 goto FOUND_PY

:: Check standard python
python --version >nul 2>&1
if %errorlevel% equ 0 goto FOUND_PYTHON

:: Check user localAppData path
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" goto FOUND_LOCAL312
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" goto FOUND_LOCAL313

:: If Python is not found, install it automatically
echo [!] Python is not installed. Starting automatic installation...
echo Downloading Python installer...

set "INSTALLER=%TEMP%\python_installer.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe', '%INSTALLER%')"

if not exist "%INSTALLER%" goto INSTALL_FAIL

echo Installing Python silently (1-2 minutes)...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%INSTALLER%" >nul 2>&1

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" goto FOUND_LOCAL312

py --version >nul 2>&1
if %errorlevel% equ 0 goto FOUND_PY

python --version >nul 2>&1
if %errorlevel% equ 0 goto FOUND_PYTHON

goto INSTALL_FAIL

:FOUND_PY
set "PYTHON_CMD=py"
set "PYTHONW_CMD=pyw"
goto RUN_PIP

:FOUND_PYTHON
set "PYTHON_CMD=python"
set "PYTHONW_CMD=pythonw"
goto RUN_PIP

:FOUND_LOCAL312
set PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe"
set PYTHONW_CMD="%LocalAppData%\Programs\Python\Python312\pythonw.exe"
goto RUN_PIP

:FOUND_LOCAL313
set PYTHON_CMD="%LocalAppData%\Programs\Python\Python313\python.exe"
set PYTHONW_CMD="%LocalAppData%\Programs\Python\Python313\pythonw.exe"
goto RUN_PIP

:RUN_PIP
echo [+] Using Python: %PYTHON_CMD%
echo.
echo ===================================================
echo [2/3] Installing required libraries...
echo ===================================================
%PYTHON_CMD% -m pip install -r "src\windows_version\requirements.txt" --quiet

echo.
echo ===================================================
echo [3/3] Launching Brother Label Printer...
echo ===================================================
start "" %PYTHONW_CMD% "src\windows_version\print_gui.py"
exit /b 0

:INSTALL_FAIL
echo.
echo [ERROR] Automatic Python installation failed.
echo Please download and install Python manually: https://www.python.org/downloads/
echo (Check the box "Add python.exe to PATH" during installation)
echo.
pause
exit /b 1
