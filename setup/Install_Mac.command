#!/bin/bash

# Переходим в папку, где лежит сам скрипт
cd "$(dirname "$0")"

echo "======================================================"
echo "   Brother Label Printer: Setup for macOS"
echo "======================================================"
echo

# 1. Проверка Python 3
if ! command -v python3 &> /dev/null
then
    echo "[!] Python 3 не найден!"
    read -p "Хотите автоматически скачать и запустить установщик Python для Mac? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        echo "[PROCESS] Скачивание Python 3.12..."
        PY_URL="https://www.python.org/ftp/python/3.12.3/python-3.12.3-macos11.pkg"
        PY_PKG="/tmp/python_install.pkg"
        curl -o "$PY_PKG" "$PY_URL"
        
        echo "[PROCESS] Запуск установщика... Следуйте инструкциям на экране."
        open "$PY_PKG"
        
        echo
        echo "======================================================"
        echo "ПОСЛЕ завершения установки Python, закройте это окно"
        echo "и запустите 'Install_Mac.command' еще раз."
        echo "======================================================"
        exit
    else
        echo "[ОШИБКА] Python 3 необходим для работы."
        echo "Пожалуйста, установите его с официального сайта: https://www.python.org/"
        exit
    fi
fi

echo "[1/2] Установка необходимых библиотек..."
python3 -m pip install --upgrade pip
python3 -m pip install brother_ql Pillow python_barcode
echo "[OK] Библиотеки установлены."
echo

# 2. Создание иконки запуска на Рабочем столе через AppleScript
echo "[2/2] Создание ярлыка на Рабочем столе..."
APP_PATH="$(pwd)/../src/mac_version/print_gui_mac.py"
OSASCRIPT_CMD="tell application \"Finder\"
    set desk to insertion point as text
    make new alias file at desktop to posix file \"$APP_PATH\"
end tell"

# Пытаемся создать алиас. Если не выйдет - создадим .command файл
osascript -e "$OSASCRIPT_CMD" &> /dev/null

if [ $? -eq 0 ]; then
    echo "[OK] Ярлык создан на рабочем столе."
else
    # Запасной вариант: создаем запускаемый файл на рабочем столе
    LAUNCHER="$HOME/Desktop/Label_Printer.command"
    echo "#!/bin/bash" > "$LAUNCHER"
    echo "cd \"$(pwd)\"" >> "$LAUNCHER"
    echo "python3 \"$APP_PATH\"" >> "$LAUNCHER"
    chmod +x "$LAUNCHER"
    echo "[OK] Создан файл запуска Label_Printer.command на рабочем столе."
fi

echo
echo "======================================================"
echo "   УСТАНОВКА ЗАВЕРШЕНА!"
echo "   Теперь вы можете запускать программу с рабочего стола."
echo "======================================================"
echo "Это окно можно закрыть."
