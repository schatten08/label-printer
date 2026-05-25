import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

text = text.replace('canvas.save(output_path)', 'canvas.save(output_path + ".png")')

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Canvas save fixed")
