@echo off
setlocal
cd /d "%~dp0"

:: Проверяем наличие Python
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python не найден. Пожалуйста, установите Python 3.12 или выше.
    pause
    exit /b
)

:: Проверяем наличие зависимостей (только pywin32)
py -m pip install pywin32 --quiet

:: Запуск программы через pythonw (без черного окна консоли)
start "" pyw "src\windows_version\print_gui.py"
exit /b
