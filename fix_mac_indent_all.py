import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# Питоновская регулярка давится из-за \s в replacement. Сделаем обычный сплит.
top_part = text.split("def send_to_printer")[0]
bot_part = text.split("threading.Thread(target=run_script, daemon=True).start()")[1]

func_code = '''def send_to_printer(text_data, status_widget, btn_widget=None):
    try:
        import barcode
        from PIL import Image
    except ImportError:
        messagebox.showerror("Ошибка", "Для работы установите библиотеки: pip3 install python-barcode Pillow brother_ql")
        return

    status_widget.config(text="⏳ Идет отправка...", foreground="blue")
    if btn_widget:
        btn_widget.config(state=tk.DISABLED)

    def run_script():
        try:
            numbers = re.split(r'[,;\s]+', text_data)
            
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file)
                image_path = temp_file + ".png"
                
                selected_printer = printer_var.get()
                
                try:
                    import os
                    from brother_ql.conversion import convert
                    from brother_ql.raster import BrotherQLRaster
                    
                    qlr = BrotherQLRaster('QL-810W')
                    qlr.exception_on_warning = True
                    
                    instructions = convert(
                        qlr=qlr, 
                        images=[image_path], 
                        label='29',
                        rotate='0',       
                        threshold=70.0,
                        dither=False,
                        compress=True,
                        red=False
                    )
                    
                    bin_path = image_path + ".bin"
                    with open(bin_path, 'wb') as f:
                        f.write(instructions)
                        
                    cmd = ["lpr", "-P", selected_printer, "-l", bin_path]
                except Exception as e:
                    print("brother_ql error:", e)
                    cmd = ["lpr", "-P", selected_printer, "-o", "natural-scaling=100", image_path]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    err_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка CUPS"
                    window.after(0, lambda e=err_msg: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\\n{e}"))
                
                try:
                    os.remove(image_path)
                    os.remove(image_path + ".bin")
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
    f.write(top_part + func_code + bot_part)

print("Indentation absolutely fixed")
