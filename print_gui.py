import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os

def print_labels():
    # Получаем введенные данные
    text = text_input.get("1.0", tk.END).strip()

    if not text:
        messagebox.showwarning("Внимание", "Пожалуйста, введите номера для печати.")
        return

    # Блокируем кнопку и меняем статус
    print_btn.config(state=tk.DISABLED)
    status_label.config(text="⏳ Идет отправка на принтер...", foreground="blue")

    def run_script():
        try:
            # Ищем скрипт print.ps1 в той же папке, где лежит эта программа
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ps_script = os.path.join(script_dir, "print.ps1")

            # Запускаем скрытый процесс PowerShell
            cmd = [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", ps_script,
                "-Text1", text
            ]

            # Ждем окончания
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="cp866")

            if result.returncode == 0:
                # Возвращаемся в главный поток для обновления интерфейса
                window.after(0, lambda: status_label.config(text="✅ Успешно напечатано!", foreground="green"))
                window.after(0, lambda: text_input.delete("1.0", tk.END)) # Очищаем поле для новой партии
            else:
                window.after(0, lambda: status_label.config(text="❌ Ошибка при печати", foreground="red"))
                print(result.stderr)

        except Exception as e:
            window.after(0, lambda err=e: status_label.config(text=f"❌ Системная ошибка: {err}", foreground="red"))
        finally:
            window.after(0, lambda: print_btn.config(state=tk.NORMAL))

    # Запускаем в отдельном потоке, чтобы окно не "зависало"
    threading.Thread(target=run_script, daemon=True).start()

# Настройка главного окна
window = tk.Tk()
window.title("Печать этикеток Brother")
window.geometry("450x350")
window.resizable(False, False)

# Стилизация (используем встроенные красивые темы)
style = ttk.Style()
style.theme_use('clam')

# Заголовок
header = ttk.Label(window, text="🖨️ Печать этикеток", font=("Segoe UI", 16, "bold"))
header.pack(pady=(15, 5))

desc = ttk.Label(window, text="Введите инвентарные номера через запятую, пробел\nили с новой строки (можно вставить скопированный список):", justify="center")
desc.pack(pady=(0, 10))

# Поле для ввода (многострочное, удобно для вставки из Excel)
text_input = tk.Text(window, height=8, width=50, font=("Consolas", 11), wrap=tk.WORD)
text_input.pack(pady=5, padx=20)
text_input.focus_set() # <--- Автоматически ставим курсор при запуске программы

# Кнопка печати
print_btn = ttk.Button(window, text="Отправить на принтер", command=print_labels)
print_btn.pack(pady=(10, 5), ipadx=10, ipady=5)

# Метка статуса
status_label = ttk.Label(window, text="", font=("Segoe UI", 10))
status_label.pack(pady=5)

# Запуск программы
window.mainloop()
