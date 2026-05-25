import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

new_gen = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": True,
        "font_size": 36,           
        "text_distance": 6,
        "module_height": 22.0,     
        "module_width": 0.6,       
        "quiet_zone": 1.0,         
    }
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(output_path, options=options)
'''

# Ищем начало def generate_label_image и заменяем до def send_to_printer
text = re.sub(r'def generate_label_image\(.*?\):.*?def send_to_printer', new_gen + '\ndef send_to_printer', text, flags=re.DOTALL)

# Убираем media параметры из lpr
text = text.replace('cmd = ["lpr", "-P", selected_printer, "-o", "fit-to-page", "-o", "media=Custom.29x90mm", image_path]', 'cmd = ["lpr", "-P", selected_printer, "-o", "fit-to-page", image_path]')

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Mac final print logic fixed!")
