@echo off
setlocal Title "Brother Label Printer - Environment Setup"

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
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please download and install Python from: https://www.python.org/downloads/
    echo IMPORTANT: Check the box "Add Python to PATH" during installation.
    pause
    exit /b
)
echo [OK] Python found.

:: 3. Обновление pip и установка библиотек
echo.
echo [2/3] Installing/Updating required Python libraries...
python -m pip install --upgrade pip
python -m pip install pywin32 pillow python-barcode brother_ql
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install some libraries. Check your internet connection.
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
set "SCRIPT_PATH=%~dp0src\windows_version\print_gui.py"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Label Printer.lnk"
set "ICON_PATH=%~dp0src\windows_version\Label.lbx"

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='pythonw.exe';$s.Arguments='\"%SCRIPT_PATH%\"';$s.WorkingDirectory='%~dp0src\windows_version';$s.IconLocation='shell32.dll,196';$s.Save()"

echo [OK] Shortcut 'Label Printer' created on your Desktop.

echo.
echo ======================================================
echo    SETUP COMPLETE! 
echo    Now you can use the shortcut on your Desktop.
echo ======================================================
pause
