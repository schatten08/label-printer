import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# Изменяем _bc.png на правильное сохранение, так как barcode.save() сам добавляет .png
new_code = '''
    temp_bc_base = output_path + "_bc"
    temp_bc_full = temp_bc_base + ".png"
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(temp_bc_base, options=options)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        bc_img = Image.open(temp_bc_full)
'''
text = text.replace('''
    temp_bc = output_path + "_bc.png"
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(temp_bc, options=options)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        bc_img = Image.open(temp_bc)''', new_code)

text = text.replace('os.remove(temp_bc)', 'os.remove(temp_bc_full)')

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Temp file bug fixed")
