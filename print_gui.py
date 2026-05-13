import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import re

def send_to_printer(text, status_widget, btn_widget=None):
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
                "-Text1", text
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="cp866")

            if result.returncode == 0:
                window.after(0, lambda: status_widget.config(text=f"✅ Напечатано: {text}", foreground="green"))
            else:
                window.after(0, lambda: status_widget.config(text="❌ Ошибка при печати", foreground="red"))
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
    send_to_printer(text, batch_status, print_btn)

def on_scan(event):
    sn = scan_entry.get().strip()
    scan_entry.delete(0, tk.END)
    if not sn:
        return
        
    raw_dict = dict_input.get("1.0", tk.END).strip().splitlines()
    mapping = {}
    for line in raw_dict:
        parts = re.split(r'[\t,; ]+', line.strip())
        parts = [p for p in parts if p]
        if len(parts) >= 2:
            mapping[parts[0]] = parts[1]
            
    if sn in mapping:
        label = mapping[sn]
        label = re.sub(r'[^\w\s\-,;]', '', label)
        send_to_printer(label, scan_status)
    else:
        scan_status.config(text=f"❌ SN не найден: {sn}", foreground="red")

window = tk.Tk()
window.title("Печать этикеток Brother")
window.geometry("500x480")
window.resizable(False, False)

style = ttk.Style()
style.theme_use('clam')

header = ttk.Label(window, text="🖨️ Печать этикеток", font=("Segoe UI", 16, "bold"))
header.pack(pady=(10, 5))

notebook = ttk.Notebook(window)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tab_batch = ttk.Frame(notebook)
notebook.add(tab_batch, text=" 📝 Список (Массовая) ")

desc_batch = ttk.Label(tab_batch, text="Введите инвентарные номера (можно таблицей):", justify="center")
desc_batch.pack(pady=(10, 5))

text_input = tk.Text(tab_batch, height=10, width=50, font=("Consolas", 11), wrap=tk.WORD)
text_input.pack(pady=5, padx=20)

print_btn = ttk.Button(tab_batch, text="Отправить на принтер", command=print_batch)
print_btn.pack(pady=(10, 5), ipadx=10, ipady=5)

batch_status = ttk.Label(tab_batch, text="", font=("Segoe UI", 10))
batch_status.pack(pady=5)

tab_scan = ttk.Frame(notebook)
notebook.add(tab_scan, text=" 🔍 Сканер коробок (SN -> Label) ")

desc_dict = ttk.Label(tab_scan, text="1. Вставьте 2 колонки из Excel (SN и Label):", justify="center")
desc_dict.pack(pady=(10, 2))

dict_input = tk.Text(tab_scan, height=8, width=50, font=("Consolas", 10), wrap=tk.WORD)
dict_input.pack(pady=5, padx=20)

desc_scan = ttk.Label(tab_scan, text="2. Кликните сюда и сканируйте SN с коробок:", justify="center")
desc_scan.pack(pady=(10, 2))

scan_entry = ttk.Entry(tab_scan, font=("Consolas", 14), width=35)
scan_entry.pack(pady=5)
scan_entry.bind("<Return>", on_scan)

scan_status = ttk.Label(tab_scan, text="", font=("Segoe UI", 10))
scan_status.pack(pady=5)

window.mainloop()