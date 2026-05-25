import codecs
import re

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# Мы просто аккуратно перезапишем всю функцию send_to_printer
top_part = text.split("def send_to_printer")[0]
bot_part = text.split("threading.Thread(target=run_script, daemon=True).start()")[1]

# Вернем генерацию PNG, и уберем фигню с PDF
func_code = '''def send_to_printer(text_data, status_widget, btn_widget=None):
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
            numbers = re.split(r'[,;\s]+', text_data)
            selected_printer = printer_var.get()
            
            # Читаем доступные размеры ленты из драйвера принтера!
            media_opts = ""
            try:
                out = subprocess.check_output(["lpoptions", "-p", selected_printer, "-l"], text=True)
                # Ищем что-то похожее на 29mm
                for line in out.splitlines():
                    if "PageSize" in line or "media" in line.lower():
                        # Ищем опцию для 29mm (напр. 29mm, 29x90, 29x90mm, 29x15_24)
                        opts = line.split(":")[-1].strip().split()
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
                
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file)
                image_path = temp_file + ".png"
                
                # Печатаем через lp с точным указанием размера ленты
                # Если media_opts найден, принтер перестанет моргать красным, т.к. размер совпадет с установленным
                cmd = ["lp", "-d", selected_printer, "-o", "fit-to-page"]
                if media_opts:
                    cmd.extend(["-o", f"media={media_opts}"])
                else:
                    # Резервный вариант, если в lpoptions ничего не нашли
                    cmd.extend(["-o", "media=29x90mm"])
                    
                cmd.append(image_path)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    err_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка CUPS"
                    window.after(0, lambda e=err_msg: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\\n{e}"))
                
                try:
                    import os
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
    f.write(top_part + func_code + bot_part)
