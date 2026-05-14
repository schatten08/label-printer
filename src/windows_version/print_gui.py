import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import re
import winsound
import ctypes
import sys

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
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ps_script = os.path.join(script_dir, "print.ps1")
            
            cmd = [
                "powershell.exe", "-ExecutionPolicy", "Bypass", 
                "-WindowStyle", "Hidden", "-File", ps_script, 
                "-Text1", text, "-PrinterName", selected_printer
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="cp866")

            if result.returncode == 0:
                window.after(0, lambda: status_widget.config(text=f"✅ Напечатано: {text}", foreground="green"))
            else:
                err_msg = result.stdout.strip() if result.stdout else "Неизвестная ошибка принтера"
                window.after(0, lambda: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\n{err_msg}"))
                window.after(0, lambda: status_widget.config(text="❌ Ошибка принтера", foreground="red"))
        except Exception as e:
            window.after(0, lambda err=e: status_widget.config(text=f"❌ Ошибка: {err}", foreground="red"))
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
window.geometry("520x540")
window.resizable(False, False)

style = ttk.Style()
if 'clam' in style.theme_names():
    style.theme_use('clam')

def apply_theme(theme_name):
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

    style.configure('TCombobox', fieldbackground=input_bg, background=bg_color, foreground=input_fg, arrowcolor=fg_color)
    style.map('TCombobox', fieldbackground=[('readonly', input_bg)], selectbackground=[('readonly', accent_color)], foreground=[('readonly', input_fg)])
    style.configure('TEntry', fieldbackground=input_bg, foreground=input_fg, insertcolor=input_fg)

    style.configure('TNotebook', background=bg_color, borderwidth=0)
    style.configure('TNotebook.Tab', background=tab_inactive, foreground=fg_color, padding=[15, 5], font=("Segoe UI", 10))
    style.map('TNotebook.Tab', background=[('selected', text_bg), ('active', '#333333' if theme_name=="dark" else '#d4d4d4')], foreground=[('selected', input_fg)])

    try:
        text_input.config(bg=text_bg, fg=input_fg, insertbackground=input_fg)
        dict_input.config(bg=text_bg, fg=input_fg, insertbackground=input_fg)
    except NameError:
        pass

# Основное меню
menubar = tk.Menu(window)
theme_menu = tk.Menu(menubar, tearoff=0)
theme_menu.add_command(label="Темная (VS Code)", command=lambda: apply_theme("dark"))
theme_menu.add_command(label="Светлая", command=lambda: apply_theme("light"))
menubar.add_cascade(label="Тема", menu=theme_menu)
window.config(menu=menubar)

apply_theme("light") # Инициализация светлой темы по умолчанию

header = ttk.Label(window, text="🖨️ Печать этикеток", font=("Segoe UI", 16, "bold"))
header.pack(pady=(10, 0))

# Блок выбора принтера (Выпадающий список)
printers_list = get_windows_printers()
default_p = next((p for p in printers_list if "QL" in p.upper() or "BROTHER" in p.upper()), printers_list[0])

printer_frame = ttk.Frame(window)
printer_frame.pack(fill=tk.X, padx=20, pady=5)
ttk.Label(printer_frame, text="Принтер:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
printer_var = tk.StringVar(value=default_p)
printer_cb = ttk.Combobox(printer_frame, textvariable=printer_var, values=printers_list, state="readonly")
printer_cb.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(10, 0))

notebook = ttk.Notebook(window)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tab_batch = ttk.Frame(notebook)
notebook.add(tab_batch, text=" 📝 Список (Массовая) ")

desc_batch = ttk.Label(tab_batch, text="Введите инвентарные номера (можно таблицей):", justify="center")
desc_batch.pack(pady=(10, 5))

text_input = tk.Text(tab_batch, height=10, width=50, font=("Consolas", 11), wrap=tk.WORD, relief=tk.FLAT)
text_input.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
add_context_menu(text_input)

print_btn = ttk.Button(tab_batch, text="Отправить на принтер", command=print_batch)
print_btn.pack(pady=(10, 5), ipadx=10, ipady=5)

batch_status = ttk.Label(tab_batch, text="", font=("Segoe UI", 10))
batch_status.pack(pady=5)

tab_scan = ttk.Frame(notebook)
notebook.add(tab_scan, text=" 🔍 Сканер коробок (SN -> Label) ")

desc_dict = ttk.Label(tab_scan, text="1. Вставьте 2 колонки из Excel (SN и Label):", justify="center")
desc_dict.pack(pady=(10, 2))

dict_input = tk.Text(tab_scan, height=8, width=50, font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT)
dict_input.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
add_context_menu(dict_input)

desc_scan = ttk.Label(tab_scan, text="2. Кликните сюда и сканируйте SN с коробок:", justify="center")
desc_scan.pack(pady=(10, 2))

scan_entry = ttk.Entry(tab_scan, font=("Consolas", 14), width=35)
scan_entry.pack(pady=5)
scan_entry.bind("<Return>", on_scan)

scan_status = ttk.Label(tab_scan, text="", font=("Segoe UI", 10))
scan_status.pack(pady=5)

apply_theme("light") # Применяем вторично, чтобы обновить цвета у tk.Text после их создания
window.mainloop()