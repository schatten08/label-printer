# Brother Label Printer

A GUI utility for batch printing labels on Brother printers (specifically QL-810W) using the Brother bPAC3 SDK.

## Description
This program allows you to quickly print a series of labels by pasting a list of asset numbers separated by spaces, commas, or new lines (ideal for copying directly from ServiceNow HAM or Excel). The input is automatically sanitized from unwanted special characters before printing. The graphical interface is written in Python (Tkinter), and the interaction with the printer driver is handled via a PowerShell script using official Brother bPAC3 COM objects.

## Requirements
- OS: **Windows only** (bPAC SDK and PowerShell COM objects are exclusively supported on Windows OS).
- Installed Python 3 (added to the PATH environment variable).
- Installed printer **Brother QL-810W** (or another supported Brother printer) and its drivers.
- Installed **Brother bPAC3 SDK**.
  - **How to install SDK**: Download the [Brother bPAC Client SDK](https://support.brother.com/g/s/es/dev/en/bpac/index.html) from the official Brother Developer Center (ensure you select your Windows version: 32-bit or 64-bit). Run the installer. Since our script uses standard Windows COM objects (`bpac.Document`), you only need a standard installation. The script will automatically connect to the SDK without needing hardcoded paths to `.dll` files.

## Usage
1. Ensure the printer is connected, turned on, and has the correct label roll installed.
2. Ensure your label template is saved as `Label.lbx` (created in P-touch Editor) in the project folder. The template must contain text/barcode objects named `Label` and `BarCode`.
3. Launch the application via **`Run Label Printer.bat`** (or use the created shortcut `Label Printer.lnk`). It uses `pythonw` to hide the console window.
4. Paste the copied asset numbers into the text box and click the "Send to printer" button.

## Project Structure
- `print_gui.py` — The main graphical user interface (Python/Tkinter).
- `print.ps1` — The PowerShell script that communicates with the printer via the COM/bPAC SDK.
- `Label.lbx` — The Brother label template.
- `Run Label Printer.bat` — Batch script for quick UI launch.
