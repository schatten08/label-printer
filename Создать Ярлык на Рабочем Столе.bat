@echo off
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Печать этикеток Brother.lnk"
set "TARGET_SCRIPT=%SCRIPT_DIR%src\windows_version\print_gui.py"
:: Используем pyw.exe для запуска без консоли. Экзешник всегда можно закрепить на панели задач!
set "TARGET_EXE=pyw.exe"
set "ICON_PATH=shell32.dll,16"

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%TARGET_EXE%" >> CreateShortcut.vbs
echo oLink.Arguments = """%TARGET_SCRIPT%""" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_DIR%src\windows_version" >> CreateShortcut.vbs
echo oLink.Description = "Brother Label Printer" >> CreateShortcut.vbs
echo oLink.IconLocation = "%ICON_PATH%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript /nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo Ярлык "Печать этикеток Brother" успешно создан на рабочем столе!
echo Теперь вы можете нажать по нему правой кнопкой мыши и выбрать "Закрепить на панели задач".
pause
