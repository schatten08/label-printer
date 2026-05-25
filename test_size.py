import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

top_part = text.split("def generate_label_image")[0]
bot_part = text.split("def send_to_printer")[1]

new_code = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 10.0, # Родной, приятный размер штрихкода (без гигантизма)
        "module_width": 0.7,   
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
            "/System/Library/Fonts/Times.ttc"
        ]
        font_size = 85 # Возвращаем адекватный размер текста (~7 миллиметров высотой)
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
            
        canvas_h = 696 # Ширина 62мм ленты ПРИНТЕРА остается 696, чтобы brother_ql не масштабировал!
        top_text = f"Epam {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)
        
        margin = 100
        canvas_w = max(text_w, bc_img.width) + (margin * 2) 
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        # Центрируем весь блок посередине 62мм ленты по вертикали
        content_h = text_h + 15 + bc_img.height
        start_y = (canvas_h - content_h) // 2
        
        text_x = (canvas_w - text_w) // 2
        text_y = start_y
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        bc_x = (canvas_w - bc_img.width) // 2
        bc_y = text_y + text_h + 15
        canvas.paste(bc_img, (bc_x, bc_y))

        # Выгружаем, драйвер brother_ql сам перевернет это на 90 градусов (rotate='90')
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

print('Success sizing')
