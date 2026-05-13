@echo off
cd "%~dp0"
if exist "src\windows_version\Run Label Printer.bat" (
    call "src\windows_version\Run Label Printer.bat"
) else if exist "windows_version\Run Label Printer.bat" (
    call "windows_version\Run Label Printer.bat"
) else (
    echo [ERROR] Can't find Run Label Printer.bat!
    pause
)
