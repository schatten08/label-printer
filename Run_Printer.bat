@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===================================================
echo [1/3] Проверка окружения Python...
echo ===================================================

set "PYTHON_CMD="

:: 1. Проверяем стандартный Python Launcher (py)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    set "PYTHONW_CMD=pyw"
) else (
    :: 2. Проверяем обычный python.exe
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
        set "PYTHONW_CMD=pythonw"
    )
)

if not defined PYTHON_CMD (
    echo.
    echo [ОШИБКА] Python не найден на вашем компьютере!
    echo.
    echo Для работы программы необходимо установить Python:
    echo 1. Скачайте Python с официального сайта: https://www.python.org/downloads/
    echo 2. При установке ОБЯЗАТЕЛЬНО поставьте галочку "Add python.exe to PATH"!
    echo.
    pause
    exit /b 1
)

echo [+] Используется: !PYTHON_CMD!

echo.
echo ===================================================
echo [2/3] Проверка и установка библиотек (pywin32)...
echo ===================================================
!PYTHON_CMD! -m pip install pywin32 --quiet
if %errorlevel% neq 0 (
    echo [!] Предупреждение: Не удалось автоматически установить pywin32 через pip.
)

echo.
echo ===================================================
echo [3/3] Запуск Brother Label Printer...
echo ===================================================

:: Запускаем через pythonw, а если возникнет ошибка - перехватываем её
start "" !PYTHONW_CMD! "src\windows_version\print_gui.py"

:: Ждем 2 секунды и проверяем, запустился ли процесс
timeout /t 2 /nobreak >nul

exit /b 0
