import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# 1. Update GUI to include Tape selector
# Find printer_cb pack line to insert after
gui_insertion_pattern = r'printer_cb\.pack\(.*?padx=\(10, 0\)\)'
gui_addition = '''
tape_frame = ttk.Frame(window)
tape_frame.pack(fill=tk.X, padx=20, pady=2)
tape_lbl = ttk.Label(tape_frame, text="Ширина ленты:", font=("Helvetica", 10))
tape_lbl.pack(side=tk.LEFT)
# Выводим в глобальную область, чтобы ее видела функция!
global tape_var 
tape_var = tk.StringVar(value="29mm (DK-22210)")
tape_cb = ttk.Combobox(tape_frame, textvariable=tape_var, values=["29mm (DK-22210)", "62mm (DK-22212)"], state="readonly")
tape_cb.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(10, 0))
'''
text = re.sub(gui_insertion_pattern, lambda m: m.group(0) + "\n" + gui_addition, text)

# 2. Update generate_label_image to accept is_62mm
bot_part = text.split("def send_to_printer")[1]
top_part = text.split("def generate_label_image")[0]

new_code = '''def generate_label_image(text_str, output_path, is_62mm=False):
    Code128 = barcode.get_barcode_class('code128')
    
    if is_62mm:
        # Настройки для широкой 62мм ленты (печать ПОПЕРЕК)
        options = {
            "write_text": False,
            "module_height": 18.0,
            "module_width": 1.0,
            "quiet_zone": 1.0,
        }
    else:
        # Настройки для узкой 29мм ленты (печать ВДОЛЬ как на Windows)
        options = {
            "write_text": False,
            "module_height": 13.0,
            "module_width": 0.8,
            "quiet_zone": 0.0,
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
        
        font_size = 100 if is_62mm else 75
        
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
            
        top_text = f"EPAM {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)

        if is_62mm:
            # 62mm: картинка ровно 696px по ширине, отрезка по высоте
            canvas_w = 696 
            margin_y = 15
            spacing = 5
            
            bc_target_w = max(int(text_w * 1.1), bc_img.width)
            bc_target_w = min(bc_target_w, canvas_w - 40)
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

            # Для 62мм мы НЕ вращаем картинку (rotate='0' in brother_ql)
            canvas.save(output_path + ".png", "PNG", dpi=(300.0, 300.0))
            
        else:
            # 29mm: Печать идет ВДОЛЬ ленты!
            canvas_h = 306 # Высота ленты 29мм = 306 пикселей
            margin_x = 40  # Отступы по ширине (длине отрезаемой этикетки)
            spacing = 10
            
            # Холст подстраивается под длину штрихкода/текста
            canvas_w = max(text_w, bc_img.width) + (margin_x * 2)
            canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
            draw = ImageDraw.Draw(canvas)
            
            # Центрируем текст и штрихкод по вертикали
            content_h = text_h + spacing + bc_img.height
            start_y = (canvas_h - content_h) // 2
            
            text_x = (canvas_w - text_w) // 2
            text_y = start_y
            draw.text((text_x, text_y), top_text, fill="black", font=font)
            
            bc_x = (canvas_w - bc_img.width) // 2
            bc_y = text_y + text_h + spacing
            canvas.paste(bc_img, (bc_x, bc_y))
            
            # Внимание: для 29мм мы сохраняем как есть (широкую картинку),
            # А В BROTHER_QL ПЕРЕДАДИМ rotate='90'
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
            
            # Вытягиваем выбранную размерность прямо из UI
            is_62mm = "62" in tape_var.get()
                
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                import os
                import tempfile
                import subprocess
                
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file, is_62mm)
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
                        label='62' if is_62mm else '29', 
                        rotate='0' if is_62mm else '90', 
                        threshold=70.0,
                        dither=False,
                        compress=True,
                        red=False
                    )
                    
                    with open(bin_path, 'wb') as f:
                        f.write(instructions)
                        
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

print('Success ultimate')
