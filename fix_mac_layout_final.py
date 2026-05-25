import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

new_gen = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 15.0,
        "module_width": 1.0,
        "quiet_zone": 1.0,
    }
    
    temp_bc = output_path + "_bc.png"
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(temp_bc, options=options)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        bc_img = Image.open(temp_bc)
        
        font = None
        font_paths = [
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Menlo.ttc"
        ]
        font_size = 110
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                continue
                
        if not font:
            font = ImageFont.load_default()
            
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(text_str)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(text_str, font=font)
            
        margin_x = 40
        margin_y = 20
        
        canvas_w = max(text_w, bc_img.width) + (margin_x * 2)
        canvas_h = 342  # Высота 29мм ленты при 300dpi
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        # Печатаем текст шрифтом в верхней половине
        text_x = (canvas_w - text_w) // 2
        text_y = margin_y
        draw.text((text_x, text_y), text_str, fill="black", font=font)
        
        # Растягиваем штрихкод без текста на всю оставшуюся нижнюю половину
        target_bc_h = canvas_h - text_h - (margin_y * 3)
        if target_bc_h > 0:
            bc_res = bc_img.resize((bc_img.width, target_bc_h), getattr(Image, 'Resampling', Image).NEAREST)
            bc_x = (canvas_w - bc_res.width) // 2
            bc_y = text_y + text_h + margin_y
            canvas.paste(bc_res, (bc_x, bc_y))

        canvas.save(output_path)
        
        try:
            os.remove(temp_bc)
        except:
            pass
            
    except Exception as e:
        print("Ошибка генерации новой этикетки:", e)
'''

text = re.sub(r'def generate_label_image\(.*?\):.*?def send_to_printer', new_gen + '\ndef send_to_printer', text, flags=re.DOTALL)

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Mac layout matched perfectly!")
