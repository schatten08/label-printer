import codecs
with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()
print("CANVAS_W:", "canvas_w =" in text)
print("ROTATE:", "rotate" in text.lower())
