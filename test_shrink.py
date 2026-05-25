import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

top_part = text.split("def generate_label_image")[0]
bot_part = text.split("def send_to_printer")[1]

# Убираем вообще все марджины
new_code = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 9.0,   
        "module_width": 0.5,    # Делаем сам штрихкод плотнее и компактнее
        "quiet_zone": 0.0,      # Отключаем встроенные отступы самого штрихкода!
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
        font_size = 65 # Делаем шрифт максимально похожим на эталонный
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
        top_text = f"EPAM {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = font_size
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)
            text_h = max(text_h, font_size)
        
        # Абсолютно в ноль убираем пустые поля
        margin_y = 0
        spacing = 5
        
        canvas_h = text_h + bc_img.height + spacing + (margin_y * 2)
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        text_x = (canvas_w - text_w) // 2
        text_y = margin_y
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        bc_x = (canvas_w - bc_img.width) // 2
        bc_y = text_y + text_h + spacing
        canvas.paste(bc_img, (bc_x, bc_y))

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

print('Success shrinking')
