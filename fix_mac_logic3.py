import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

top_part = text.split("def generate_label_image")[0]
bot_part = text.split("threading.Thread(target=run_script, daemon=True).start()")[1]

# Вставляем всё целиком руками
new_code = '''def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 13.0,
        "module_width": 0.8,
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
        font_size = 90
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
            
        canvas_h = 306
        top_text = f"Epam {text_str}"
        
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
        try:
            bbox = font.getbbox(top_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = dummy_draw.textsize(top_text, font=font)
        
        # Делаем длину ленты посимпатичнее. 
        margin = 100 # Отступы (пустое место) по краям ленты
        canvas_w = max(text_w, bc_img.width) + (margin * 2) 
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        text_x = (canvas_w - text_w) // 2
        text_y = 50 # Отступ от верхнего края ленты 29мм
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        bc_target_w = max(text_w, bc_img.width)
        bc_target_h = canvas_h - text_h - 100
        if bc_target_h > 0:
            bc_res = bc_img.resize((bc_target_w, bc_target_h), getattr(Image, 'Resampling', Image).NEAREST)
            bc_x = (canvas_w - bc_res.width) // 2
            bc_y = text_y + text_h + 10
            canvas.paste(bc_res, (bc_x, bc_y))

        # САМОЕ ГЛАВНОЕ: Разворачиваем холст!
        # После поворота ширина станет 306px (ширина ленты), а высота - canvas_w (длина ленты)
        canvas = canvas.rotate(90, expand=True)

        # Выгружаем картинку
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
        from PIL import Image
    except ImportError:
        messagebox.showerror("Ошибка", "Для работы установите библиотеки: pip3 install python-barcode Pillow")
        return

    status_widget.config(text="⏳ Идет отправка...", foreground="blue")
    if btn_widget:
        btn_widget.config(state=tk.DISABLED)

    def run_script():
        try:
            import re
            numbers = re.split(r'[,;\s]+', text_data)
            selected_printer = printer_var.get()
            
            media_opts = ""
            try:
                import subprocess
                out = subprocess.check_output(["lpoptions", "-p", selected_printer, "-l"], text=True)
                # Выискиваем формат 29mm, при этом избегаем 29x90 так как нам нужна гибкая длина ленты (по картинке)
                for line in out.splitlines():
                    if "PageSize" in line or "media" in line.lower():
                        opts = line.split(":")[-1].strip().split()
                        for opt in opts:
                            if "29" in opt and "90" not in opt:
                                media_opts = opt.replace("*", "")
                                break
                        if not media_opts:
                            # Фолбэк если есть только 29x90
                            for opt in opts:
                                if "29" in opt:
                                    media_opts = opt.replace("*", "")
                                    break
            except:
                pass
                
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                import os
                import tempfile
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file)
                image_path = temp_file + ".png"
                
                # Теперь картинка уже повернута программно как надо, поэтому landscape ВЫКЛЮЧЕН
                # fit-to-page тоже можно опустить или оставить, но оставим fit-to-page чтобы картинка массштабировалась строго в рамки 29мм
                cmd = ["lp", "-d", selected_printer]
                if media_opts:
                    cmd.extend(["-o", f"media={media_opts}"])
                else:
                    cmd.extend(["-o", "media=29mm"])
                    
                cmd.append(image_path)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    err_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка CUPS"
                    window.after(0, lambda e=err_msg: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\\n{e}"))
                
                try:
                    os.remove(image_path)
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

print('Success 3')
