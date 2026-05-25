import codecs

filepath = 'README.md'
with codecs.open(filepath, 'r', 'utf-8-sig') as f:
    content = f.read()

addition = """
### Hardware Scanner Setup (Zebra DS22 / Bluetooth)
If you are using a wireless barcode scanner like the **Zebra DS2278** and want to connect it directly via Bluetooth (bypassing the dock station):
- **Windows:** Download and install the [Cordless Scan-to-Connect (123Scan)](https://www.zebra.com/us/en/support-downloads/software/scanner-software/cordless-scantoconnect.html) utility from the official Zebra website. Run the utility and scan the pairing barcode from the screen.
- **macOS:** You usually do not need extra software. Scan the "HID Bluetooth Classic" (or "HID Keyboard Emulation") configuration barcode from the Zebra Quick Start Guide to put the scanner in pairing mode, then go to macOS *System Settings > Bluetooth* and connect the scanner as a standard keyboard.
"""

if 'Hardware Scanner Setup' not in content:
    content = content.replace(
        '### macOS Setup',
        addition + '\n### macOS Setup'
    )
    with codecs.open(filepath, 'w', 'utf-8') as f:
        f.write(content)
    print("README updated")
