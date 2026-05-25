import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

new_gen = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": True,
        "font_size": 42,           
        "text_distance": 10,
        "module_height": 25.0,     
        "module_width": 0.8,       
        "quiet_zone": 1.0,         
    }
    my_bc = Code128(text_str, writer=ImageWriter())
    saved_path = my_bc.save(output_path, options=options)
    
    # Создаем идеальное полотно под стандартную этикетку 90мм x 29мм (300dpi = 1062x342px)
    # Это предотвратит обрезание и заставит CUPS растянуть штрихкод ровно по площади ленты.
    try:
        from PIL import Image
        img = Image.open(saved_path)
        
        canvas_w, canvas_h = 1062, 342
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        
        # Если штрихкод вдруг больше холста, пропорционально уменьшаем
        if img.width > canvas_w - 40 or img.height > canvas_h - 40:
            # Используем LANCZOS для качественного сжатия
            img.thumbnail((canvas_w - 40, canvas_h - 40), getattr(Image, 'Resampling', Image).LANCZOS)
            
        offset = ((canvas_w - img.width) // 2, (canvas_h - img.height) // 2)
        canvas.paste(img, offset)
        
        canvas.save(saved_path)
    except Exception as e:
        print("Ошибка холста:", e)
'''

# Ищем начало def generate_label_image и заменяем до def send_to_printer
text = re.sub(r'def generate_label_image\(.*?\):.*?def send_to_printer', new_gen + '\ndef send_to_printer', text, flags=re.DOTALL)

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Mac canvas logic fixed!")
