import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

top_part = text.split("def generate_label_image")[0]
bot_part = text.split("def send_to_printer")[1]

new_code = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 18.0,   # Значительно увеличил высоту штрихкода как на эталоне
        "module_width": 1.0,     # Сделал его шире
        "quiet_zone": 1.0,
    }
    
    temp_bc = output_path + "_bc"
    temp_bc_full = temp_bc + ".png"
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(temp_bc, options=options)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        bc_img = Image.open(temp_bc_full)
        
        font = None
        font_paths = [
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
            "/System/Library/Fonts/Times.ttc",
            "/Library/Fonts/Times New Roman.ttf"
        ]
        font_size = 100 # Крупный, читаемый шрифт как на оригинале
        for fp in font_paths:
            try:
                import os
                if os.path.exists(fp):
                    font = ImageFont.truetype(fp, font_size)
                    break
            except:
                pass
        
        if not font:
            font = ImageFont.load_default()
            
        canvas_w = 696 
        
        # Оставляем строго EPAM (заглавными)
        top_text = f"EPAM {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)
        
        # Минимизируем пустое пространство (отступы) сверху и снизу
        margin_y = 15
        spacing = 5
        
        # Если штрихкод все равно мал по ширине по-сравнению с текстом, можно его немного растянуть
        bc_target_w = max(int(text_w * 1.1), bc_img.width) # Штрихкод чуть шире текста
        bc_target_w = min(bc_target_w, canvas_w - 40) # Но не шире самой ленты
        
        bc_target_h = int(bc_img.height * (bc_target_w / bc_img.width)) if bc_img.width else bc_img.height
        bc_res = bc_img.resize((bc_target_w, bc_target_h), getattr(Image, 'Resampling', Image).NEAREST)

        canvas_h = text_h + bc_res.height + spacing + (margin_y * 2)
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        text_x = (canvas_w - text_w) // 2
        text_y = margin_y
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        bc_x = (canvas_w - bc_res.width) // 2
        bc_y = text_y + text_h + spacing
        canvas.paste(bc_res, (bc_x, bc_y))

        canvas.save(output_path + ".png", "PNG", dpi=(300.0, 300.0))
        
        try:
            import os
            os.remove(temp_bc_full)
        except:
            pass
            
    except Exception as e:
        print("Ошибка генерации новой этикетки:", e)

'''

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(top_part + new_code + "def send_to_printer" + bot_part)

print('Success sizing 2')
