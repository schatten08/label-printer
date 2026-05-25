import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

text = text.replace('canvas.save(output_path + ".png")', 'canvas.save(output_path + ".png", dpi=(300, 300))')

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("DPI re-applied strictly")
