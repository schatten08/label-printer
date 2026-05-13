# Brother Label Printer

A GUI utility for batch printing labels on Brother printers (specifically QL-810W) using the Brother bPAC3 SDK.

## Description
This program allows you to quickly print a series of labels. It features a tabbed interface with two distinct modes:
1. **Batch Printing Mode**: Paste a list of asset numbers separated by spaces, commas, or new lines (ideal for copying directly from ServiceNow HAM or Excel) to print them all at once.
2. **Scanner Dictionary Mode**: Paste a two-column mapping of Serial Numbers (SN) to Labels. Connect a barcode scanner, scan the SN on a physical box, and the program will automatically find and print the corresponding Label in real-time with audio feedback.

The application automatically scans for installed printers and populates a dropdown menu, defaulting to the Brother printer. The input is automatically sanitized from unwanted special characters before printing. The graphical interface is written in Python (Tkinter). For Windows, the interaction with the printer driver is handled via a PowerShell script using official Brother bPAC3 COM objects. For macOS, it uses dynamic barcode image generation and the CUPS print server.

## Requirements
- OS: **Windows** (Primary version via bPAC SDK) or **macOS** (Alternative version via CUPS).
- Installed Python 3 (added to the PATH environment variable).
- Installed printer **Brother QL-810W** (or another supported Brother printer) and its drivers.

### Windows Setup
- Installed **Brother bPAC3 SDK**.
  - **How to install SDK**: Download the [Brother bPAC Client SDK](https://support.brother.com/g/s/es/dev/en/bpac/index.html) from the official Brother Developer Center (ensure you select your Windows version: 32-bit or 64-bit). Run the installer. Since our script uses standard Windows COM objects (`bpac.Document`), you only need a standard installation. The script will automatically connect to the SDK without needing hardcoded paths to `.dll` files.

### macOS Setup
For macOS, the application dynamically generates barcode images and bypasses the unsupported `.lbx` templates.
1. Open the terminal and install the required Python libraries:
   `pip3 install -r mac_version/requirements.txt`
2. Ensure your Brother printer is added in macOS "Printers & Scanners" settings. The script will automatically detect any printer containing "Brother" or "QL" in its name via the CUPS system.

## Usage
*The application provides two tabs/modes of operation:*

### Tab 1: Batch Printing (List)
1. Paste the copied asset/label numbers into the large text box.
2. Click the "Send to printer" button. All labels will be generated and printed sequentially.

### Tab 2: Box Scanner (SN -> Label)
1. Paste a two-column list (SN and Label) from Excel or ServiceNow into the upper dictionary field. Both horizontal formats and vertical sequential formats are supported.
2. Place your cursor in the bottom scanner input field.
3. Use a physical barcode scanner to scan the SN on your boxes. The program will parse the input (ignoring hardware 'S' prefixes), map it to the label, and print it automatically. You'll hear a system beep upon success or a different tone if the SN isn't found.

### Launching on Windows
1. Ensure the printer is connected, turned on, and has the correct label roll installed.
2. Ensure your label template is saved as `Label.lbx` (created in P-touch Editor) in the project folder. The template must contain text/barcode objects named `Label` and `BarCode`.
3. Launch the application via **`Run Label Printer.bat`** (or use the created shortcut `Label Printer.lnk`). It uses `pythonw` to hide the console window.

### Launching on macOS
1. Navigate to the `mac_version` directory.
2. Run the script: `python3 print_gui_mac.py`

## Project Structure
- `windows_version/print_gui.py` — The main graphical user interface for Windows (Python/Tkinter).
- `print.ps1` — The PowerShell script that communicates with the printer via the COM/bPAC SDK.
- `Label.lbx` — The Brother label template.
- `Run Label Printer.bat` — Batch script for quick UI launch.
