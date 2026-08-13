# Copilot Instructions — Brother Label Printer

Утилита для быстрой печати наклеек на принтерах Brother (QL series, QL-810W) со штрихкодами и текстом. Поддерживает Windows и macOS.

## 🏗 Архитектура проекта и точки входа

- **Windows Версия**: [src/windows_version/print_gui.py](src/windows_version/print_gui.py)
  - Использует системный COM-объект `bpac.Document` / `bpac.Printer` через `win32com.client`.
  - Требует установленный компонент [bPAC Client Component](https://support.brother.com/g/s/es/dev/en/bpac/download/index.html?c=eu_ot&lang=en&navi=offall&comple=on&redirect=on) на системе.
  - Шаблоны наклеек: [src/windows_version/Label.lbx](src/windows_version/Label.lbx), `Label_Free.lbx`.
  - Конфигурация: `config.json` (последний выбранный принтер и т.д.).

- **macOS Версия**: [src/mac_version/print_gui_mac.py](src/mac_version/print_gui_mac.py)
  - Использует открытую библиотеку `brother_ql` для прямой отправки команд растровой печати на принтер (через USB / Wi-Fi).

- **Обход антивирусов / Простой запуск (Windows)**: [Run_Printer.bat](Run_Printer.bat)
  - Автоматически находит или скрытно устанавливает Python 3.12 (`/quiet`).
  - Проверяет наличие COM-объекта `bpac.Document` и, если его нет, скачивает и тихо устанавливает официальный `b-PAC Client Component (x64)` MSI от Brother (`msiexec /qn`) — может показать запрос UAC.
  - Ставит зависимости из `src/windows_version/requirements.txt` (`pywin32`).
  - Запускает `print_gui.py` без консольного окна через `pyw`.

- **Сборка EXE (PyInstaller)**:
  - Настройки сборки: [src/windows_version/Label_Printer.spec](src/windows_version/Label_Printer.spec).
  - `build/` и `dist/` — генерируемые каталоги, **не коммитятся в git** (см. `.gitignore`). Готовый `.exe` не распространяется через репозиторий: корпоративные антивирусы (SentinelOne/Defender) блокируют неподписанные бинарники, поэтому основной способ запуска — `Run_Printer.bat`.

## 🚀 Команды запуска и сборки

- **Запуск через bat-скрипт (Windows)**:
  ```cmd
  Run_Printer.bat
  ```
- **Запуск напрямую через Python**:
  ```bash
  python src/windows_version/print_gui.py
  ```
- **Сборка EXE файла (Windows)**:
  ```cmd
  cd src/windows_version
  pyinstaller --noconfirm --onefile --windowed --name "Label_Printer" --add-data "Label.lbx;." --add-data "Label_Free.lbx;." print_gui.py
  ```
- **Синхронизация с Git**:
  ```bash
  git add .
  git commit -m "feat: description"
  git push origin main
  ```

## 📐 Соглашения по коду и принципы

1. **YAGNI / Простота**: Инструкции пользователя в README и интерфейсе должны быть простыми и понятными конечным пользователям (не разработчикам).
2. **Формат коммитов (Conventional Commits)**: `feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`.
3. **Безопасность антивирусов**: Отдавать приоритет запуску через `Run_Printer.bat` или прямой Python-код при жестких корпоративных политиках (SentinelOne / Defender).
4. **Совместимость бат-файлов**: Командные файлы `.bat` должны быть записаны в кодировке ASCII без кириллицы и без сложной вложенности `if (...)`, чтобы избежать сбоев кодировки и спецсимволов в путях.
