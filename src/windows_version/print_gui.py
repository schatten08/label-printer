import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import os
import re
import winsound
import ctypes
import sys
import json
from datetime import datetime

# --- Проверка на повторный запуск (Только для Windows) ---
mutex_name = "BrotherLabelPrinter_SingleInstanceMutex"
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
last_error = ctypes.windll.kernel32.GetLastError()
if last_error == 183:  # ERROR_ALREADY_EXISTS
    ctypes.windll.user32.MessageBoxW(0, "Программа уже запущена!\nПожалуйста, проверьте панель задач.", "Внимание", 0x30)
    sys.exit(0)

# Отвязываем значок на панели задач от базового процесса Python (чтобы можно было закрепить именно программу)
try:
    myappid = 'brother.label.printer.gui.1_4'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def get_windows_printers():
    try:
        import win32com.client
        p = win32com.client.Dispatch("bpac.Printer")
        printers = p.GetInstalledPrinters()
        if printers:
            return list(printers)
    except ImportError:
        pass # Fallback to PowerShell if pywin32 is not installed yet
    except Exception:
        pass

    try:
        cmd = ["powershell", "-NoProfile", "-Command", "Get-Printer | Select-Object -ExpandProperty Name"]
        # Используем cp866 для кириллических имен принтеров в русской Windows
        # creationflags=0x08000000 предотвращает моргание черного окна консоли
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="cp866", creationflags=0x08000000)
        printers = [p.strip() for p in result.stdout.splitlines() if p.strip()]
        return printers if printers else ["Принтеры не найдены"]
    except Exception:
        return ["Ошибка поиска принтеров"]

def send_to_printer(text, status_widget, btn_widget=None):
    selected_printer = printer_var.get()
    status_widget.config(text="⏳ Идет отправка...", foreground="blue")
    if btn_widget:
        btn_widget.config(state=tk.DISABLED)

    def run_script():
        try:
            try:
                import win32com.client
                import pythoncom
                # Для работы с COM-объектами в отдельном фоновом потоке Python обязательна инициализация!
                pythoncom.CoInitialize() 
            except ImportError:
                window.after(0, lambda: messagebox.showerror(
                    "Необходима билиотека", 
                    "Для работы Windows-версии приложения на чистом Python теперь требуется библиотека pywin32.\n\n"
                    "Закройте приложение, откройте консоль от имени Администратора (или просто терминал) и введите команду:\n\n"
                    "pip install pywin32\n\n"
                    "После установки запустите приложение снова."
                ))
                window.after(0, lambda: status_widget.config(text="❌ Отсутствует pywin32", foreground="red"))
                return

            import re
            numbers = [n.strip() for n in re.split(r'[,;\s]+', text) if n.strip()]
            if not numbers:
                return

            doc = win32com.client.Dispatch("bpac.Document")
            
            # Предварительная проверка включен ли принтер
            try:
                printer_checker = win32com.client.Dispatch("bpac.Printer")
                if not printer_checker.IsPrinterOnline(selected_printer):
                    window.after(0, lambda: messagebox.showwarning("Принтер недоступен", f"Принтер '{selected_printer}' выключен или не подключен.\n\nПожалуйста, включите устройство и проверьте USB/Wi-Fi соединение."))
                    window.after(0, lambda: status_widget.config(text="❌ Принтер Off-line", foreground="red"))
                    return
            except Exception as e:
                print("Skipping online check:", e)

            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, "Label.lbx")

            if not doc.Open(template_path):
                window.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось открыть файл шаблона:\n{template_path}"))
                window.after(0, lambda: status_widget.config(text="❌ Ошибка шаблона", foreground="red"))
                return

            # Выставляем принтер
            doc.SetPrinter(selected_printer, False)
            
            # Открываем канал печати 1 раз (Пакетная печать быстрее)
            doc.StartPrint("Batch Labels", 0)

            for num in numbers:
                lbl = doc.GetObject("Label")
                if lbl:
                    lbl.Text = num
                
                bc = doc.GetObject("BarCode")
                if bc:
                    bc.Text = num
                
                # Закидываем в очередь печати 1 копию и переходим к следующему
                doc.PrintOut(1, 0)
                
            # Из-за особенностей библиотеки pywin32, некоторые функции без параметров могут возвращаться как переменные (свойства)
            if callable(doc.EndPrint): doc.EndPrint()
            else: _ = doc.EndPrint
            
            if callable(doc.Close): doc.Close()
            else: _ = doc.Close

            window.after(0, lambda: status_widget.config(text=f"✅ Напечатано: {len(numbers)} шт.", foreground="green"))
            
        except Exception as e:
            window.after(0, lambda err=e: messagebox.showerror("Системная ошибка", f"Ошибка COM-объекта bPAC:\n{err}"))
            window.after(0, lambda err=e: status_widget.config(text=f"❌ Ошибка", foreground="red"))
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass
                
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
        if not line:
            continue
            
        # Пытаемся разбить строку по пробелам/табам/запятым (если вставили в одну строку из Excel)
        parts = re.split(r'[\t,; ]+', line)
        parts = [p for p in parts if p]
        
        if len(parts) >= 2:
            # Классический случай: "SN Label" в одной строке
            mapping[parts[0]] = parts[1]
        elif len(parts) == 1 and i + 1 < len(raw_dict):
            # Случай вертикальной вставки: "SN" на одной строке, "Label" на следующей
            next_line_parts = re.split(r'[\t,; ]+', raw_dict[i+1].strip())
            next_line_parts = [p for p in next_line_parts if p]
            
            if len(next_line_parts) >= 1:
                mapping[parts[0]] = next_line_parts[0]
            
    # Умный поиск: точное совпадение ИЛИ совпадение без префикса 'S'
    if sn in mapping:
        label = mapping[sn]
    elif sn.upper().startswith('S') and sn[1:] in mapping:
        label = mapping[sn[1:]]
    else:
        label = None
        # Поиск по подстроке: сканеры с оборудования часто выдают лишние префиксы или аппаратные суффиксы ревизии (например, букву/суффикс 'F')
        for excel_sn, excel_label in mapping.items():
            if len(excel_sn) >= 5 and (excel_sn.upper() in sn.upper() or sn.upper() in excel_sn.upper()):
                label = excel_label
                break

    if label:
        label = re.sub(r'[^\w\s\-,;]', '', label)
        # Звук успешного сканирования (высокий и короткий "Пик")
        threading.Thread(target=lambda: winsound.Beep(2000, 150), daemon=True).start()
        send_to_printer(label, scan_status)
    else:
        # Звук ошибки (низкий и длинный "Бууп")
        threading.Thread(target=lambda: winsound.Beep(500, 400), daemon=True).start()
        scan_status.config(text=f"❌ SN не найден: {sn}", foreground="red")

def add_context_menu(widget):
    """ Додаем контекстное меню (ПКМ) и чиним Ctrl+V для русской раскладки """
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))
    
    # Показ меню по клику правой кнопкой
    widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    
    # Модификатор для русской раскладки клавиатуры (перехват по keycode вместо символа)
    def check_paste(event):
        if event.state & 4 and event.keycode == 86: # 4 = Ctrl, 86 = V (независимо от языка)
            widget.event_generate("<<Paste>>")
            return "break"
            
    widget.bind("<KeyPress>", check_paste, add="+")

window = tk.Tk()
window.title("Печать этикеток Brother")
window.geometry("540x570")
window.minsize(540, 570)
window.resizable(True, True)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_theme_pref():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("theme", "light")
        except Exception:
            pass
    return "light"

def save_theme_pref(theme_name):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["theme"] = theme_name
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

style = ttk.Style()
if 'clam' in style.theme_names():
    style.theme_use('clam')


LANGS = {
    "ru": {
        "title": "Печать этикеток",
        "printer": "Принтер:",
        "t_batch": " 📝 Список (Массовая) ",
        "d_batch": "Введите инвентарные номера (можно таблицей):",
        "btn_p": "Отправить на принтер",
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
        "c_mod": "Модель"
    },
    "en": {
        "title": "Label Printing",
        "printer": "Printer:",
        "t_batch": " 📝 List (Batch) ",
        "d_batch": "Enter inventory numbers (table format supported):",
        "btn_p": "Send to Printer",
        "t_scan": " 🔍 Equipment Scanner ",
        "d_dict": "1. Paste 2 columns from Excel (SN and Label):",
        "d_scan": "2. Focus here (moves automatically) and scan:",
        "t_inv": " 📋 Inventory Audit ",
        "i_top": "1. Paste database (Label / Model):",
        "btn_ld": "⚙️ Load Database",
        "i_scan": "2. Scan:",
        "btn_ex": "💾 Export to CSV",
        "c_stat": "Status",
        "c_lbl": "Label (Inventory ID)",
        "c_mod": "Model",
        "s_pend": "? Pending",
        "s_found": "? Found",
        "s_stats": "Found:",
        "found_stat": "Found:"
    }
}
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

def update_texts(lang):
    global current_lang
    current_lang = lang
    l = LANGS[lang]
    header.config(text="🖨️ " + l["title"])
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
    else:
        bg_color = "#f3f3f3"
        fg_color = "#333333"
        accent_color = "#007acc"
        accent_hover = "#005999"
        text_bg = "#ffffff"
        tab_inactive = "#e8e8e8"
        input_bg = "#ffffff"
        input_fg = "black"

    window.configure(bg=bg_color)
    style.configure('.', background=bg_color, foreground=fg_color)
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
    style.configure('TButton', background=accent_color, foreground="white", font=("Segoe UI", 10, "bold"), padding=6, borderwidth=0)
    style.map('TButton', background=[('active', accent_hover)])

    style.configure('TCombobox', fieldbackground=input_bg, background=bg_color, foreground=input_fg, arrowcolor=fg_color, padding=5)
    style.map('TCombobox', fieldbackground=[('readonly', input_bg)], selectbackground=[('readonly', accent_color)], foreground=[('readonly', input_fg)])
    style.configure('TEntry', fieldbackground=input_bg, foreground=input_fg, insertcolor=input_fg, padding=6)

    style.configure('Treeview', background=text_bg, foreground=input_fg, fieldbackground=text_bg, borderwidth=0)
    style.configure('Treeview.Heading', background=tab_inactive, foreground=fg_color, font=("Segoe UI" if "win" in sys.platform else "Helvetica", 10, "bold"))
    style.map('Treeview.Heading', background=[('active', bg_color)])
    style.map('Treeview', background=[('selected', accent_color)], foreground=[('selected', 'white')])


    # Настраиваем желтый/оранжевый цвет для предупреждения, зависящий от темы
    warning_color = "#e6a200" if theme_name == "dark" else "#d97706"
    style.configure('Warning.TLabel', background=bg_color, foreground=warning_color, font=("Segoe UI", 9, "italic", "bold"))

    style.configure('TNotebook', background=bg_color, borderwidth=0)
    style.configure('TNotebook.Tab', background=tab_inactive, foreground=fg_color, padding=[15, 5], font=("Segoe UI", 10))
    style.map('TNotebook.Tab', background=[('selected', text_bg), ('active', '#333333' if theme_name=="dark" else '#d4d4d4')], foreground=[('selected', input_fg)])

    try:
        text_input.config(bg=text_bg, fg=input_fg, insertbackground=input_fg)
        dict_input.config(bg=text_bg, fg=input_fg, insertbackground=input_fg)
        inv_dict_input.config(bg=text_bg, fg=input_fg, insertbackground=input_fg)
    except NameError:
        pass

# Основное меню
menubar = tk.Menu(window)
theme_menu = tk.Menu(menubar, tearoff=0)
theme_menu.add_command(label="Темная", command=lambda: apply_theme("dark"))
theme_menu.add_command(label="Светлая", command=lambda: apply_theme("light"))
menubar.add_cascade(label="Тема", menu=theme_menu)

lang_menu = tk.Menu(menubar, tearoff=0)
lang_menu.add_command(label="🇷🇺 Русский", command=lambda: save_lang("ru"))
lang_menu.add_command(label="🇬🇧 English", command=lambda: save_lang("en"))
menubar.add_cascade(label="Язык", menu=lang_menu)

window.config(menu=menubar)

current_theme = load_theme_pref()
apply_theme(current_theme) # Инициализация сохраненной темы

header = ttk.Label(window, text="🖨️ Печать этикеток", font=("Segoe UI", 16, "bold"))
header.pack(pady=(10, 0))

# Блок выбора принтера (Выпадающий список)
printers_list = get_windows_printers()
default_p = next((p for p in printers_list if "QL" in p.upper() or "BROTHER" in p.upper()), printers_list[0])

printer_frame = ttk.Frame(window)
printer_frame.pack(fill=tk.X, padx=20, pady=5)
printer_lbl = ttk.Label(printer_frame, text="Принтер:", font=("Segoe UI", 10))
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

text_input = tk.Text(tab_batch, height=10, width=50, font=("Consolas", 11), wrap=tk.WORD, relief=tk.FLAT, padx=10, pady=10)
text_input.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
add_context_menu(text_input)

print_btn = ttk.Button(tab_batch, text="Отправить на принтер", command=print_batch)
print_btn.pack(pady=(10, 5), ipadx=10, ipady=5)

batch_status = ttk.Label(tab_batch, text="", font=("Segoe UI", 10))
batch_status.pack(pady=5)

tab_scan = ttk.Frame(notebook)
notebook.add(tab_scan, text=" 🔍 Сканер коробок / оборудования ")

def auto_focus_scanner(event=None):
    # Автоматически переводим фокус на строку сканирования (с задержкой, чтобы вставка сработала)
    window.after(100, lambda: scan_entry.focus())

desc_dict = ttk.Label(tab_scan, text="1. Вставьте 2 колонки из Excel (SN и Label):", justify="center")
desc_dict.pack(pady=(10, 2))

dict_input = tk.Text(tab_scan, height=8, width=50, font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT, padx=10, pady=10)
dict_input.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
add_context_menu(dict_input)
dict_input.bind("<<Paste>>", auto_focus_scanner)

desc_scan = ttk.Label(tab_scan, text="2. Фокус сюда (перейдет автоматически) и сканируйте:", justify="center")
desc_scan.pack(pady=(10, 2))

scan_entry = ttk.Entry(tab_scan, font=("Consolas", 14), width=35)
scan_entry.pack(pady=5)
scan_entry.bind("<Return>", on_scan)

scan_status = ttk.Label(tab_scan, text="", font=("Segoe UI", 10))
scan_status.pack(pady=5)

# --- ВКЛАДКА "ИНВЕНТАРИЗАЦИЯ" ---
tab_inv = ttk.Frame(notebook)
notebook.add(tab_inv, text=" 📋 Инвентаризация ")

inv_top_frame = ttk.Frame(tab_inv)
inv_top_frame.pack(fill=tk.X, padx=10, pady=5)

inv_top_lbl = ttk.Label(inv_top_frame, text="1. Вставьте базу (Label / Модель):")
inv_top_lbl.pack(side=tk.LEFT)

inv_dict_input = tk.Text(tab_inv, height=4, font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT, padx=10, pady=5)
inv_dict_input.pack(fill=tk.X, padx=10, pady=5)
add_context_menu(inv_dict_input)

inv_stats_var = tk.StringVar(value="Найдено: 0 / 0")
inv_data = {} # Справочник инвентаризации
inv_items_map = {} # Связь Label -> Treeview Item ID

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
        parts = re.split(r'[\t,;]+', line.strip()) # Разделяем по табам или точкам с запятой
        parts = [p.strip() for p in parts if p.strip()]
        if not parts: continue
        
        if len(parts) == 1:
            sn = parts[0]
            rest = ""
        else:
            # Если первый элемент содержит пробелы (длинное название), 
            # а последний без пробелов или состоит только из цифр, то считаем последний штрихкодом.
            if (' ' in parts[0] and ' ' not in parts[-1]) or parts[-1].isdigit():
                sn = parts[-1]
                rest = " | ".join(parts[:-1])
            else:
                sn = parts[0]
                rest = " | ".join(parts[1:])
        
        
        status = "❌ Ожидает"
        item_id = inv_tree.insert("", tk.END, values=(status, sn, rest))
        
        # Сохраняем в память
        inv_data[sn] = {
            "status": status,
            "sn": sn,
            "rest": rest,
            "item_id": item_id
        }
        inv_items_map[sn] = item_id

    update_inv_stats()
    inv_scan_entry.focus()

btn_load = ttk.Button(tab_inv, text="⚙️ Загрузить базу", command=load_inventory)
btn_load.pack(pady=2)

# Таблица инвентаризации
columns = ("status", "sn", "rest")
inv_tree = ttk.Treeview(tab_inv, columns=columns, show="headings", height=8)
inv_tree.heading("status", text="Статус")
inv_tree.heading("sn", text="Label (Инвентарный №)")
inv_tree.heading("rest", text="Модель")
inv_tree.column("status", width=80, anchor=tk.CENTER)
inv_tree.column("sn", width=150)
inv_tree.column("rest", width=220)
inv_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Тег для подсветки найденных строк (светло-зеленый)
inv_tree.tag_configure('found', background='#abf7b1', foreground='black')

inv_scan_frame = ttk.Frame(tab_inv)
inv_scan_frame.pack(fill=tk.X, padx=10, pady=5)

inv_scan_lbl = ttk.Label(inv_scan_frame, text="2. Сканируйте:")
inv_scan_lbl.pack(side=tk.LEFT)
inv_scan_entry = ttk.Entry(inv_scan_frame, font=("Consolas", 14), width=25)
inv_scan_entry.pack(side=tk.LEFT, padx=10)

ttk.Label(inv_scan_frame, textvariable=inv_stats_var, font=("Segoe UI", 10, "bold")).pack(side=tk.RIGHT)

def update_inv_stats():
    total = len(inv_data)
    found = sum(1 for v in inv_data.values() if "Найдено" in v["status"])
    inv_stats_var.set(f"Найдено: {found} / {total}")

def on_inv_scan(event):
    sn = inv_scan_entry.get().strip()
    inv_scan_entry.delete(0, tk.END)
    if not sn: return
    
    target_id = None
    
    # Прямой поиск
    if sn in inv_items_map:
        target_id = inv_items_map[sn]
    elif sn.upper().startswith('S') and sn[1:] in inv_items_map:
        target_id = inv_items_map[sn[1:]]
    else:
        # Умный поиск (подстрока от 5 символов)
        for excel_sn, item_id in inv_items_map.items():
            if len(excel_sn) >= 5 and (excel_sn.upper() in sn.upper() or sn.upper() in excel_sn.upper()):
                target_id = item_id
                break
                
    if target_id:
        item_data = inv_tree.item(target_id)
        sn_key = item_data['values'][1] # Достаем оригинальный отображаемый SN
        
        # Закрашиваем строку и меняем статус
        inv_tree.item(target_id, values=("✅ Найдено", sn_key, item_data['values'][2]), tags=('found',))
        
        # Обновляем память
        for k, v in inv_data.items():
            if v['item_id'] == target_id:
                v["status"] = "✅ Найдено"
                break
                
        inv_tree.see(target_id)
        update_inv_stats()
        threading.Thread(target=lambda: winsound.Beep(2000, 150), daemon=True).start()
    else:
        threading.Thread(target=lambda: winsound.Beep(500, 400), daemon=True).start()
        messagebox.showwarning("Не найдено", f"Оборудование не из списка!\nОтсканировано: {sn}")

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

apply_theme(current_theme) # Применяем вторично, чтобы обновить цвета у tk.Text после их создания
current_lang = get_lang()
update_texts(current_lang)
window.mainloop()