import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import re
import tempfile

try:
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pass

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

def generate_label_image(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = {
        "write_text": True,
        "font_size": 14,
        "text_distance": 4,
        "module_height": 10.0,
        "quiet_zone": 3.0
    }
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(output_path, options=options)

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
            numbers = re.split(r'[,;\s]+', text_data)
            
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                generate_label_image(clean_num, temp_file)
                image_path = temp_file + ".png"
                
                selected_printer = printer_var.get()
                cmd = ["lpr", "-P", selected_printer, image_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    err_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка CUPS"
                    window.after(0, lambda e=err_msg: messagebox.showerror("Ошибка печати", f"Скрипт сообщил об ошибке:\n{e}"))
                    raise Exception("Ошибка принтера")
                
                try: os.remove(image_path)
                except: pass

            window.after(0, lambda: status_widget.config(text="✅ Отправлено в печать!", foreground="green"))
        except Exception as e:
            window.after(0, lambda err=e: status_widget.config(text=f"❌ Ошибка печати: {err}", foreground="red"))
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
        if not messagebox.askyesno("Подтверждение", f"Вы собираетесь отправить на печать {len(items_to_print)} этикеток!\n\nВы уверены, что хотите продолжить?"):
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
            mapping[parts[0]] = parts[1]
        elif len(parts) == 1 and i + 1 < len(raw_dict):
            next_line_parts = re.split(r'[\t,; ]+', raw_dict[i+1].strip())
            next_line_parts = [p for p in next_line_parts if p]
            if len(next_line_parts) >= 1:
                mapping[parts[0]] = next_line_parts[0]
            
    if sn in mapping:
        label = mapping[sn]
    elif sn.upper().startswith('S') and sn[1:] in mapping:
        label = mapping[sn[1:]]
    else:
        label = None

    if label:
        label = re.sub(r'[^\w\s\-,;]', '', label)
        threading.Thread(target=play_sound, args=("success",), daemon=True).start()
        send_to_printer(label, scan_status)
    else:
        threading.Thread(target=play_sound, args=("error",), daemon=True).start()
        scan_status.config(text=f"❌ SN не найден: {sn}", foreground="red")

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
window.geometry("500x520")
window.resizable(False, False)

style = ttk.Style()
if 'aqua' in style.theme_names():
    style.theme_use('aqua')
else:
    style.theme_use('default')

header = ttk.Label(window, text="🍏 Печать этикеток (Mac)", font=("Helvetica", 16, "bold"))
header.pack(pady=(10, 0))

# Блок выбора принтера (Выпадающий список)
printers_list = get_mac_printers()
default_p = next((p for p in printers_list if "QL" in p.upper() or "BROTHER" in p.upper()), printers_list[0])

printer_frame = ttk.Frame(window)
printer_frame.pack(fill=tk.X, padx=20, pady=5)
ttk.Label(printer_frame, text="Принтер:", font=("Helvetica", 10)).pack(side=tk.LEFT)
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
notebook.add(tab_scan, text=" 🔍 Сканер коробок (SN -> Label) ")
desc_dict = ttk.Label(tab_scan, text="1. Вставьте 2 колонки из Excel (SN и Label):", justify="center")
desc_dict.pack(pady=(10, 2))
dict_input = tk.Text(tab_scan, height=8, width=50, font=("Menlo", 12), wrap=tk.WORD)
dict_input.pack(pady=5, padx=20)
add_context_menu(dict_input)

desc_scan = ttk.Label(tab_scan, text="2. Кликните сюда и сканируйте SN с коробок:", justify="center")
desc_scan.pack(pady=(10, 2))
scan_entry = ttk.Entry(tab_scan, font=("Menlo", 14), width=35)
scan_entry.pack(pady=5)
scan_entry.bind("<Return>", on_scan)
scan_status = ttk.Label(tab_scan, text="", font=("Helvetica", 10))
scan_status.pack(pady=5)

window.mainloop()