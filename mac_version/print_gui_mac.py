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
    pass # Will handle this inside the app to show a UI error

# ⚠️ ВНИМАНИЕ: Укажите точное имя принтера из настроек macOS (CUPS)
# Узнать имя принтера можно в терминале командой: lpstat -p
PRINTER_NAME = "Brother_QL_810W" 

def generate_label_image(text_str, output_path):
    """Генерирует картинку со штрихкодом и текстом."""
    # Используем Code128, так как он поддерживает буквы и цифры
    Code128 = barcode.get_barcode_class('code128')
    
    # Настройки отображения штрихкода
    options = {
        "write_text": True,   # Писать цифры под штрихкодом
        "font_size": 14,
        "text_distance": 4,
        "module_height": 10.0, # Высота полосок
        "quiet_zone": 3.0      # Отступы по краям
    }
    
    my_bc = Code128(text_str, writer=ImageWriter())
    # Сохраняем во временный PNG файл
    my_bc.save(output_path, options=options)

def print_labels():
    # Проверка наличия библиотек
    try:
        import barcode
        from PIL import Image
    except ImportError:
        messagebox.showerror("Ошибка библиотек", "Для работы на Mac установите библиотеки терминале:\npip3 install python-barcode Pillow")
        return

    raw_text = text_input.get("1.0", tk.END).strip()
    text = re.sub(r'[^\w\s\-,;]', '', raw_text)

    if text != raw_text:
        text_input.delete("1.0", tk.END)
        text_input.insert("1.0", text)

    if not text:
        messagebox.showwarning("Внимание", "Пожалуйста, введите номера для печати.")
        return

    print_btn.config(state=tk.DISABLED)
    status_label.config(text="⏳ Идет отправка в очередь macOS...", foreground="blue")

    def run_script():
        try:
            # Разбиваем текст на отдельные номера аналогично PS скрипту
            numbers = re.split(r'[,;\s]+', text)
            
            for num in numbers:
                clean_num = num.strip()
                if not clean_num:
                    continue
                
                # Создаем временный файл для картинки
                temp_file = os.path.join(tempfile.gettempdir(), f"label_{clean_num}")
                
                # Генерируем изображение
                generate_label_image(clean_num, temp_file)
                image_path = temp_file + ".png"
                
                # Отправляем в системную очередь печати Mac (CUPS)
                # Команда: lpr -P Имя_Принтера путь_к_картинке
                cmd = ["lpr", "-P", PRINTER_NAME, image_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"Ошибка CUPS: {result.stderr}")
                
                # Удаляем временную картинку после отправки на печать
                try:
                    os.remove(image_path)
                except:
                    pass

            window.after(0, lambda: status_label.config(text="✅ Успешно отправлено в macOS!", foreground="green"))
            
        except Exception as e:
            window.after(0, lambda err=e: status_label.config(text=f"❌ Ошибка печати: {err}", foreground="red"))
        finally:
            window.after(0, lambda: print_btn.config(state=tk.NORMAL))

    threading.Thread(target=run_script, daemon=True).start()

# --- GUI (аналогично Windows версии) ---
window = tk.Tk()
window.title("Mac Label Printer")
window.geometry("450x350")
window.resizable(False, False)

style = ttk.Style()
# В MacOS интерфейс выглядит лучше с темой default или aqua
if 'aqua' in style.theme_names():
    style.theme_use('aqua')
else:
    style.theme_use('default')

header = ttk.Label(window, text="🍏 Печать этикеток (Mac)", font=("Helvetica", 16, "bold"))
header.pack(pady=(15, 5))

desc = ttk.Label(window, text="Введите инвентарные номера через запятую, пробел\nили с новой строки:", justify="center")
desc.pack(pady=(0, 10))

text_input = tk.Text(window, height=8, width=50, font=("Menlo", 12), wrap=tk.WORD)
text_input.pack(pady=5, padx=20)

print_btn = ttk.Button(window, text="Отправить на принтер", command=print_labels)
print_btn.pack(pady=(10, 5), ipadx=10, ipady=5)

status_label = ttk.Label(window, text="", font=("Helvetica", 10))
status_label.pack(pady=5)

window.mainloop()