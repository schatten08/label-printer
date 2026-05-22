import sys

def patch(file):
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace('font=("Segoe UI" if "windows" in file else "Helvetica", 10, "bold")', 
                        'font=("Segoe UI" if "win" in sys.platform else "Helvetica", 10, "bold")')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)

patch('src/windows_version/print_gui.py')
patch('src/mac_version/print_gui_mac.py')
print("Fixed theme var NameError!")
