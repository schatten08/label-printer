import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

new_gen = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 13.0,     # Штрихкод стал пониже
        "module_width": 0.8,
        "quiet_zone": 1.0,
    }
    
    temp_bc = output_path + "_bc"
    temp_bc_full = temp_bc + ".png"
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(temp_bc, options=options)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import os
        bc_img = Image.open(temp_bc_full)
        
        font = None
        font_paths = [
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            "/System/Library/Fonts/Times.ttc"
        ]
        font_size = 90  # Размер шрифта для текста сверху
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                continue
                
        if not font:
            font = ImageFont.load_default()
            
        # Задаем размер полотна (29мм в высоту ~ 342px при 300dpi, ширина динамическая, но не менее 1200)
        canvas_h = 342
        
        # Строка текста сверху: "Epam " + сам номер
        top_text = f"Epam {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)
        
        # Ширина холста подстраивается под текст или штрихкод
        canvas_w = max(text_w + 100, bc_img.width + 100, 1200)
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        # 1. Текст сверху (Epam 1121502)
        # Немного сдвигаем текст влево от центра (чтобы выглядело как в оригинале)
        text_x = (canvas_w - text_w) // 2
        text_y = 50 # Отступ сверху
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        # 2. Штрихкод снизу
        # Растягиваем его по ширине текста
        bc_target_w = max(text_w, bc_img.width)
        bc_target_h = canvas_h - text_h - 100 # Оставшееся место
        if bc_target_h > 0:
            bc_res = bc_img.resize((bc_target_w, bc_target_h), getattr(Image, 'Resampling', Image).NEAREST)
            bc_x = (canvas_w - bc_res.width) // 2
            bc_y = text_y + text_h + 10  # Сразу под текстом
            canvas.paste(bc_res, (bc_x, bc_y))

        canvas.save(output_path + ".png")
        
        try:
            os.remove(temp_bc_full)
        except:
            pass
            
    except Exception as e:
        print("Ошибка генерации новой этикетки:", e)
'''

text = re.sub(r'def generate_label_image\(.*?\):.*?def send_to_printer', new_gen + '\ndef send_to_printer', text, flags=re.DOTALL)

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("Mac EPAm layout created!")
