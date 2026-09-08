# shared.py — общие константы и утилиты для Windows и macOS версий.
# Импортируйте нужное: from shared import LANGS, parse_mapping, load_config, save_config_key

import json
import os
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Локализация
# ---------------------------------------------------------------------------

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
        "found_stat": "Найдено:",
        "t_free": " 🔤 Произвольная ",
        "d_free": "Вставьте текст или список (разделяйте переносом строки):",
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
        """,
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
        "s_pend": "❌ Pending",
        "s_found": "✅ Found",
        "s_stats": "Found:",
        "found_stat": "Found:",
        "t_free": " 🔤 Direct Print ",
        "d_free": "Text (Inventory ID, custom name, etc):",
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
        """,
    },
}

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

def load_config(config_file: str) -> dict:
    """Читает config.json и возвращает dict. При ошибке возвращает {}."""
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config_key(config_file: str, key: str, value) -> None:
    """Сохраняет одно поле в config.json, не трогая остальные."""
    try:
        data = load_config(config_file)
        data[key] = value
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Парсинг словаря SN<->Label для вкладки «Сканер»
# ---------------------------------------------------------------------------

def parse_mapping(text: str) -> dict:
    """
    Принимает многострочный текст (вставка из Excel: 2 колонки SN и Label),
    возвращает двусторонний словарь {SN: Label, Label: SN}.

    Поддерживает:
    - горизонтальный формат: «SN<tab>Label» на одной строке
    - вертикальный формат: SN на одной строке, Label на следующей
    """
    lines = text.strip().splitlines()
    mapping: dict = {}

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parts = re.split(r"[\t,; ]+", line)
        parts = [p for p in parts if p]

        if len(parts) >= 2:
            mapping[parts[0]] = parts[-1]
            mapping[parts[-1]] = parts[0]
        elif len(parts) == 1 and i + 1 < len(lines):
            next_parts = re.split(r"[\t,; ]+", lines[i + 1].strip())
            next_parts = [p for p in next_parts if p]
            if next_parts:
                mapping[parts[0]] = next_parts[-1]
                mapping[next_parts[-1]] = parts[0]

    return mapping


def lookup_sn(sn: str, mapping: dict):
    """
    Ищет SN в словаре mapping.
    Возвращает найденный label или None.

    Порядок поиска:
    1. Точное совпадение
    2. Без префикса 'S' (сканеры иногда добавляют его)
    3. Нечёткий поиск по подстроке (минимум 5 символов)
    """
    if sn in mapping:
        return mapping[sn]
    if sn.upper().startswith("S") and sn[1:] in mapping:
        return mapping[sn[1:]]
    for key in mapping:
        if len(key) >= 5 and (key.upper() in sn.upper() or sn.upper() in key.upper()):
            return mapping[key]
    return None


# ---------------------------------------------------------------------------
# Проверка версии по GitHub API (без Git)
# ---------------------------------------------------------------------------

def fetch_latest_commit_date(repo: str = "schatten08/label-printer") -> str | None:
    """
    Возвращает дату последнего коммита в main в формате ISO ('2024-06-04T...').
    При ошибке возвращает None.
    """
    import urllib.request

    try:
        url = f"https://api.github.com/repos/{repo}/commits/main"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data["commit"]["author"]["date"]
    except Exception:
        return None


def is_newer_version_available(app_version: str, repo: str = "schatten08/label-printer") -> bool | None:
    """
    Сравнивает APP_VERSION с последним коммитом.
    Возвращает True если есть обновление, False если нет, None при ошибке.
    """
    latest = fetch_latest_commit_date(repo)
    if latest is None:
        return None
    try:
        # Нормализуем обе даты к datetime для корректного сравнения
        latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        app_dt = datetime.fromisoformat(app_version.replace(" ", "T") + ":00+00:00")
        return latest_dt > app_dt
    except Exception:
        # Фолбэк: лексикографическое сравнение
        return latest[:16] > app_version[:16]
