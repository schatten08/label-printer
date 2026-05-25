import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

target = 'canvas.save(output_path + ".png")'
replacement = '''# Разворачиваем итоговый холст на 90 градусов (книжная ориентация), 
        # чтобы драйвер принтера вытянул его по длине ленты (ширина принтера = 29мм -> 342px)
        canvas = canvas.rotate(90, expand=True)
        canvas.save(output_path + ".png")'''

if target in text:
    text = text.replace(target, replacement)
    with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
        f.write(text)
    print("Canvas rotation applied.")
else:
    print("Target not found. Something is wrong.")
