@echo off
title Brother Label Printer - Environment Setup
setlocal

echo ======================================================
echo    Brother Label Printer: Setup Environment
echo ======================================================
echo.

:: 1. Проверка прав администратора (нужны для реестра и установки SDK в будущем)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrative privileges.
) else (
    echo [!] Please run this script as Administrator for best results.
)

:: 2. Проверка Python
echo.
echo [1/3] Checking Python installation...

:: Пытаемся найти работающий Python (сначала через лаунчер 'py', потом просто 'python')
set "PYTHON_EXEC="
py -0 >nul 2>&1 && set "PYTHON_EXEC=py"
if not defined PYTHON_EXEC (
    python --version >nul 2>&1 && set "PYTHON_EXEC=python"
)

:: Проверяем, есть ли Python и работает ли в нем pip
if defined PYTHON_EXEC (
    %PYTHON_EXEC% -m pip --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo [!] Python found, but 'pip' module is missing or broken.
        set "PYTHON_EXEC="
    )
)

if not defined PYTHON_EXEC (
    echo [!] Working Python not found or pip is missing.
    echo.
    set /p "install_python=Would you like to download and install Python 3.12 automatically? (y/n): "
    if /i "%install_python%"=="y" (
        echo.
        echo [PROCESS] Downloading Python 3.12 installer...
        set "py_url=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
        set "py_exe=%temp%\python_installer.exe"
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%py_url%', '%py_exe%')"
        
        echo [PROCESS] Launching installer...
        echo IMPORTANT: When requested, ensure you check 'Add Python to PATH'!
        start /wait "" "%py_exe%" /passive PrependPath=1 Include_test=0
        
        echo.
        echo [OK] Installation attempt finished.
        echo Please CLOSE this window and launch 'Install_Setup.bat' AGAIN to finish setup.
        pause
        exit /b
    ) else (
        echo.
        echo [ERROR] Python with 'pip' is required. Please install it from: https://www.python.org/
        echo IMPORTANT: Check the box "Add Python to PATH" during installation.
        pause
        exit /b
    )
)
echo [OK] Python found (%PYTHON_EXEC%).

:: 3. Обновление pip и установка библиотек
echo.
echo [2/3] Installing/Updating required Python libraries...
%PYTHON_EXEC% -m pip install --upgrade pip
%PYTHON_EXEC% -m pip install pywin32 pillow python-barcode brother_ql
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install some libraries. Check your internet connection.
    echo If you have multiple Python versions, ensure the correct one is in PATH.
    pause
    exit /b
)
echo [OK] Python libraries installed.

:: 4. Проверка bPAC SDK (через наличие DLL в системе)
echo.
echo [3/3] Checking Brother bPAC SDK...
if exist "C:\Program Files\Brother bPAC SDK" (
    echo [OK] bPAC SDK seems to be installed.
) else if exist "C:\Program Files (x86)\Brother bPAC SDK" (
    echo [OK] bPAC SDK (x86) seems to be installed.
) else (
    echo [WARNING] Brother bPAC SDK not found! 
    echo Windows printing will NOT work without it.
    echo Please download it from Brother Developer Center later.
)

:: 5. Создание ярлыка (вызов PowerShell для создания .lnk)
echo.
echo [BONUS] Creating Desktop Shortcut...
set "SCRIPT_PATH=%~dp0..\src\windows_version\print_gui.py"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Label Printer.lnk"
set "WORKING_DIR=%~dp0..\src\windows_version"

:: Определяем GUI лаунчер (pyw или pythonw)
set "PYW_EXEC=pythonw"
if "%PYTHON_EXEC%"=="py" (set "PYW_EXEC=pyw")

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='%PYW_EXEC%';$s.Arguments='\"%SCRIPT_PATH%\"';$s.WorkingDirectory='%WORKING_DIR%';$s.IconLocation='shell32.dll,196';$s.Save()"

echo [OK] Shortcut 'Label Printer' created on your Desktop.

echo.
echo ======================================================
echo    SETUP COMPLETE! 
echo    Now you can use the shortcut on your Desktop.
echo ======================================================
pause
