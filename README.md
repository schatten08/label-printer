# 🖨️ Brother Label Printer

Утилита для быстрой печати наклеек на принтерах Brother (через штрихкод или текстом). Работает на Windows и macOS.

---

## 🚀 БЫСТРЫЙ СТАРТ

Для начала работы выберите наиболее удобный способ:

### 1. Самый простой (Windows)
Просто скачайте и запустите готовый файл:
👉 **[src/windows_version/dist/Label_Printer.exe](src/windows_version/dist/Label_Printer.exe)**
*(Не требует установки Python или библиотек. Работает сразу.)*

### 2. Через установщик (Windows и macOS)
Если вы хотите запускать программу через ярлык на рабочем столе и иметь возможность автообновления:

1.  Зайдите в папку [setup/](setup/)
2.  Запустите нужный файл:
    -   **Windows**: запустите [setup/Install_Setup.bat](setup/Install_Setup.bat) от имени Администратора.
    -   **macOS**: запустите [setup/Install_Mac.command](setup/Install_Mac.command).

**Что сделает установщик:**
- Проверит наличие Python (и предложит установить, если его нет).
- Автоматически установит все необходимые библиотеки.
- Создаст удобный ярлык на вашем Рабочем столе для быстрого запуска программы.

---

## 🛠️ Основные режимы работы (Вкладки)

1.  **📝 Список**: Вставьте список номеров (из Excel или письма) → Нажмите "Печать". Каждый номер — отдельная наклейка со штрихкодом.
2.  **🔍 Сканер**: Вставьте список "Серийник — Инвентарник" → Сканируйте коробку → Принтер сам печатает нужную наклейку.
3.  **📋 Инвентаризация**: Загрузите базу → Сканируйте всё подряд → Программа отметит найденное и выгрузит отчет.
4.  **abc Произвольная печать**: Напишите любой текст → Нажмите "Печать". Печать без лишних слов и штрихкодов, текст по центру.

---

## 🔄 Как обновлять программу
Внутри программы есть кнопка **"🔄 Check for Updates"**:
- Если у вас стоит Git — программа обновится сама.
- Если Git нет — программа предложит скачать новую версию в браузере.

---

## 📋 Технические подробности (Для разработчиков)
*(Далее следует старая версия README с деталями...)*

## Requirements
- OS: **Windows** (Primary version via bPAC SDK) or **macOS** (Alternative version via CUPS & brother_ql).
- Installed Python 3 (added to the PATH environment variable).
- Installed printer **Brother QL-810W** (or another supported Brother printer) and its drivers.

### Windows Setup
1. Open the terminal/command prompt and install the required library:
   `pip install pywin32`
2. Install the **Brother bPAC3 SDK**.
   - **How to install SDK**: Download the [Brother bPAC Client SDK](https://support.brother.com/g/s/es/dev/en/bpac/index.html) from the official Brother Developer Center (ensure you select your Windows version: 32-bit or 64-bit). Run the installer. Since our script uses standard Windows COM objects (`bpac.Document`), you only need a standard installation.


### Hardware Scanner Setup (Zebra DS22 / Bluetooth)
If you are using a wireless barcode scanner like the **Zebra DS2278** and want to connect it directly via Bluetooth (bypassing the dock station):
- **Windows:** Download and install the [Cordless Scan-to-Connect (123Scan)](https://www.zebra.com/us/en/support-downloads/software/scanner-software/cordless-scantoconnect.html) utility from the official Zebra website. Run the utility and scan the pairing barcode from the screen.
- **macOS:** You usually do not need extra software. Scan the "HID Bluetooth Classic" (or "HID Keyboard Emulation") configuration barcode from the Zebra Quick Start Guide to put the scanner in pairing mode, then go to macOS *System Settings > Bluetooth* and connect the scanner as a standard keyboard.

### macOS Setup
For macOS, the application dynamically generates barcode images and bypasses the unsupported `.lbx` templates. Instead of relying on native CUPS drivers (which often distort continuous roll dimensions), the Mac version uses the `brother_ql` library to compile raw binary instructions, which are then passed natively to the printer.
1. Open the terminal and install the required Python libraries:
   `pip3 install -r mac_version/requirements.txt` *(Note: requires `brother_ql`, `Pillow`, and `python-barcode`)*
2. Ensure your Brother printer is added in macOS "Printers & Scanners" settings. The script will automatically detect any printer containing "Brother" or "QL" in its name and map the job to print directly over `lp -o raw`.

## Usage
*The application provides three tabs/modes of operation:*

### Tab 1: Batch Printing (List)
1. Paste the copied asset/label numbers into the large text box.
2. Click the "Send to printer" button. All labels will be generated and printed sequentially.

### Tab 2: Box Scanner (SN -> Label)
1. Paste a two-column list (SN and Label) from Excel or ServiceNow into the upper dictionary field. Both horizontal formats and vertical sequential formats are supported.
2. Place your cursor in the bottom scanner input field.
3. Use a physical barcode scanner to scan the SN on your boxes. The program will parse the input (ignoring hardware 'S' prefixes), map it to the label, and print it automatically. You'll hear a system beep upon success or a different tone if the SN isn't found.

### Tab 3: Inventory Audit
1. Paste your device database (e.g., from Excel, containing SN/Label and Model) into the top input field.
2. Click the "Load Database" button. This will parse the data and populate an interactive, searchable checklist displaying all pending equipment.
3. Scan barcodes using the bottom scanner input field.
4. The scanner uses smart string matching to locate the scanned serial number, instantly marks it as "Found" (highlighting it green) in the checklist, and plays a success chime. If not found, it alerts you.
5. Track your overall scanning progress in real-time (`Found: X / Y`).
6. Once the audit is complete, click "Export to CSV" to generate a clean, Excel-ready report (UTF-8 encoded with semicolon delimiters) of your inventory statuses.

### Tab 4: Direct Print (Произвольная печать)
1. Paste or type any multiline text into the large text area.
2. Click "Print" — each line will be printed as a separate, individual label.
3. In this mode, the hardware barcode and standard "EPAM " prefixes are completely bypassed. The text is perfectly centered across the entire width of the label.

### Updates & Maintenance
The application includes a **"Check for Updates"** button.
- **If Git is installed**: It automatically performs a `git pull`, ensuring you always have the latest features and fixes.
- **If Git is NOT installed**: It uses the GitHub API to check for updates. If a new version is found, it will offer to open the download page in your browser.
- **Network Drives Support**: The program automatically handles Git's "dubious ownership" errors, making it safe to run from network shares.
- **ZIP Downloads**: If you downloaded the project as a ZIP archive, you can now enable full auto-updates with one click (the app will offer to initialize a Git repository for you).

### Launching on Windows
1. Ensure the printer is connected, turned on, and has the correct label roll installed.
2. Ensure your label template is saved as `Label.lbx` (created in P-touch Editor) in the project folder. The template must contain text/barcode objects named `Label` and `BarCode`.
3. Launch the application via **`Run Label Printer.bat`** (or use the created shortcut `Label Printer.lnk`). It uses `pythonw` to hide the console window.

### Launching on macOS
1. Navigate to the `mac_version` directory.
2. Run the script: `python3 print_gui_mac.py`

**Creating a macOS App Shortcut (Automator):**
To run the application natively without keeping a Terminal window open, you can create a Mac `.app`:
1. Open **Automator** and create a New Document -> **Application**.
2. Drag and drop the **"Run Shell Script"** action from the left sidebar into the right pane.
3. Paste the following script (adjusting the paths to your specific Python environment, e.g., `pyenv` or `homebrew`, and your project path):
   ```bash
   # Example for pyenv users:
   export PATH="$HOME/.pyenv/bin:$HOME/.pyenv/shims:$PATH"
   
   cd "$HOME/Downloads/label-printer/src/mac_version"
   python3 print_gui_mac.py
   ```
4. Click **File -> Save**, name it `Label Printer`, and save it to your Applications folder or Desktop. You can now launch the printer GUI like any other Mac app.

## Project Structure
- `src/windows_version/print_gui.py` — The pure Python graphical user interface and print engine for Windows.
- `src/windows_version/Label.lbx` — The Brother label template.
- `src/windows_version/Run Label Printer.bat` — Batch script for quick UI launch.
- `src/mac_version/print_gui_mac.py` — The dedicated version of the app optimized for macOS.
