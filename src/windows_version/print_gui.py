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
import urllib.request
import webbrowser

# Текущая версия программы (дата последнего релиза, см. CHANGELOG.md).
# Формат ISO ("YYYY-MM-DD HH:MM") важен: строка сравнивается лексикографически
# с датой коммита GitHub API в check_for_updates().
APP_VERSION = "2026-08-03 00:00"

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

# --- Глобальные переменные для прогресса сканера ---
scanned_in_scanner_tab = set()
scan_stats_var = None # Будет инициализирован после создания окна

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

def send_to_printer(text, status_widget, btn_widget=None, use_epam=True, print_barcode=True):
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
            if isinstance(text, list):
                numbers = [str(n).strip() for n in text if str(n).strip()]
            else:
                numbers = [n.strip() for n in re.split(r'[,;\s]+', str(text)) if n.strip()]
                
            if not numbers:
                return

            total_count = len(numbers)
            window.after(0, lambda: progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10)))
            window.after(0, lambda: progress_bar.configure(maximum=total_count, value=0))
            window.after(0, lambda: progress_lbl.config(text=f"0 / {total_count}"))

            doc = win32com.client.Dispatch("bpac.Document")
            
            # Предварительная проверка включен ли принтер
            try:
                printer_checker = win32com.client.Dispatch("bpac.Printer")
                if not printer_checker.IsPrinterOnline(selected_printer):
                    window.after(0, lambda: messagebox.showwarning("Принтер недоступен", f"Принтер '{selected_printer}' выключен или не подключен.\n\nПожалуйста, включите устройство и проверьте USB/Wi-Fi соединение."))
                    window.after(0, lambda: status_widget.config(text="❌ Принтер Off-line", foreground="red"))
                    window.after(0, lambda: progress_frame.pack_forget())
                    return
            except Exception as e:
                print("Skipping online check:", e)
                window.after(0, lambda: messagebox.showwarning(
                    "Проверка принтера пропущена",
                    f"Не удалось проверить статус принтера '{selected_printer}'.\n\n"
                    "Часто это значит, что установлен только b-PAC, но НЕ установлен сам "
                    "драйвер принтера Brother. Попытка печати продолжится."
                ))

            script_dir = os.path.dirname(os.path.abspath(__file__))
            if print_barcode:
                template_path = os.path.join(script_dir, "Label.lbx")
            else:
                template_path = os.path.join(script_dir, "Label_Free.lbx")
                if not os.path.exists(template_path):
                    # Если генерация не сработала, фолбэк на старый шаблон
                    template_path = os.path.join(script_dir, "Label.lbx")

            if not doc.Open(template_path):
                window.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось открыть файл шаблона:\n{template_path}"))
                window.after(0, lambda: status_widget.config(text="❌ Ошибка шаблона", foreground="red"))
                window.after(0, lambda: progress_frame.pack_forget())
                return

            # Выставляем принтер
            if not doc.SetPrinter(selected_printer, False):
                window.after(0, lambda: messagebox.showerror(
                    "Принтер не найден в Windows",
                    f"Не удалось выбрать принтер '{selected_printer}'.\n\n"
                    "Обычно это значит, что установлен только компонент b-PAC, но НЕ установлен "
                    "сам драйвер принтера Brother.\n\nСкачайте и установите 'Printer Driver' "
                    "с официального сайта Brother для вашей модели, затем добавьте принтер в Windows."
                ))
                window.after(0, lambda: status_widget.config(text="❌ Принтер не найден", foreground="red"))
                window.after(0, lambda: progress_frame.pack_forget())
                if callable(doc.Close): doc.Close()
                return
            
            # Открываем канал печати 1 раз (Пакетная печать быстрее)
            doc.StartPrint("Batch Labels", 0)

            failed = 0
            for i, num in enumerate(numbers, 1):
                lbl = doc.GetObject("Label")
                if lbl:
                    lbl.Text = num
                    
                upam_lbl = doc.GetObject("EPAm")
                if upam_lbl: upam_lbl.Text = "EPAM" if use_epam else ""
                
                upam_lbl2 = doc.GetObject("EPAM")
                if upam_lbl2: upam_lbl2.Text = "EPAM" if use_epam else ""
                
                bc = doc.GetObject("BarCode")
                if bc:
                    bc.Text = num if print_barcode else ""
                
                # Закидываем в очередь печати 1 копию и переходим к следующему
                if not doc.PrintOut(1, 0):
                    failed += 1
                
                window.after(0, lambda val=i: progress_bar.configure(value=val))
                window.after(0, lambda val=i: progress_lbl.config(text=f"{val} / {total_count}"))
                
            # Из-за особенностей библиотеки pywin32, некоторые функции без параметров могут возвращаться как переменные (свойства)
            if callable(doc.EndPrint): doc.EndPrint()
            else: _ = doc.EndPrint
            
            if callable(doc.Close): doc.Close()
            else: _ = doc.Close

            if failed:
                window.after(0, lambda: status_widget.config(text=f"⚠️ Напечатано {len(numbers) - failed} из {len(numbers)} (ошибок: {failed})", foreground="orange"))
                window.after(0, lambda: messagebox.showwarning(
                    "Часть этикеток не напечатана",
                    f"{failed} из {len(numbers)} этикеток не удалось отправить на печать.\n\n"
                    "Проверьте, что установлен драйвер принтера Brother (одного b-PAC недостаточно), "
                    "а также что принтер включен и подключен."
                ))
            else:
                window.after(0, lambda: status_widget.config(text=f"✅ Напечатано: {len(numbers)} шт.", foreground="green"))
            window.after(2000, lambda: progress_frame.pack_forget())
            
        except Exception as e:
            window.after(0, lambda err=e: messagebox.showerror("Системная ошибка", f"Ошибка COM-объекта bPAC:\n{err}"))
            window.after(0, lambda err=e: status_widget.config(text=f"❌ Ошибка", foreground="red"))
            window.after(0, lambda: progress_frame.pack_forget())
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
            # Двусторонняя связь (SN -> Label и Label -> SN)
            mapping[parts[0]] = parts[-1]
            mapping[parts[-1]] = parts[0]
        elif len(parts) == 1 and i + 1 < len(raw_dict):
            # Случай вертикальной вставки: "SN" на одной строке, "Label" на следующей
            next_line_parts = re.split(r'[\t,; ]+', raw_dict[i+1].strip())
            next_line_parts = [p for p in next_line_parts if p]
            
            if len(next_line_parts) >= 1:
                mapping[parts[0]] = next_line_parts[-1]
                mapping[next_line_parts[-1]] = parts[0]
            
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
        
        # Обновляем статистику для вкладки сканера
        scanned_in_scanner_tab.add(sn)
        update_scan_stats()
        
        send_to_printer([label], scan_status)
    else:
        # Звук ошибки (низкий и длинный "Бууп")
        threading.Thread(target=lambda: winsound.Beep(500, 400), daemon=True).start()
        scan_status.config(text=f"❌ SN не найден: {sn}", foreground="red")
        
        if messagebox.askyesno("Штрихкод не найден", f"Штрихкод '{sn}' не найден в словаре.\nРаспечатать его как Инвентарный номер?"):
            sn_to_print = re.sub(r'[^\w\s\-,;]', '', sn)
            send_to_printer([sn_to_print], scan_status)
        
    return "break"

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

# Инициализируем переменные Tkinter после создания окна
scan_stats_var = tk.StringVar(value="")

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
        "btn_upd": "🔄 Проверить обновление",
        "upd_ok": "✅ У вас последняя версия!",
        "upd_err": "❌ Ошибка при проверке",
        "upd_no_git": "❌ Git не найден! Установите его с git-scm.com",
        "upd_no_git_ask": "Git не установлен. Проверить новую версию в браузере?",
        "upd_not_repo": "❌ Программа скачана как архив. Авто-обновление невозможно.",
        "upd_not_repo_ask": "Папка не является Git-репозиторием. Хотите включить автоматические обновления?\n(Это создаст .git папку и синхронизирует код с GitHub)",
        "upd_init_ok": "✅ Теперь обновления включены! Нажмите кнопку еще раз.",
        "upd_new_zip": "🚀 Найдена новая версия! Открыть страницу загрузки?",
        "m_theme": "Тема",
        "m_dark": "Темная",
        "m_light": "Светлая",
        "m_lang": "Язык",
        "m_help": "Справка",
        "h_title": "Как пользоваться программой",
        "h_text": """
1. Список (Batch):
   - Вставьте список номеров через пробел или Enter.
   - Нажмите 'Печать'. Каждый номер будет на отдельной наклейке.

2. Сканер коробок:
   - Вставьте таблицу из Excel (2 колонки: SN и Label).
   - Сканируйте серийник с коробки. Программа сама найдет Label и напечатает.

3. Инвентаризация:
   - Загрузите базу оборудования.
   - Сканируйте всё подряд. Программа отметит найденное зеленым цветом.
   - Нажмите 'Экспорт', чтобы сохранить результат в файл.

4. Произвольная печать:
   - Напишите любой текст. Программа напечатает его по центру без штрихкода.
        """
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
        "btn_ex": "💾 Export to CSV",
        "c_stat": "Status",
        "c_lbl": "Label (Inventory ID)",
        "c_mod": "Model",
        "s_pend": "? Pending",
        "s_found": "? Found",
        "s_stats": "Found:",
        "found_stat": "Found:",
        "btn_upd": "🔄 Check for Updates",
        "upd_ok": "✅ You have the latest version!",
        "upd_err": "❌ Update check failed",
        "upd_no_git": "❌ Git not found! Please install it.",
        "upd_no_git_ask": "Git not found. Check for updates in browser?",
        "upd_not_repo": "❌ Downloaded as ZIP. Auto-update disabled.",
        "upd_not_repo_ask": "Folder is not a Git repo. Would you like to enable auto-updates?\n(This will sync your code with GitHub)",
        "upd_init_ok": "✅ Updates enabled! Click the button again.",
        "upd_new_zip": "🚀 New version found! Open download page?",
        "m_theme": "Theme",
        "m_dark": "Dark",
        "m_light": "Light",
        "m_lang": "Language",
        "m_help": "Help",
        "h_title": "How to use the program",
        "h_text": """
1. List (Batch):
   - Paste a list of numbers (space or Enter separated).
   - Click 'Print'. Each number will be a separate label.

2. Box Scanner:
   - Paste an Excel table (2 columns: SN and Label).
   - Scan the Serial Number from the box. The app finds the Label and prints it.

3. Inventory Audit:
   - Load your device database.
   - Scan items. The app marks them green when found.
   - Click 'Export' to save the result to a CSV file.

4. Direct Print:
   - Type any text. The app prints it centered without a barcode.
        """
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

def show_help():
    l = LANGS.get(current_lang, LANGS["ru"])
    help_win = tk.Toplevel(window)
    help_win.title(l.get("m_help", "Help"))
    help_win.geometry("500x450")
    help_win.transient(window)
    
    # Применяем текущую тему к фону
    bg = "#f3f3f3" if current_theme == "light" else "#252526"
    fg = "#333333" if current_theme == "light" else "#cccccc"
    help_win.configure(bg=bg)
    
    tk.Label(help_win, text=l.get("h_title", "Help"), font=("Segoe UI", 14, "bold"), bg=bg, fg=fg).pack(pady=10)
    
    txt = tk.Text(help_win, wrap="word", font=("Segoe UI", 10), bg=bg, fg=fg, bd=0, padx=20, pady=10)
    txt.insert("1.0", l.get("h_text", ""))
    txt.config(state="disabled")
    txt.pack(expand=True, fill="both")
    
    ttk.Button(help_win, text="OK", command=help_win.destroy).pack(pady=10)

def check_for_updates():
    """ Пытается сделать git pull и сообщает результат """
    try:
        l = LANGS.get(current_lang, LANGS["ru"])
        update_btn.config(state="disabled")
        
        def run_git():
            try:
                import subprocess
                import os
                import shutil
                
                # Получаем путь к директории скрипта
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # Проект находится на уровень выше папки windows_version
                project_root = os.path.abspath(os.path.join(script_dir, "../../"))

                # 1. Проверяем наличие Git
                if not shutil.which("git"):
                    if messagebox.askyesno("Update", l.get("upd_no_git_ask", "Git not found. Open browser?")):
                        # Пытаемся проверить дату последнего коммита через API (без Git)
                        try:
                            api_url = "https://api.github.com/repos/schatten08/label-printer/commits/main"
                            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=5) as response:
                                data = json.loads(response.read().decode())
                                last_commit_date = data['commit']['author']['date'] # 2024-06-04T...
                                if last_commit_date > APP_VERSION:
                                    if messagebox.askyesno("Update", l.get("upd_new_zip", "New version!")):
                                        webbrowser.open("https://github.com/schatten08/label-printer")
                                else:
                                    window.after(0, lambda: messagebox.showinfo("Update", l.get("upd_ok", "✅ Latest!")))
                        except:
                            webbrowser.open("https://github.com/schatten08/label-printer")
                    return

                # 2. Проверяем, что это git репозиторий
                if not os.path.exists(os.path.join(project_root, ".git")):
                    # Спросим пользователя, хочет ли он включить обновления
                    if messagebox.askyesno("Update", l.get("upd_not_repo_ask", "Enable updates?")):
                        subprocess.run(["git", "init"], cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
                        subprocess.run(["git", "remote", "add", "origin", "https://github.com/schatten08/label-printer.git"], cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
                        subprocess.run(["git", "fetch", "--all"], cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
                        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
                        window.after(0, lambda: messagebox.showinfo("Update", l.get("upd_init_ok", "✅ Done!")))
                    return

                # Устраняем ошибку "dubious ownership" (для сетевых папок или других юзеров)
                subprocess.run(
                    ["git", "config", "--global", "--add", "safe.directory", project_root.replace("\\", "/")],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                # Безопасное обновление: Fetch + Reset (убивает конфликты в config.json и прочих)
                subprocess.run(["git", "fetch", "--all"], cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Запоминаем текущий хэш
                old_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                
                # Сбрасываем к состоянию на сервере (это лечит любые ошибки с локальными файлами)
                subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=project_root, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Проверяем, изменился ли хэш
                new_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
                
                if old_hash == new_hash:
                    window.after(0, lambda: messagebox.showinfo("Update", l.get("upd_ok", "✅ Latest version!")))
                else:
                    window.after(0, lambda: messagebox.showinfo("Update", "✅ Обновление успешно! Перезапустите программу.\nChanges downloaded! Please restart."))
            except Exception as ex:
                window.after(0, lambda: messagebox.showerror("Update", f"Git error: {str(ex)}\nУбедитесь, что Git установлен."))
            finally:
                window.after(0, lambda: update_btn.config(state="normal"))

        threading.Thread(target=run_git, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        update_btn.config(state="normal")

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
    
    try:
        notebook.tab(3, text=l.get("t_free", " 🔤 Direct Print "))
        desc_free.config(text=l.get("d_free", "Text (Inventory ID, custom name, etc):"))
        btn_free_print.config(text=l.get("btn_f", "Print Single Label"))
    except Exception:
        pass

    # Обновляем кнопку обновления
    try:
        update_btn.config(text=l.get("btn_upd", "🔄 Check for Updates"))
    except NameError:
        pass

    # Обновляем названия меню
    try:
        menubar.entryconfig(1, label=l.get("m_theme", "Theme"))
        menubar.entryconfig(2, label=l.get("m_lang", "Language"))
        menubar.entryconfig(3, label=l.get("m_help", "Help"))
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
        free_entry.config(bg=text_bg, fg=input_fg, insertbackground=input_fg)
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

menubar.add_command(label="Справка", command=show_help)

window.config(menu=menubar)

current_theme = load_theme_pref()
apply_theme(current_theme) # Инициализация сохраненной темы

header = ttk.Label(window, text="🖨️ Печать этикеток", font=("Segoe UI", 16, "bold"))
header.pack(pady=(10, 0))

update_btn = ttk.Button(window, text="🔄 Проверить обновление", command=check_for_updates)
update_btn.pack(pady=(5, 5))

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

# Фрейм прогресса (скрыт по умолчанию)
progress_frame = ttk.Frame(window)
progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 10))
progress_lbl = ttk.Label(progress_frame, text="0 / 0", font=("Segoe UI", 9, "bold"))
progress_lbl.pack(side=tk.RIGHT, padx=(0, 20))

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
    window.after(200, update_scan_stats)

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

# Фрейм прогресса для сканера
scan_progress_frame = ttk.Frame(tab_scan)
scan_progress_bar = ttk.Progressbar(scan_progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
scan_progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
scan_progress_lbl = ttk.Label(scan_progress_frame, textvariable=scan_stats_var, font=("Segoe UI", 10, "bold"))
scan_progress_lbl.pack(side=tk.RIGHT)

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

# Состояние сортировки: {column: reverse}
inv_sort_state = {}

def sort_inventory_column(col):
    """Сортировка таблицы инвентаризации по выбранной колонке"""
    # Переключаем направление сортировки
    reverse = not inv_sort_state.get(col, False)
    inv_sort_state[col] = reverse

    # Получаем все данные из таблицы
    data_list = []
    for item_id in inv_tree.get_children():
        values = inv_tree.item(item_id)['values']
        tags = inv_tree.item(item_id)['tags']
        data_list.append((values, tags, item_id))

    # Индекс колонки для сортировки
    col_index = {"status": 0, "sn": 1, "rest": 2}[col]

    # Сортируем данные
    data_list.sort(key=lambda x: str(x[0][col_index]).lower(), reverse=reverse)

    # Удаляем все элементы из таблицы
    for item_id in inv_tree.get_children():
        inv_tree.delete(item_id)

    # Вставляем отсортированные данные обратно
    for values, tags, old_item_id in data_list:
        new_item_id = inv_tree.insert("", tk.END, values=values, tags=tags)

        # Находим соответствующий элемент в inv_data по старому item_id и обновляем
        for sn_key, data in inv_data.items():
            if data["item_id"] == old_item_id:
                data["item_id"] = new_item_id
                inv_items_map[sn_key] = new_item_id
                break

    # Обновляем заголовки с индикаторами сортировки
    for column in columns:
        text = inv_tree.heading(column)['text']
        # Убираем старые индикаторы
        text = text.replace(' ▲', '').replace(' ▼', '')
        if column == col:
            text += ' ▼' if reverse else ' ▲'
        inv_tree.heading(column, text=text)

# Привязываем сортировку к кликам на заголовки
inv_tree.heading("status", command=lambda: sort_inventory_column("status"))
inv_tree.heading("sn", command=lambda: sort_inventory_column("sn"))
inv_tree.heading("rest", command=lambda: sort_inventory_column("rest"))

# Тег для подсветки найденных строк (светло-зеленый)
inv_tree.tag_configure('found', background='#abf7b1', foreground='black')

inv_scan_frame = ttk.Frame(tab_inv)
inv_scan_frame.pack(fill=tk.X, padx=10, pady=5)

inv_scan_lbl = ttk.Label(inv_scan_frame, text="2. Сканируйте:")
inv_scan_lbl.pack(side=tk.LEFT)
inv_scan_entry = ttk.Entry(inv_scan_frame, font=("Consolas", 14), width=25)
inv_scan_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

ttk.Label(inv_scan_frame, textvariable=inv_stats_var, font=("Segoe UI", 10, "bold")).pack(side=tk.RIGHT)

def update_inv_stats():
    total = len(inv_data)
    found = sum(1 for v in inv_data.values() if "Найдено" in v["status"])
    inv_stats_var.set(f"Найдено: {found} / {total}")

# --- ФУНКЦИИ ПРОГРЕССА ДЛЯ СКАНЕРА ---
def update_scan_stats():
    raw_dict_text = dict_input.get("1.0", tk.END).strip()
    if not raw_dict_text:
        scan_progress_frame.pack_forget()
        return

    raw_dict = raw_dict_text.splitlines()
    total = 0
    for line in raw_dict:
        if line.strip():
            parts = re.split(r'[\t,; ]+', line.strip())
            if len(parts) >= 2: total += 1
            elif len(parts) == 1: total += 1 # Считаем как один элемент в словаре

    if total > 0:
        found = len(scanned_in_scanner_tab)
        scan_stats_var.set(f"Прогресс: {found} / {total}")
        scan_progress_bar.configure(maximum=total, value=found)
        scan_progress_frame.pack(fill=tk.X, padx=40, pady=5)
    else:
        scan_progress_frame.pack_forget()

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
        try:
            item_data = inv_tree.item(target_id)
            vals = item_data.get('values', [])
            sn_key = vals[1] if len(vals) > 1 else sn
            rest_key = vals[2] if len(vals) > 2 else ""
            
            # Закрашиваем строку и меняем статус
            inv_tree.item(target_id, values=("✅ Найдено", sn_key, rest_key), tags=('found',))
            
            # Обновляем память
            for k, v in inv_data.items():
                if v['item_id'] == target_id:
                    v["status"] = "✅ Найдено"
                    break
                    
            inv_tree.see(target_id)
            update_inv_stats()
            threading.Thread(target=lambda: winsound.Beep(2000, 150), daemon=True).start()
        except Exception as e:
            print("Scan error:", e)
    else:
        threading.Thread(target=lambda: winsound.Beep(500, 400), daemon=True).start()
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

free_entry = tk.Text(tab_free, height=8, width=50, font=("Consolas", 12), wrap=tk.WORD, relief=tk.FLAT, padx=10, pady=10)
free_entry.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
add_context_menu(free_entry)

free_status = ttk.Label(tab_free, text="", font=("Segoe UI", 10))
free_status.pack(pady=5)

def on_free_print(event=None):
    raw_text = free_entry.get("1.0", tk.END).strip()
    if not raw_text: return
    
    # Разбиваем по строкам или запятым/точкам с запятой
    lines = [line.strip() for line in re.split(r'[\n,;]+', raw_text) if line.strip()]
    
    clean_lines = []
    for line in lines:
        line = re.sub(r'[^\w\s\-\.,;]', '', line).strip()
        if line:
            clean_lines.append(line)
            
    if not clean_lines: return
    send_to_printer(clean_lines, free_status, btn_free_print, use_epam=False, print_barcode=False)

btn_free_print = ttk.Button(tab_free, text="Напечатать", command=on_free_print)
btn_free_print.pack(pady=(5, 10), ipadx=10, ipady=5)

apply_theme(current_theme) # Применяем вторично, чтобы обновить цвета у tk.Text после их создания
current_lang = get_lang()
update_texts(current_lang)
window.mainloop()