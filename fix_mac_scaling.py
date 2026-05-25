import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

target = 'cmd = ["lpr", "-P", selected_printer, "-o", "fit-to-page", image_path]'
replacement = 'cmd = ["lpr", "-P", selected_printer, "-o", "natural-scaling=100", image_path]'

if target in text:
    text = text.replace(target, replacement)
    with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
        f.write(text)
    print("Scaling fixed!")
else:
    print("Target not found.")

