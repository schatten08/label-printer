@echo off
setlocal
cd /d "%~dp0"

:: Self-elevate to Administrator if not already running as admin.
:: This is required because installing the b-PAC Client Component (system-wide
:: COM component via msiexec) silently fails without admin rights - msiexec /qn
:: suppresses all UI including the UAC prompt, so the failure is invisible.
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges - a UAC prompt will appear, please click Yes...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ===================================================
echo [1/4] Checking Python environment...
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
echo [2/4] Checking Brother b-PAC component...
echo ===================================================

:: b-PAC is a system COM component required to talk to the printer.
:: Detect it by trying to instantiate the bpac.Document COM object.
powershell -NoProfile -Command "try { New-Object -ComObject bpac.Document | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto BPAC_OK

echo [!] b-PAC Client Component not found. Downloading official installer...
set "BPAC_MSI=%TEMP%\bpac_client_x64.msi"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://download.brother.com/welcome/dlfp101010/bcciw34015_64.msi', '%BPAC_MSI%')"

if not exist "%BPAC_MSI%" goto BPAC_DL_FAIL

echo Installing b-PAC Client Component...
msiexec /i "%BPAC_MSI%" /qn /norestart /l*v "%TEMP%\bpac_install.log"
del "%BPAC_MSI%" >nul 2>&1

powershell -NoProfile -Command "try { New-Object -ComObject bpac.Document | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto BPAC_OK

echo [WARNING] Could not verify b-PAC installation. If printing fails later, install it manually:
echo https://support.brother.com/g/s/es/dev/en/bpac/download/index.html
goto BPAC_OK

:BPAC_DL_FAIL
echo [WARNING] Failed to download the b-PAC installer (check your internet connection).
echo Please install it manually:
echo https://support.brother.com/g/s/es/dev/en/bpac/download/index.html

:BPAC_OK
echo.
echo ===================================================
echo [3/4] Installing required Python libraries...
echo ===================================================
%PYTHON_CMD% -m pip install -r "src\windows_version\requirements.txt" --quiet
if %errorlevel% neq 0 echo [WARNING] pip install failed. Check your internet connection or proxy settings.

echo.
echo ===================================================
echo [4/4] Launching Brother Label Printer...
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
