import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

top_part = text.split("def generate_label_image")[0]
bot_part = text.split("threading.Thread(target=run_script, daemon=True).start()")[1]

new_code = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 7.0,   # Компактный "офисный" размер штрихкода как на идеальной этикетке
        "module_width": 0.4,    
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
        font_size = 50 # Идеальный компактный шрифт
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
            
        # ЖЕСТКАЯ ПРИВЯЗКА ШИРИНЫ К ЛЕНТЕ 62ММ (696 ПИКСЕЛЕЙ).
        # brother_ql при rotate='0' требует, чтобы ширина картинки до пикселя равнялась 696.
        canvas_w = 696 
        
        # Меняем "Epam" на "EPAm" как на эталонном фото (опционально, но пусть будет как на оригинале)
        top_text = f"EPAm {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)
        
        # Высота этикетки будет минимальной! Никаких гигантских отступов.
        # Лента просто отрежется нужной длины.
        margin_y = 25
        spacing = 10
        canvas_h = text_h + bc_img.height + spacing + (margin_y * 2) 
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        # Центрируем текст по оси X (ширина ленты)
        text_x = (canvas_w - text_w) // 2
        text_y = margin_y
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        # Центрируем штрихкод по оси X (ширина ленты)
        bc_x = (canvas_w - bc_img.width) // 2
        bc_y = text_y + text_h + spacing
        canvas.paste(bc_img, (bc_x, bc_y))

        # Сохраняем как есть (ширина 696, высота маленькая). НИКАКОГО ВРАЩЕНИЯ!
        canvas.save(output_path + ".png", "PNG", dpi=(300.0, 300.0))
        
        try:
            import os
            os.remove(temp_bc_full)
        except:
            pass
            
    except Exception as e:
        print("Ошибка генерации новой этикетки:", e)

def send_to_printer(text_data, status_widget, btn_widget=None):
    try:
        import barcode
        import PIL
        from PIL import Image
        if not hasattr(PIL.Image, 'ANTIALIAS'):
            PIL.Image.ANTIALIAS = getattr(PIL.Image, 'Resampling', PIL.Image).LANCZOS
    except ImportError:
        messagebox.showerror("Ошибка", "Для работы установите библиотеки: pip3 install python-barcode Pillow brother_ql")
        return

    status_widget.config(text="⏳ Идет отправка...", foreground="blue")
    if btn_widget:
        btn_widget.config(state=tk.DISABLED)

    def run_script():
        try:
            import re
            numbers = re.split(r'[,;\s]+', text_data)
            selected_printer = printer_var.get()
                
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                import os
                import tempfile
                import subprocess
                
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file)
                image_path = temp_file + ".png"
                bin_path = temp_file + ".bin"
                
                try:
                    import warnings
                    warnings.filterwarnings("ignore", category=DeprecationWarning)
                    from brother_ql.conversion import convert
                    from brother_ql.raster import BrotherQLRaster
                    
                    qlr = BrotherQLRaster('QL-810W')
                    
                    instructions = convert(
                        qlr=qlr, 
                        images=[image_path], 
                        label='62', # Лента 62mm
                        rotate='0', # НУЛЕВОЙ поворот! Наша картинка ровно 696px в ширину. 
                        threshold=70.0,
                        dither=False,
                        compress=True,
                        red=False
                    )
                    
                    with open(bin_path, 'wb') as f:
                        f.write(instructions)
                        
                    # -o raw передает машинный код в принтер без изменений!
                    cmd = ["lp", "-d", selected_printer, "-o", "raw", bin_path]
                except Exception as e:
                    print("Brother_ql error:", e)
                    cmd = ["lp", "-d", selected_printer, "-o", "fit-to-page", image_path]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    err_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка CUPS"
                    window.after(0, lambda e=err_msg: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\\n{e}"))
                
                try:
                    os.remove(image_path)
                    os.remove(bin_path)
                except:
                    pass
                    
            window.after(0, lambda: status_widget.config(text="✅ Успешно отправлено!", foreground="green"))
            window.after(3000, lambda: status_widget.config(text=""))
        except Exception as e:
            window.after(0, lambda e=e: messagebox.showerror("Системная ошибка", f"Детали:\\n{e}"))
            window.after(0, lambda: status_widget.config(text="❌ Ошибка", foreground="red"))
        finally:
            if btn_widget:
                window.after(0, lambda: btn_widget.config(state=tk.NORMAL))

    threading.Thread(target=run_script, daemon=True).start()'''

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(top_part + new_code + bot_part)

print('Success perfect label')
