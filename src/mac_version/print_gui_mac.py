import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import os
import re
import tempfile
from datetime import datetime

try:
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    import barcode
    from barcode.writer import ImageWriter
    import PIL
    from PIL import Image, ImageDraw, ImageFont
    # Monkey-patch для совместимости brother_ql со свежими версиями Pillow
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = getattr(PIL.Image, 'Resampling', PIL.Image).LANCZOS
except ImportError:
    pass


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
LANGS = {
    "ru": {
        "title": "Печать этикеток",
        "printer": "Принтер:",
        "t_batch": " 📝 Список (Массовая) ",
        "d_batch": "Введите инвентарные номера (можно таблицей):",
        "btn_p": "Печать",
        "btn_f": "Печать",
        "t_scan": " 🔍 Сканер коробок / оборудования ",
        "d_dict": "1. Вставьте 2 колонки из Excel (SN и Label):",
        "d_scan": "2. Фокус сюда (перейдет автоматически) и сканируйте:",
        "t_inv": " 📋 Инвентаризация ",
        "i_top": "1. Вставьте базу (Label / Модель):",
        "btn_ld": "⚙️ Загрузить базу",
        "i_scan": "2. Сканируйте:",
        "btn_ex": "💾 Экспорт отчета в CSV",
        "c_stat": "Статус",
        "c_lbl": "Label (Инвентарный №)",
        "c_mod": "Модель",
        "s_pend": "❌ Ожидает",
        "s_found": "✅ Найдено",
        "s_stats": "Найдено:",
        "found_stat": "Найдено:"
    },
    "en": {
        "title": "Label Printing",
        "printer": "Printer:",
        "t_batch": " 📝 List (Batch) ",
        "d_batch": "Enter inventory numbers (table format supported):",
        "btn_p": "Print",
        "btn_f": "Print",
        "t_scan": " 🔍 Equipment Scanner ",
        "d_dict": "1. Paste 2 columns from Excel (SN and Label):",
        "d_scan": "2. Focus here (moves automatically) and scan:",
        "t_inv": " 📋 Inventory Audit ",
        "i_top": "1. Paste database (Label / Model):",
        "btn_ld": "⚙️ Load Database",
        "i_scan": "2. Scan:",
        "btn_ex": "💾 Export Report",
        "c_stat": "Status",
        "c_lbl": "Label (Inventory ID)",
        "c_mod": "Model",
        "s_pend": "❌ Pending",
        "s_found": "✅ Found",
        "s_stats": "Found:"
    }
}

def save_theme_pref(theme_name):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        data["theme"] = theme_name
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(data, f)
    except: pass

def load_theme_pref():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("theme", "system")
        except: pass
    return "system"

def apply_theme(theme_name):
    save_theme_pref(theme_name)
    if theme_name == "dark":
        bg_color = "#252526"
        fg_color = "#cccccc"
        accent_color = "#0e639c"
        accent_hover = "#1177bb"
        text_bg = "#1e1e1e"
        tab_inactive = "#2d2d2d"
        input_bg = "#3c3c3c"
        input_fg = "white"
    elif theme_name == "light":
        bg_color = "#f3f3f3"
        fg_color = "#333333"
        accent_color = "#007acc"
        accent_hover = "#005999"
        text_bg = "#ffffff"
        tab_inactive = "#e8e8e8"
        input_bg = "#ffffff"
        input_fg = "black"
    else:
        # system (macOS native)
        return

    window.configure(bg=bg_color)
    style.configure('.', background=bg_color, foreground=fg_color)
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, foreground=fg_color, font=("Helvetica", 10))
    style.configure('TButton', background=accent_color, foreground="black" if theme_name == "light" else "white")
    style.configure('Treeview', background=text_bg, fieldbackground=text_bg, foreground=input_fg)
    
    if 'text_input' in globals():
        text_input.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)
    if 'dict_input' in globals():
        dict_input.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)
    if 'inv_dict_input' in globals():
        inv_dict_input.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)
    if 'free_entry' in globals():
        free_entry.configure(bg=input_bg, fg=input_fg, insertbackground=input_fg)


def get_lang():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("lang", "ru")
        except: pass
    return "ru"

def save_lang(lang_code):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: data = json.load(f)
        data["lang"] = lang_code
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(data, f)
    except: pass
    update_texts(lang_code)

def check_for_updates():
    """ Пытается сделать git pull и сообщает результат """
    try:
        l = LANGS.get(current_lang, LANGS["ru"])
        update_btn.config(state="disabled")
        
        def run_git():
            try:
                import subprocess
                # Пытаемся получить изменения
                process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate(timeout=30)
                
                if "Already up to date" in stdout or "Уже обновлено" in stdout:
                    window.after(0, lambda: messagebox.showinfo("Update", l.get("upd_ok", "✅ Latest version!")))
                elif "Updating" in stdout or "Изменения:" in stdout or "Fast-forward" in stdout:
                    window.after(0, lambda: messagebox.showinfo("Update", "✅ Обновление загружено! Перезапустите программу.\nChanges downloaded! Please restart."))
                else:
                    window.after(0, lambda: messagebox.showwarning("Update", f"{l.get('upd_err', 'Error')}\n{stderr}"))
            except Exception as ex:
                window.after(0, lambda: messagebox.showerror("Update", f"Git error: {str(ex)}\nУбедитесь, что Git установлен."))
            finally:
                window.after(0, lambda: update_btn.config(state="normal"))

        import threading
        threading.Thread(target=run_git, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        update_btn.config(state="normal")

def update_texts(lang):
    global current_lang
    current_lang = lang
    l = LANGS[lang]
    header.config(text="🍏 " + l["title"] + " (Mac)")
    printer_lbl.config(text=l["printer"])
    notebook.tab(0, text=l["t_batch"])
    desc_batch.config(text=l["d_batch"])
    print_btn.config(text=l["btn_p"])
    notebook.tab(1, text=l["t_scan"])
    desc_dict.config(text=l["d_dict"])
    desc_scan.config(text=l["d_scan"])
    notebook.tab(2, text=l["t_inv"])
    inv_top_lbl.config(text=l["i_top"])
    btn_load.config(text=l["btn_ld"])
    inv_scan_lbl.config(text=l["i_scan"])
    btn_export.config(text=l["btn_ex"])
    inv_tree.heading("status", text=l["c_stat"])
    inv_tree.heading("sn", text=l["c_lbl"])
    inv_tree.heading("rest", text=l["c_mod"])
    
    try:
        notebook.tab(3, text=l.get("t_free", " 🔤 Direct Print "))
        desc_free.config(text=l.get("d_free", "Text (Inventory ID, custom name, etc):"))
        btn_free_print.config(text=l.get("btn_f", "Print Single Label"))
    except Exception:
        pass

    # Обновляем кнопку обновления
    try:
        update_btn.config(text=l.get("btn_upd", "🔄 Check for Updates"))
    except: pass

    # Обновляем названия меню
    try:
        menubar.entryconfig(1, label=l.get("m_theme", "Theme"))
        menubar.entryconfig(2, label=l.get("m_lang", "Language"))
        theme_menu.entryconfig(0, label=l.get("m_dark", "Dark"))
        theme_menu.entryconfig(1, label=l.get("m_light", "Light"))
    except: pass
        
    # Update inventory contents on lang switch
    if 'inv_tree' in globals() and 'inv_data' in globals():
        for sn, data in inv_data.items():
            if "???????" in data["status"] or "Found" in data["status"]:
                data["status"] = l["s_found"]
            else:
                data["status"] = l["s_pend"]
            inv_tree.set(data["item_id"], "status", data["status"])
        if 'update_inv_stats' in globals():
            update_inv_stats()

    update_inv_stats()


def get_mac_printers():
    """ Получает список всех системных принтеров через CUPS """
    try:
        result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
        # lpstat -a выводит строки вида: "Brother_QL_810W accepting requests since..."
        printers = [line.split()[0] for line in result.stdout.splitlines() if line]
        return printers if printers else ["Нет доступных принтеров"]
    except:
        return ["Ошибка_Поиска_Принтеров"]

def play_sound(sound_type):
    """ Воспроизводит системный звук на macOS """
    try:
        if sound_type == "success":
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
        else:
            subprocess.run(["afplay", "/System/Library/Sounds/Basso.aiff"], check=False)
    except:
        pass

def generate_label_image(text_str, output_path, use_epam=True, print_barcode=True):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": False,
        "module_height": 9.0,   
        "module_width": 0.5,    # Делаем сам штрихкод плотнее и компактнее
        "quiet_zone": 0.0,      # Отключаем встроенные отступы самого штрихкода!
    }
    
    temp_bc = output_path + "_bc"
    temp_bc_full = temp_bc + ".png"
    
    if print_barcode:
        my_bc = Code128(text_str, writer=ImageWriter())
        my_bc.save(temp_bc, options=options)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        if print_barcode:
            bc_img = Image.open(temp_bc_full)
        else:
            bc_img = Image.new('RGB', (0,0))
            
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
        top_text = f"EPAM {text_str}" if use_epam else f"{text_str}"
        
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
        
        if print_barcode:
            canvas_h = text_h + bc_img.height + spacing + (margin_y * 2)
        else:
            canvas_h = text_h + (margin_y * 2)
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        text_x = (canvas_w - text_w) // 2
        text_y = margin_y
        draw.text((text_x, text_y), top_text, fill="black", font=font)
        
        if print_barcode:
            bc_x = (canvas_w - bc_img.width) // 2
            bc_y = text_y + text_h + spacing
            canvas.paste(bc_img, (bc_x, bc_y))

        canvas.save(output_path + ".png", "PNG", dpi=(300.0, 300.0))
        
        if print_barcode:
            try:
                import os
                os.remove(temp_bc_full)
            except:
                pass
            
    except Exception as e:
        print("Ошибка генерации новой этикетки:", e)

def send_to_printer(text_data, status_widget, btn_widget=None, use_epam=True, print_barcode=True):
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
            selected_printer = printer_var.get()
            
            if isinstance(text_data, list):
                numbers = [str(n).strip() for n in text_data if str(n).strip()]
            else:
                numbers = [n.strip() for n in re.split(r'[,;\s]+', str(text_data)) if n.strip()]
                
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                import os
                import tempfile
                import subprocess
                
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file, use_epam=use_epam, print_barcode=print_barcode)
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
                    window.after(0, lambda e=err_msg: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\n{e}"))
                
                try:
                    os.remove(image_path)
                    os.remove(bin_path)
                except:
                    pass
                    
            # Подсистема Mac (CUPS) скрывает реальный статус железа около 30 секунд.
            # Самый надежный способ узнать завис ли принтер - проверить убывает ли очередь заданий:
            def get_queue_size():
                res = subprocess.run(["lpstat", "-o", selected_printer], capture_output=True, text=True).stdout
                return len([line for line in res.split('\n') if line.strip()])

            initial_jobs = get_queue_size()
            
            if initial_jobs == 0:
                # Очередь пуста моментально - принтер съел файл
                window.after(0, lambda: status_widget.config(text="✅ Успешно отправлено!", foreground="green"))
                window.after(3000, lambda: status_widget.config(text=""))
            else:
                import time
                time.sleep(2.0) # Ждем 2 секунды, чтобы дать принтеру шанс
                current_jobs = get_queue_size()
                
                if current_jobs >= initial_jobs:
                    # Принтер не смог забрать ни одного задания за 2 секунды - он выключен
                    # Очищаем очередь команд 
                    subprocess.run(["cancel", "-a", selected_printer], capture_output=True)
                    window.after(0, lambda: messagebox.showwarning(
                        "Принтер не отвечает", 
                        f"Задания зависли в системной очереди macOS.\n\n"
                        f"Принтер '{selected_printer}' выключен, находится в спящем режиме или потерял связь.\n"
                        "Все зависшие задания удалены, чтобы избежать случайной печати."
                    ))
                    window.after(0, lambda: status_widget.config(text="❌ Принтер Off-line", foreground="red"))
                else:
                    window.after(0, lambda: status_widget.config(text="✅ Успешно отправлено!", foreground="green"))
                    window.after(3000, lambda: status_widget.config(text=""))
        except Exception as e:
            window.after(0, lambda e=e: messagebox.showerror("Системная ошибка", f"Детали:\n{e}"))
            window.after(0, lambda: status_widget.config(text="❌ Ошибка", foreground="red"))
        finally:
            if btn_widget:
                window.after(0, lambda: btn_widget.config(state=tk.NORMAL))

    threading.Thread(target=run_script, daemon=True).start()

def print_batch():
    raw_text = text_input.get("1.0", tk.END).strip()
    text = re.sub(r'[^\w\s\-,;]', '', raw_text)
    if text != raw_text:
        text_input.delete("1.0", tk.END)
        text_input.insert("1.0", text)

    if not text:
        messagebox.showwarning("Внимание", "Пожалуйста, введите номера для печати.")
        return

    # Предотвращение случайного запуска огромной очереди печати
    items_to_print = [n for n in re.split(r'[,;\s]+', text) if n]
    if len(items_to_print) > 10:
        msg = f"Введено огромное количество номеров: {len(items_to_print)} шт.\n\nВы точно уверены, что хотите отправить их все на печать?"
        if not messagebox.askyesno("Защита от случайной печати", msg):
            return

    send_to_printer(text, batch_status, print_btn)

def on_scan(event):
    sn = scan_entry.get().strip()
    scan_entry.delete(0, tk.END)
    if not sn:
        return
        
    raw_dict = dict_input.get("1.0", tk.END).strip().splitlines()
    mapping = {}
    for i in range(len(raw_dict)):
        line = raw_dict[i].strip()
        if not line: continue
            
        parts = re.split(r'[\t,; ]+', line)
        parts = [p for p in parts if p]
        
        if len(parts) >= 2:
            mapping[parts[0]] = parts[-1]
            mapping[parts[-1]] = parts[0]
        elif len(parts) == 1 and i + 1 < len(raw_dict):
            next_line_parts = re.split(r'[\t,; ]+', raw_dict[i+1].strip())
            next_line_parts = [p for p in next_line_parts if p]
            if len(next_line_parts) >= 1:
                mapping[parts[0]] = next_line_parts[-1]
                mapping[next_line_parts[-1]] = parts[0]
            
    if sn in mapping:
        label = mapping[sn]
    elif sn.upper().startswith('S') and sn[1:] in mapping:
        label = mapping[sn[1:]]
    else:
        label = None
        # Поиск по подстроке: сканеры с оборудования часто выдают лишние префиксы или аппаратные суффиксы ревизии (например, букву 'F')
        for excel_sn, excel_label in mapping.items():
            if len(excel_sn) >= 5 and (excel_sn.upper() in sn.upper() or sn.upper() in excel_sn.upper()):
                label = excel_label
                break

    if label:
        label = re.sub(r'[^\w\s\-,;]', '', label)
        threading.Thread(target=play_sound, args=("success",), daemon=True).start()
        send_to_printer([label], scan_status)
    else:
        threading.Thread(target=play_sound, args=("error",), daemon=True).start()
        scan_status.config(text=f"❌ SN не найден: {sn}", foreground="red")
        
        if messagebox.askyesno("Штрихкод не найден", f"Штрихкод '{sn}' не найден в словаре.\nРаспечатать его как Инвентарный номер?"):
            sn_to_print = re.sub(r'[^\w\s\-,;]', '', sn)
            send_to_printer([sn_to_print], scan_status)
        
    return "break"

def add_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))
    
    # Правый клик на Mac (Button-2 или Button-3)
    widget.bind("<Button-2>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

window = tk.Tk()
window.title("Mac Label Printer")
window.geometry("540x570")
window.minsize(540, 570)
window.resizable(True, True)

style = ttk.Style()
if 'aqua' in style.theme_names():
    style.theme_use('aqua')
else:
    style.theme_use('default')

# Основное меню
menubar = tk.Menu(window)

theme_menu = tk.Menu(menubar, tearoff=0)
theme_menu.add_command(label="Системная (Auto)", command=lambda: apply_theme("system"))
theme_menu.add_command(label="Темная", command=lambda: apply_theme("dark"))
theme_menu.add_command(label="Светлая", command=lambda: apply_theme("light"))
menubar.add_cascade(label="Тема", menu=theme_menu)

lang_menu = tk.Menu(menubar, tearoff=0)
lang_menu.add_command(label="🇷🇺 Русский", command=lambda: save_lang("ru"))
lang_menu.add_command(label="🇬🇧 English", command=lambda: save_lang("en"))
menubar.add_cascade(label="Язык", menu=lang_menu)
window.config(menu=menubar)

header = ttk.Label(window, text="🍏 Печать этикеток (Mac)", font=("Helvetica", 16, "bold"))
header.pack(pady=(10, 0))

update_btn = ttk.Button(window, text="🔄 Проверить обновление", command=check_for_updates)
update_btn.pack(pady=(5, 5))

# Блок выбора принтера (Выпадающий список)
printers_list = get_mac_printers()
default_p = next((p for p in printers_list if "QL" in p.upper() or "BROTHER" in p.upper()), printers_list[0])

printer_frame = ttk.Frame(window)
printer_frame.pack(fill=tk.X, padx=20, pady=5)
printer_lbl = ttk.Label(printer_frame, text="Принтер:", font=("Helvetica", 10))
printer_lbl.pack(side=tk.LEFT)
printer_var = tk.StringVar(value=default_p)
printer_cb = ttk.Combobox(printer_frame, textvariable=printer_var, values=printers_list, state="readonly")
printer_cb.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(10, 0))

notebook = ttk.Notebook(window)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tab_batch = ttk.Frame(notebook)
notebook.add(tab_batch, text=" 📝 Список (Массовая) ")
desc_batch = ttk.Label(tab_batch, text="Введите инвентарные номера (можно таблицей):", justify="center")
desc_batch.pack(pady=(10, 5))
text_input = tk.Text(tab_batch, height=10, width=50, font=("Menlo", 12), wrap=tk.WORD)
text_input.pack(pady=5, padx=20)
add_context_menu(text_input)

print_btn = ttk.Button(tab_batch, text="Отправить на принтер", command=print_batch)
print_btn.pack(pady=(10, 5), ipadx=10, ipady=5)
batch_status = ttk.Label(tab_batch, text="", font=("Helvetica", 10))
batch_status.pack(pady=5)

tab_scan = ttk.Frame(notebook)
notebook.add(tab_scan, text=" 🔍 Сканер коробок / оборудования ")
desc_dict = ttk.Label(tab_scan, text="1. Вставьте 2 колонки из Excel (SN и Label):", justify="center")
desc_dict.pack(pady=(10, 2))

def auto_focus_scanner(event=None):
    window.after(100, lambda: scan_entry.focus())

dict_input = tk.Text(tab_scan, height=8, width=50, font=("Menlo", 12), wrap=tk.WORD)
dict_input.pack(pady=5, padx=20)
add_context_menu(dict_input)
dict_input.bind("<<Paste>>", auto_focus_scanner)

desc_scan = ttk.Label(tab_scan, text="2. Фокус сюда (перейдет автоматически) и сканируйте:", justify="center")
desc_scan.pack(pady=(10, 2))
scan_entry = ttk.Entry(tab_scan, font=("Menlo", 14), width=35)
scan_entry.pack(pady=5)
scan_entry.bind("<Return>", on_scan)
scan_status = ttk.Label(tab_scan, text="", font=("Helvetica", 10))
scan_status.pack(pady=5)

# --- ВКЛАДКА "ИНВЕНТАРИЗАЦИЯ" ---
tab_inv = ttk.Frame(notebook)
notebook.add(tab_inv, text=" 📋 Инвентаризация ")

inv_top_frame = ttk.Frame(tab_inv)
inv_top_frame.pack(fill=tk.X, padx=10, pady=5)

inv_top_lbl = ttk.Label(inv_top_frame, text="1. Вставьте базу (Label / Модель):")
inv_top_lbl.pack(side=tk.LEFT)

inv_dict_input = tk.Text(tab_inv, height=4, font=("Menlo", 12), wrap=tk.WORD, padx=10, pady=5)
inv_dict_input.pack(fill=tk.X, padx=10, pady=5)
add_context_menu(inv_dict_input)

inv_stats_var = tk.StringVar(value="Найдено: 0 / 0")
inv_data = {}
inv_items_map = {}

def load_inventory():
    raw_content = inv_dict_input.get("1.0", tk.END).strip()
    if not raw_content:
        messagebox.showwarning("Внимание", "Пожалуйста, вставьте список оборудования (базу) перед загрузкой.")
        return

    for item in inv_tree.get_children():
        inv_tree.delete(item)
    inv_data.clear()
    inv_items_map.clear()
    
    raw_text = raw_content.split('\n')
    for line in raw_text:
        parts = re.split(r'[\t,;]+', line.strip())
        parts = [p.strip() for p in parts if p.strip()]
        if not parts: continue
        
        if len(parts) == 1:
            sn = parts[0]
            rest = ""
        else:
            if (' ' in parts[0] and ' ' not in parts[-1]) or parts[-1].isdigit():
                sn = parts[-1]
                rest = " | ".join(parts[:-1])
            else:
                sn = parts[0]
                rest = " | ".join(parts[1:])
        
        
        status = "❌ Ожидает"
        item_id = inv_tree.insert("", tk.END, values=(status, sn, rest))
        
        inv_data[sn] = {"status": status, "sn": sn, "rest": rest, "item_id": item_id}
        inv_items_map[sn] = item_id

    update_inv_stats()
    inv_scan_entry.focus()

btn_load = ttk.Button(tab_inv, text="⚙️ Загрузить базу", command=load_inventory)
btn_load.pack(pady=2)

columns = ("status", "sn", "rest")
inv_tree = ttk.Treeview(tab_inv, columns=columns, show="headings", height=6)
inv_tree.heading("status", text="Статус")
inv_tree.heading("sn", text="Label (Инвентарный №)")
inv_tree.heading("rest", text="Модель")
inv_tree.column("status", width=80, anchor=tk.CENTER)
inv_tree.column("sn", width=150)
inv_tree.column("rest", width=200)
inv_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

inv_tree.tag_configure('found', background='#abf7b1', foreground='black')

inv_scan_frame = ttk.Frame(tab_inv)
inv_scan_frame.pack(fill=tk.X, padx=10, pady=5)

inv_scan_lbl = ttk.Label(inv_scan_frame, text="2. Сканируйте:")
inv_scan_lbl.pack(side=tk.LEFT)
inv_scan_entry = ttk.Entry(inv_scan_frame, font=("Menlo", 14), width=20)
inv_scan_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

ttk.Label(inv_scan_frame, textvariable=inv_stats_var, font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT)

def update_inv_stats():
    total = len(inv_data)
    found = sum(1 for v in inv_data.values() if "Найдено" in v["status"])
    inv_stats_var.set(f"Найдено: {found} / {total}")

def on_inv_scan(event):
    sn = inv_scan_entry.get().strip()
    inv_scan_entry.delete(0, tk.END)
    if not sn: return
    
    target_id = None
    if sn in inv_items_map:
        target_id = inv_items_map[sn]
    elif sn.upper().startswith('S') and sn[1:] in inv_items_map:
        target_id = inv_items_map[sn[1:]]
    else:
        for excel_sn, item_id in inv_items_map.items():
            if len(excel_sn) >= 5 and (excel_sn.upper() in sn.upper() or sn.upper() in excel_sn.upper()):
                target_id = item_id
                break
                
    if target_id:
        try:
            item_data = inv_tree.item(target_id)
            vals = item_data.get('values', [])
            sn_key = vals[1] if len(vals) > 1 else sn
            rest_key = vals[2] if len(vals) > 2 else ""
            
            inv_tree.item(target_id, values=("✅ Найдено", sn_key, rest_key), tags=('found',))
            
            for k, v in inv_data.items():
                if v['item_id'] == target_id:
                    v["status"] = "✅ Найдено"
                    break
                    
            inv_tree.see(target_id)
            update_inv_stats()
            threading.Thread(target=play_sound, args=("success",), daemon=True).start()
        except Exception as e:
            print(e)
    else:
        threading.Thread(target=play_sound, args=("error",), daemon=True).start()
        messagebox.showwarning("Не найдено", f"Оборудование не из списка!\nОтсканировано: {sn}")

    return "break"

inv_scan_entry.bind("<Return>", on_inv_scan)

def export_inventory():
    if not inv_data:
        messagebox.showinfo("Пусто", "Нет данных для экспорта.")
        return
        
    default_name = f"inventory_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    filepath = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV (Excel)", "*.csv")])
    if not filepath: return
    
    try:
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            import csv
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Status", "Label", "Model"])
            for item in inv_tree.get_children():
                writer.writerow(inv_tree.item(item)['values'])
        messagebox.showinfo("Сохранено", f"Отчет успешно сохранен для Excel в:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

btn_export = ttk.Button(tab_inv, text="💾 Экспорт отчета (Excel)", command=export_inventory)
btn_export.pack(pady=10)

# --- ВКЛАДКА "ПРОИЗВОЛЬНАЯ ПЕЧАТЬ" ---
tab_free = ttk.Frame(notebook)
notebook.add(tab_free, text=" 🔤 Произвольная ")

desc_free = ttk.Label(tab_free, text="Вставьте текст или список (разделяйте переносом строки):", justify="center")
desc_free.pack(pady=(10, 5))

free_entry = tk.Text(tab_free, height=8, width=50, font=("Menlo", 12), wrap=tk.WORD, relief=tk.FLAT, padx=10, pady=10)
free_entry.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
add_context_menu(free_entry)

free_status = ttk.Label(tab_free, text="", font=("Helvetica", 10))
free_status.pack(pady=5)

def on_free_print(event=None):
    raw_text = free_entry.get("1.0", tk.END).strip()
    if not raw_text: return
    
    lines = [line.strip() for line in re.split(r'[\n,;]+', raw_text) if line.strip()]
    
    clean_lines = []
    for line in lines:
        line = re.sub(r'[^\w\s\-\.,;]', '', line).strip()
        if line:
            clean_lines.append(line)
            
    if not clean_lines: return
    send_to_printer(clean_lines, free_status, use_epam=False, print_barcode=False)

btn_free_print = ttk.Button(tab_free, text="Напечатать", command=on_free_print)
btn_free_print.pack(pady=(5, 10), ipadx=10, ipady=5)

current_theme = load_theme_pref()
apply_theme(current_theme)
current_lang = get_lang()
update_texts(current_lang)
window.mainloop()